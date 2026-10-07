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
    ctx = await service.assemble_for_requirement(
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
        await service.assemble_for_requirement(
            user_id="u1",
            conversation_id="c1",
            requirement_text="   ",
        )


@pytest.mark.asyncio
async def test_assemble_rejects_invalid_retrieval_limit():
    service = ContentAssemblyService()

    with pytest.raises(ValueError, match="retrieval_top_k"):
        await service.assemble_for_requirement(
            user_id="u1",
            conversation_id="c1",
            requirement_text="Build a cafe website",
            retrieval_top_k=0,
        )


@pytest.mark.asyncio
async def test_checklist_assembly_retrieves_and_assesses_each_item(monkeypatch):
    queries = []

    async def fake_search(self, **kwargs):
        queries.append(kwargs["query"])
        return [{"text": f"Evidence for {kwargs['query']}"}]

    class FakeEnterprise:
        async def search_for_requirement(self, requirement_text):
            return [{"platform": "confluence", "result": {"ok": True}}]

        async def fetch_from_platform(self, platform, action, params):
            return {"ok": True}

    class FakeAssessor:
        async def assess(self, *, checklist, conversation, evidence):
            assert len(evidence) == len(checklist) == 2
            return [
                {
                    "key": "users",
                    "status": "answered",
                    "evidence_summary": "The notes identify customers.",
                    "clarification_question": None,
                },
                {
                    "key": "scope",
                    "status": "needs_clarification",
                    "evidence_summary": "The first release is not defined.",
                    "clarification_question": "Which features belong in the first release?",
                },
            ]

    monkeypatch.setattr(
        "brd_agent.orchestration.context_assembly_service.VectorRetrievalService.search_uploaded_documents",
        fake_search,
    )
    service = ContentAssemblyService(
        enterprise=FakeEnterprise(),
        assessor=FakeAssessor(),
    )
    result = await service.assemble_for_checklist(
        user_id="u1",
        conversation_id="c1",
        checklist=[
            {"key": "users", "label": "Who are the users?", "status": "missing"},
            {"key": "scope", "label": "What is in scope?", "status": "missing"},
        ],
        conversation=[{"role": "user", "text": "Build a cafe site."}],
    )

    assert queries == ["Who are the users?", "What is in scope?"]
    assert [item["status"] for item in result["items"]] == [
        "answered",
        "needs_clarification",
    ]
    assert result["status"] == "needs_user_input"
    assert result["items"][1]["clarification_question"].startswith("Which features")
