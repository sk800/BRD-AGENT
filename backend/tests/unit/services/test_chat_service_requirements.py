from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from brd_agent.domain.models.chat import AttachmentInDB, ConversationInDB, MessageInDB
from brd_agent.services.chat_service import ChatService
from datetime import UTC, datetime


def _conversation() -> ConversationInDB:
    now = datetime.now(UTC)
    return ConversationInDB.model_validate(
        {
            "_id": "conv-1",
            "user_id": "user-1",
            "title": "Test",
            "created_at": now,
            "updated_at": now,
            "workflow_state": {},
        }
    )


def _message(chunks: list[dict] | None = None) -> MessageInDB:
    now = datetime.now(UTC)
    return MessageInDB.model_validate(
        {
            "_id": "msg-1",
            "conversation_id": "conv-1",
            "user_id": "user-1",
            "role": "user",
            "text": "Build support portal BRD",
            "attachments": [],
            "created_at": now,
            "chunks": chunks or [],
        }
    )


@pytest.mark.asyncio
async def test_send_message_runs_ingestion_then_requirements(monkeypatch):
    service = ChatService(MagicMock())
    conversation = _conversation()
    message = _message(chunks=[{"text": "Meeting notes about SLA"}])

    service._conversations.get_by_id = AsyncMock(return_value=conversation)
    service._conversations.create = AsyncMock(return_value=conversation)
    service._conversations.touch = AsyncMock()
    service._messages.create = AsyncMock(return_value=message)
    ingested_message = _message(chunks=[{"text": "chunk"}])
    service._messages.update_ingestion_results = AsyncMock(return_value=ingested_message)
    service._messages.list_by_conversation = AsyncMock(return_value=[message])
    service._conversations.update_workflow_state = AsyncMock()
    service._file_storage.save_files = AsyncMock(
        return_value=[
            AttachmentInDB(
                id="att-1",
                filename="f.txt",
                original_filename="f.txt",
                mime_type="text/plain",
                size_bytes=10,
                storage_path="/tmp/f.txt",
                content_sha256="abc",
            )
        ]
    )

    monkeypatch.setattr(
        "brd_agent.services.chat_service.run_ingestion",
        AsyncMock(return_value={"chunks": [{"text": "chunk"}], "extraction_status": "done"}),
    )
    run_requirements = AsyncMock(
        return_value={
            "requirement_checklist": [{"key": "scope", "label": "Scope"}],
            "brd_requirement_points": {"scope": {"label": "Scope"}},
            "requirement_checklist_status": "ready",
            "conversation_route": "project",
        }
    )
    monkeypatch.setattr(
        "brd_agent.services.chat_service.run_requirements",
        run_requirements,
    )
    monkeypatch.setattr(
        "brd_agent.services.chat_service.log_extraction_results",
        lambda **kwargs: None,
    )

    conv, msg, req_state = await service.send_message(
        user_id="user-1",
        text="Build support portal BRD",
        files=[SimpleNamespace(filename="notes.txt", file=MagicMock())],
        conversation_id="conv-1",
    )

    assert conv.id == "conv-1"
    assert req_state["requirement_checklist_status"] == "ready"
    run_requirements.assert_awaited_once()
    assert run_requirements.await_args.kwargs["request"] == "Build support portal BRD"
    assert run_requirements.await_args.kwargs["chunks"] == [{"text": "chunk"}]
