import pytest

from brd_agent.agents.graph.requirements_graph import run_requirements
from brd_agent.agents.nodes.requirements import requirements_node


class FakeDiscoveryService:
    def __init__(self):
        self.discovery_input = None

    async def discover_result(self, discovery_input):
        self.discovery_input = discovery_input
        return {
            "route": "project",
            "redirect_message": None,
            "items": [
                {
                    "key": "visitor_actions",
                    "label": "What visitors should do",
                    "rationale": "This defines the website's essential journey.",
                    "status": "missing",
                }
            ],
        }


@pytest.mark.asyncio
async def test_node_combines_request_history_and_uploaded_document_chunks():
    service = FakeDiscoveryService()
    result = await requirements_node(
        {
            "current_user_text": "I want to make a website for my cafe",
            "conversation_history": [
                {"role": "user", "text": "The cafe serves breakfast and lunch."},
            ],
            "chunks": [{"text": "Customers often ask about the menu by phone."}],
        },
        discovery_service=service,
    )

    assert "Current user request:\nI want to make a website for my cafe" in service.discovery_input
    assert "The cafe serves breakfast and lunch." in service.discovery_input
    assert "Customers often ask about the menu by phone." in service.discovery_input
    assert result["requirement_checklist_status"] == "ready"
    assert result["requirement_checklist"][0]["key"] == "visitor_actions"
    assert result["conversation_route"] == "project"


@pytest.mark.asyncio
async def test_node_skips_when_request_and_documents_are_missing():
    result = await requirements_node({})

    assert result["requirement_checklist"] == []
    assert result["requirement_checklist_status"] == "skipped"


@pytest.mark.asyncio
async def test_node_discovers_from_documents_without_free_text():
    service = FakeDiscoveryService()

    await requirements_node(
        {"chunks": [{"text": "The first release should let customers book a table."}]},
        discovery_service=service,
    )

    assert "Infer the project requirements from these files." in service.discovery_input
    assert "book a table" in service.discovery_input


@pytest.mark.asyncio
async def test_node_preserves_prior_checklist_and_redirects_off_topic():
    class RedirectDiscoveryService:
        async def discover_result(self, discovery_input):
            return {
                "route": "redirect",
                "redirect_message": "Happy to help later; which users should the project serve?",
                "items": [],
            }

    prior = [{"key": "target_users", "label": "Who will use it?", "status": "missing"}]
    result = await requirements_node(
        {
            "current_user_text": "Tell me a joke",
            "prior_checklist": prior,
        },
        discovery_service=RedirectDiscoveryService(),
    )

    assert result["conversation_route"] == "redirect"
    assert result["requirement_checklist"] == prior
    assert "which users" in result["assistant_message"]


@pytest.mark.asyncio
async def test_requirements_graph_accepts_text_documents_and_history(monkeypatch):
    captured = {}

    async def fake_discover_result(self, discovery_input):
        captured["input"] = discovery_input
        return {
            "route": "project",
            "redirect_message": None,
            "items": [
                {
                    "key": "table_booking",
                    "label": "How guests book tables",
                    "rationale": "The booking flow defines a core visitor action.",
                    "status": "missing",
                }
            ],
        }

    monkeypatch.setattr(
        "brd_agent.agents.nodes.requirements.RequirementDiscoveryService.discover_result",
        fake_discover_result,
    )

    async def fake_assemble(self, **kwargs):
        return {"items": [], "status": "empty"}

    monkeypatch.setattr(
        "brd_agent.agents.nodes.context_assembly.ContentAssemblyService.assemble_for_checklist",
        fake_assemble,
    )
    result = await run_requirements(
        request="Build a cafe website",
        chunks=[{"text": "Guests currently call to book tables."}],
        conversation_history=[{"role": "user", "text": "The cafe serves dinner."}],
    )

    assert "Build a cafe website" in captured["input"]
    assert "Guests currently call to book tables." in captured["input"]
    assert "The cafe serves dinner." in captured["input"]
    assert result["requirement_checklist_status"] == "ready"
