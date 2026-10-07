import pytest

from brd_agent.intake.services.evidence_assessment_service import (
    EvidenceAssessmentService,
)


class FakeJsonClient:
    def __init__(self, response):
        self.response = response

    async def complete_json(self, **kwargs):
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
