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
        "brd_agent.agents.nodes.context_assembly.ContentAssemblyService.assemble_for_brd_generation",
        fake_assemble,
    )

    state = await run_context_assembly(
        user_id="u1",
        conversation_id="c1",
        requirement_text="Generate BRD",
    )
    assert state["context_assembly_status"] == "assembled"
    assert state["assembled_context"]["requirement_text"] == "Generate BRD"
