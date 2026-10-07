from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from brd_agent.api.routes import chat


class FakeChatService:
    def __init__(self):
        self.workflow_state = {}
        self.saved_state = None

    async def send_message(self, **kwargs):
        return (
            SimpleNamespace(id="conversation-1"),
            SimpleNamespace(id="message-1", chunks=[]),
        )

    async def list_messages(self, user_id, conversation_id):
        return []

    async def get_workflow_state(self, user_id, conversation_id):
        return self.workflow_state

    async def save_workflow_state(self, user_id, conversation_id, workflow_state):
        self.saved_state = workflow_state


@pytest.mark.asyncio
async def test_requirements_endpoint_returns_and_persists_assessed_checklist(monkeypatch):
    async def fake_run_requirements(**kwargs):
        assert kwargs["user_id"] == "user-1"
        assert kwargs["conversation_id"] == "conversation-1"
        return {
            "requirement_checklist": [
                {
                    "key": "target_users",
                    "label": "Who will use it?",
                    "status": "missing",
                    "clarification_question": "Who is the primary audience?",
                }
            ],
            "requirement_checklist_status": "ready",
            "assembled_checklist_context": [{"key": "target_users"}],
            "context_assembly_status": "needs_user_input",
            "conversation_route": "project",
            "assistant_message": "Who is the primary audience?",
        }

    monkeypatch.setattr(chat, "run_requirements", fake_run_requirements)
    service = FakeChatService()
    response = await chat.discover_requirements(
        current_user=SimpleNamespace(id="user-1"),
        chat_service=service,
        text="Build a cafe website",
    )

    assert response.requirement_checklist[0]["status"] == "missing"
    assert response.assistant_message == "Who is the primary audience?"
    assert response.context_assembly_status == "needs_user_input"
    assert service.saved_state["requirement_checklist"][0]["key"] == "target_users"


@pytest.mark.asyncio
async def test_requirements_endpoint_rejects_write_mcp_actions():
    with pytest.raises(HTTPException) as error:
        await chat.discover_requirements(
            current_user=SimpleNamespace(id="user-1"),
            chat_service=FakeChatService(),
            text="Build a cafe website",
            enterprise_sources_json=(
                '[{"platform":"confluence","action":"create_page","params":{}}]'
            ),
        )

    assert error.value.status_code == 400
