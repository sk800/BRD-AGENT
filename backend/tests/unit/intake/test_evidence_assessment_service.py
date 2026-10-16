import json

import pytest

from brd_agent.intake.services.evidence_assessment_service import (
    EvidenceAssessmentService,
)


class FakeJsonClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def complete_json(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


@pytest.mark.asyncio
async def test_evidence_assessment_returns_each_key_once():
    service = EvidenceAssessmentService(
        FakeJsonClient(
            {
                "items": [
                    {
                        "key": "audience",
                        "status": "answered",
                        "evidence_summary": "The document identifies cafe customers.",
                        "clarification_question": None,
                    },
                    {
                        "key": "scope",
                        "status": "missing",
                        "evidence_summary": "",
                        "clarification_question": "Which features are needed at launch?",
                    },
                ]
            }
        )
    )

    result = await service.assess(
        checklist=[
            {"key": "audience", "label": "Who uses it?"},
            {"key": "scope", "label": "What is in the first release?"},
        ],
        conversation=[{"role": "user", "text": "Build a cafe website."}],
        evidence=[],
    )

    assert [item["status"] for item in result] == ["answered", "missing"]
    assert result[1]["clarification_question"].startswith("Which features")


@pytest.mark.asyncio
async def test_evidence_assessment_rejects_incomplete_key_set():
    service = EvidenceAssessmentService(
        FakeJsonClient(
            {
                "items": [
                    {
                        "key": "audience",
                        "status": "answered",
                        "evidence_summary": "Customers.",
                    }
                ]
            }
        )
    )

    with pytest.raises(ValueError, match="each checklist key once"):
        await service.assess(
            checklist=[
                {"key": "audience", "label": "Who?"},
                {"key": "scope", "label": "What?"},
            ],
            conversation=[],
            evidence=[],
        )


@pytest.mark.asyncio
async def test_evidence_assessment_includes_all_retrieved_document_chunks():
    client = FakeJsonClient(
        {
            "items": [
                {
                    "key": "scope",
                    "status": "answered",
                    "evidence_summary": "The launch scope is documented.",
                    "clarification_question": None,
                }
            ]
        }
    )
    service = EvidenceAssessmentService(client)

    await service.assess(
        checklist=[{"key": "scope", "label": "What is in the first release?"}],
        conversation=[],
        evidence=[
            {
                "key": "scope",
                "requirement_text": "What is in the first release?",
                "uploaded_document_chunks": [
                    {"chunk_id": f"chunk-{index}", "text": f"Evidence {index}"}
                    for index in range(10)
                ],
            }
        ],
    )

    payload = json.loads(client.calls[0]["user_prompt"])
    chunks = payload["evidence"][0]["uploaded_document_chunks"]
    assert len(chunks) == 10
    assert chunks[-1]["text"] == "Evidence 9"
