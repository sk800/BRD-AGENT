import pytest

from brd_agent.orchestration.context_assembly_service import (
    ContentAssemblyService,
    EnterpriseSourceRequest,
)


@pytest.mark.asyncio
async def test_assemble_combines_vector_hits_and_enterprise_mcp(monkeypatch):
    async def fake_search(self, **kwargs):
        return [
            {
                "source": "uploaded_documents",
                "chunk_id": "c1",
                "text": "Uploaded requirement notes",
            }
        ]

    class FakeEnterprise:
        async def fetch_from_platform(self, platform, action, params):
            return {
                "ok": True,
                "data": {"title": "Confluence spec"},
            }

    monkeypatch.setattr(
        "brd_agent.orchestration.context_assembly_service.VectorRetrievalService.search_uploaded_documents",
        fake_search,
    )

    service = ContentAssemblyService(enterprise=FakeEnterprise())
    ctx = await service.assemble_for_brd_generation(
        user_id="u1",
        conversation_id="conv1",
        requirement_text="Build login BRD",
        enterprise_sources=[
            EnterpriseSourceRequest(
                platform="confluence",
                action="read_page",
                params={"page_id": "99"},
            )
        ],
    )

    assert ctx.uploaded_document_chunks[0]["text"] == "Uploaded requirement notes"
    assert ctx.enterprise_knowledge[0]["platform"] == "confluence"
    assert ctx.enterprise_knowledge[0]["result"]["data"]["title"] == "Confluence spec"
    assert ctx.status == "assembled"


@pytest.mark.asyncio
async def test_assemble_requires_requirement_text():
    service = ContentAssemblyService()
    with pytest.raises(ValueError, match="requirement_text"):
        await service.assemble_for_brd_generation(
            user_id="u1",
            conversation_id="c1",
            requirement_text="   ",
        )
