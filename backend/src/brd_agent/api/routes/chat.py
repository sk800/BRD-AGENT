from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from brd_agent.api.dependencies.auth import get_current_user
from brd_agent.api.dependencies.chat import get_chat_service
from brd_agent.api.schemas.chat import (
    AttachmentResponse,
    ConversationListResponse,
    ConversationResponse,
    ExtractedDocumentResponse,
    ExtractionErrorResponse,
    MessageListResponse,
    MessageResponse,
    SendMessageResponse,
)
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
