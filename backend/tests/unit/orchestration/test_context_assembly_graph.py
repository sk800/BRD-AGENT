import pytest

from brd_agent.agents.graph.context_assembly_graph import run_context_assembly


@pytest.mark.asyncio
async def test_run_context_assembly_graph(monkeypatch):
    async def fake_assemble(self, **kwargs):
        from brd_agent.orchestration.context_assembly_service import AssembledContext

        return AssembledContext(
            requirement_text=kwargs["requirement_text"],
            uploaded_document_chunks=[],
            enterprise_knowledge=[],
        )

    monkeypatch.setattr(
        "brd_agent.agents.nodes.context_assembly.ContentAssemblyService.assemble_for_requirement",
        fake_assemble,
    )

    state = await run_context_assembly(
        user_id="u1",
        conversation_id="c1",
        requirement_text="Generate BRD",
    )
    assert state["context_assembly_status"] == "assembled"
    assert state["assembled_context"]["requirement_text"] == "Generate BRD"


@pytest.mark.asyncio
async def test_context_assembly_graph_rejects_enterprise_source_without_action():
    with pytest.raises(ValueError, match="platform and action"):
        await run_context_assembly(
            user_id="u1",
            conversation_id="c1",
            requirement_text="Find the relevant cafe menu",
            enterprise_sources=[{"platform": "confluence"}],
        )
