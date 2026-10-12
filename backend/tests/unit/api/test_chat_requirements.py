from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from brd_agent.api.routes import chat


class FakeChatService:
    def __init__(self):
        self.workflow_state = {}
        self.saved_state = None
        self.last_send_kwargs = None

    async def send_message(self, **kwargs):
        self.last_send_kwargs = kwargs
        state = {
            "requirement_checklist": [
                {
                    "key": "target_users",
                    "label": "Who will use it?",
                    "status": "missing",
                    "clarification_question": "Who is the primary audience?",
                }
            ],
            "brd_requirement_points": {
                "target_users": {
                    "label": "Who will use it?",
                    "status": "missing",
                }
            },
            "requirement_checklist_status": "ready",
            "assembled_checklist_context": [{"key": "target_users"}],
            "context_assembly_status": "needs_user_input",
            "conversation_route": "project",
            "assistant_message": "Who is the primary audience?",
        }
        return (
            SimpleNamespace(id="conversation-1"),
            SimpleNamespace(id="message-1", chunks=[]),
            state,
        )


@pytest.mark.asyncio
async def test_requirements_endpoint_returns_checklist_from_unified_send_message():
    service = FakeChatService()
    response = await chat.discover_requirements(
        current_user=SimpleNamespace(id="user-1"),
        chat_service=service,
        text="Build a cafe website",
    )

    assert response.requirement_checklist[0]["status"] == "missing"
    assert response.assistant_message == "Who is the primary audience?"
    assert response.context_assembly_status == "needs_user_input"
    assert service.last_send_kwargs["text"] == "Build a cafe website"


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
