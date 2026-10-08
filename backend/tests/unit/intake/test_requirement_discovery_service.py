import pytest

from brd_agent.intake.services.requirement_discovery_service import (
    RequirementDiscoveryService,
)


class FakeJsonClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def complete_json(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


@pytest.mark.asyncio
async def test_discovery_builds_a_concise_valid_checklist():
    client = FakeJsonClient(
        {
            "items": [
                {
                    "key": "visitor_actions",
                    "label": "What visitors should do",
                    "rationale": "This defines the website's essential journey.",
                    "status": "ready",
                },
                {
                    "key": "visitor_actions",
                    "label": "What visitors should do",
                    "rationale": "Duplicate item.",
                    "status": "missing",
                },
            ]
        }
    )

    result = await RequirementDiscoveryService(client).discover(
        "Current user request: Build a website for my cafe"
    )

    assert result == [
        {
            "key": "visitor_actions",
            "label": "What visitors should do",
            "rationale": "This defines the website's essential journey.",
            "status": "missing",
        }
    ]
    assert "Current user request" in client.calls[0]["user_prompt"]
    system_prompt = client.calls[0]["system_prompt"].casefold()
    assert "common brd essentials" in system_prompt
    assert "objective/problem" in system_prompt
    assert "do not ask about" in system_prompt
    assert "answer it clearly" in system_prompt
    assert "do not pad the checklist" in system_prompt
    assert "fixed number or range" in system_prompt
    assert "never more than 8" not in system_prompt
    assert "do not split one workflow" in system_prompt
    assert "short, manageable" in system_prompt
    assert "time slots, party size" in system_prompt


@pytest.mark.asyncio
async def test_discovery_allows_empty_checklist_when_no_gaps_remain():
    service = RequirementDiscoveryService(FakeJsonClient({"items": []}))

    assert await service.discover("Build a cafe website") == []


@pytest.mark.asyncio
async def test_discovery_rejects_blank_checklist_fields():
    service = RequirementDiscoveryService(
        FakeJsonClient(
            {
                "items": [
                    {
                        "key": "target_users",
                        "label": " ",
                        "rationale": "Clarifies the primary audience.",
                    }
                ]
            }
        )
    )

    with pytest.raises(ValueError, match="invalid requirements checklist"):
        await service.discover("Build a cafe website")


@pytest.mark.asyncio
async def test_discovery_requires_nonempty_input():
    service = RequirementDiscoveryService(FakeJsonClient({"items": []}))

    with pytest.raises(ValueError, match="cannot be empty"):
        await service.discover(" ")
