from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from brd_agent.api.dependencies.auth import get_current_user
from brd_agent.api.dependencies.chat import get_chat_service
from brd_agent.api.schemas.brd import AssembleBrdContextRequest, AssembledContextResponse
from brd_agent.core.exceptions import ChatError
from brd_agent.domain.models.user import UserPublic
from brd_agent.agents.graph.context_assembly_graph import run_context_assembly
from brd_agent.services.chat_service import ChatService

router = APIRouter(prefix="/brd", tags=["brd"])


@router.post(
    "/assemble-context",
    response_model=AssembledContextResponse,
    status_code=status.HTTP_200_OK,
)
async def assemble_brd_context(
    body: AssembleBrdContextRequest,
    current_user: Annotated[UserPublic, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> AssembledContextResponse:
    """Gather context for BRD generation: vector DB (uploads) + live enterprise MCP."""

    try:
        await chat_service.list_messages(current_user.id, body.conversation_id)
    except ChatError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    try:
        state = await run_context_assembly(
            user_id=current_user.id,
            conversation_id=body.conversation_id,
            requirement_text=body.requirement_text,
            enterprise_sources=[
                item.model_dump() for item in body.enterprise_sources
            ],
            retrieval_top_k=body.retrieval_top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    assembled = state.get("assembled_context") or {}
    return AssembledContextResponse(
        requirement_text=assembled.get("requirement_text", body.requirement_text),
        uploaded_document_chunks=assembled.get("uploaded_document_chunks", []),
        enterprise_knowledge=assembled.get("enterprise_knowledge", []),
        status=assembled.get("status", "assembled"),
        context_assembly_status=state.get("context_assembly_status"),
    )
