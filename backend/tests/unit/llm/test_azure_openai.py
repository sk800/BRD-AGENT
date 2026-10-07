import json

import httpx
import pytest

from brd_agent.llm.gateway.azure_openai import AzureOpenAIClient


@pytest.mark.asyncio
async def test_azure_client_sends_json_mode_request(monkeypatch):
    from brd_agent.core.config.settings import Settings

    settings = Settings(
        azure_openai_endpoint="https://example.openai.azure.com",
        azure_openai_api_key="test-key",
        azure_openai_deployment="requirements",
        azure_openai_api_version="2024-10-21",
    )
    monkeypatch.setattr(
        "brd_agent.llm.gateway.azure_openai.get_settings",
        lambda: settings,
    )
    captured = {}

    async def handler(request):
        captured["url"] = str(request.url)
        captured["api_key"] = request.headers["api-key"]
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": '{"items": []}'}}
                ]
            },
        )

    client = AzureOpenAIClient(transport=httpx.MockTransport(handler))
    result = await client.complete_json(
        system_prompt="system",
        user_prompt="user",
    )

    assert result == {"items": []}
    assert "deployments/requirements/chat/completions" in captured["url"]
    assert "api-version=2024-10-21" in captured["url"]
    assert captured["api_key"] == "test-key"
    assert captured["payload"]["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_azure_client_rejects_missing_configuration(monkeypatch):
    from brd_agent.core.config.settings import Settings

    monkeypatch.setattr(
        "brd_agent.llm.gateway.azure_openai.get_settings",
        lambda: Settings(
            azure_openai_endpoint="",
            azure_openai_api_key="",
            azure_openai_deployment="",
        ),
    )
    client = AzureOpenAIClient()

    with pytest.raises(RuntimeError, match="Azure OpenAI is not configured"):
        await client.complete_json(system_prompt="system", user_prompt="user")
