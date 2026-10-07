import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import TypeAdapter, ValidationError

from brd_agent.api.dependencies.auth import get_current_user
from brd_agent.api.dependencies.chat import get_chat_service
from brd_agent.api.schemas.chat import (
    AttachmentResponse,
    ConversationListResponse,
    ConversationResponse,
    ExtractedDocumentResponse,
    ChunkResponse,
    ExtractionErrorResponse,
    MessageListResponse,
    MessageResponse,
    RequirementDiscoveryResponse,
    SendMessageResponse,
)
from brd_agent.api.schemas.brd import EnterpriseSourceSpec
from brd_agent.agents.graph.requirements_graph import run_requirements
from brd_agent.core.exceptions import ChatError
from brd_agent.domain.models.chat import ConversationInDB, MessageInDB
from brd_agent.domain.models.user import UserPublic
from brd_agent.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


def _to_conversation_response(conversation: ConversationInDB) -> ConversationResponse:
    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def _to_message_response(message: MessageInDB) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        conversation_id=message.conversation_id,
        role=message.role,
        text=message.text,
        attachments=[
            AttachmentResponse(
                id=attachment.id,
                filename=attachment.filename,
                original_filename=attachment.original_filename,
                mime_type=attachment.mime_type,
                size_bytes=attachment.size_bytes,
            )
            for attachment in message.attachments
        ],
        extraction_status=message.extraction_status,
        extracted_documents=[
            ExtractedDocumentResponse(
                attachment_id=item.attachment_id,
                original_filename=item.original_filename,
                extraction=item.extraction,
            )
            for item in message.extracted_documents
        ],
        extraction_errors=[
            ExtractionErrorResponse(
                attachment_id=item.attachment_id,
                original_filename=item.original_filename,
                error=item.error,
            )
            for item in message.extraction_errors
        ],
        chunking_method=message.chunking_method,
        chunking_status=message.chunking_status,
        chunks=[
            ChunkResponse(
                chunk_id=chunk.get("chunk_id", ""),
                chunk_type=chunk.get("chunk_type", "unknown"),
                text=chunk.get("text", ""),
                metadata=chunk.get("metadata", {}),
                parent_id=chunk.get("parent_id"),
            )
            for chunk in message.chunks
        ],
        created_at=message.created_at,
    )


@router.post("/messages", response_model=SendMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    current_user: Annotated[UserPublic, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
    text: Annotated[str | None, Form()] = None,
    conversation_id: Annotated[str | None, Form()] = None,
    files: Annotated[list[UploadFile] | None, File()] = None,
) -> SendMessageResponse:
    try:
        conversation, message = await chat_service.send_message(
            user_id=current_user.id,
            text=text,
            files=files or [],
            conversation_id=conversation_id,
        )
    except ChatError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return SendMessageResponse(
        conversation=_to_conversation_response(conversation),
        message=_to_message_response(message),
    )


@router.post(
    "/requirements",
    response_model=RequirementDiscoveryResponse,
    status_code=status.HTTP_200_OK,
)
async def discover_requirements(
    current_user: Annotated[UserPublic, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
    text: Annotated[str | None, Form()] = None,
    conversation_id: Annotated[str | None, Form()] = None,
    files: Annotated[list[UploadFile] | None, File()] = None,
    enterprise_sources_json: Annotated[str | None, Form()] = None,
    retrieval_top_k: Annotated[int | None, Form()] = None,
) -> RequirementDiscoveryResponse:
    """Discover BRD gaps, retrieve evidence for each, and return any user questions."""
    enterprise_sources: list[EnterpriseSourceSpec] = []
    if enterprise_sources_json:
        try:
            enterprise_sources = TypeAdapter(
                list[EnterpriseSourceSpec]
            ).validate_python(json.loads(enterprise_sources_json))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="enterprise_sources_json must be a JSON list of valid source specifications",
            ) from exc
        read_only_actions = {
            ("confluence", "read_page"),
            ("confluence", "search"),
            ("servicenow", "get_record"),
            ("servicenow", "query_records"),
        }
        invalid = [
            item
            for item in enterprise_sources
            if (item.platform.lower(), item.action.lower()) not in read_only_actions
        ]
        if invalid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Checklist context assembly accepts read-only MCP actions only",
            )

    try:
        conversation, message = await chat_service.send_message(
            user_id=current_user.id,
            text=text,
            files=files or [],
            conversation_id=conversation_id,
        )
        messages = await chat_service.list_messages(current_user.id, conversation.id)
        workflow_state = await chat_service.get_workflow_state(
            current_user.id, conversation.id
        )
    except ChatError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    state = await run_requirements(
        request=text,
        chunks=[chunk for chunk in message.chunks],
        user_id=current_user.id,
        conversation_id=conversation.id,
        prior_checklist=workflow_state.get("requirement_checklist", []),
        enterprise_sources=[item.model_dump() for item in enterprise_sources],
        retrieval_top_k=retrieval_top_k,
        conversation_history=[
            {"role": item.role, "text": item.text or ""}
            for item in messages
            if item.id != message.id and item.text
        ]
        + (
            [
                {
                    "role": "assistant",
                    "text": workflow_state["assistant_message"],
                }
            ]
            if workflow_state.get("assistant_message")
            else []
        ),
    )

    if state.get("conversation_route") != "redirect":
        await chat_service.save_workflow_state(
            current_user.id,
            conversation.id,
            {
                "requirement_checklist": state.get("requirement_checklist", []),
                "requirement_checklist_status": state.get(
                    "requirement_checklist_status", "failed"
                ),
                "assembled_checklist_context": state.get(
                    "assembled_checklist_context", []
                ),
                "context_assembly_status": state.get("context_assembly_status"),
                "assistant_message": state.get("assistant_message"),
            },
        )

    previous_context = workflow_state.get("assembled_checklist_context", [])
    return RequirementDiscoveryResponse(
        conversation_id=conversation.id,
        message_id=message.id,
        requirement_checklist=state.get("requirement_checklist", []),
        requirement_checklist_status=state.get(
            "requirement_checklist_status",
            "failed",
        ),
        assembled_checklist_context=state.get(
            "assembled_checklist_context", previous_context
        ),
        context_assembly_status=state.get(
            "context_assembly_status",
            workflow_state.get("context_assembly_status"),
        ),
        conversation_route=state.get("conversation_route", "project"),
        assistant_message=state.get("assistant_message"),
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    current_user: Annotated[UserPublic, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> ConversationListResponse:
    conversations = await chat_service.list_conversations(current_user.id)
    return ConversationListResponse(
        conversations=[_to_conversation_response(item) for item in conversations],
    )


@router.get("/conversations/{conversation_id}/messages", response_model=MessageListResponse)
async def list_messages(
    conversation_id: str,
    current_user: Annotated[UserPublic, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> MessageListResponse:
    try:
        messages = await chat_service.list_messages(current_user.id, conversation_id)
    except ChatError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return MessageListResponse(
        conversation_id=conversation_id,
        messages=[_to_message_response(item) for item in messages],
    )
