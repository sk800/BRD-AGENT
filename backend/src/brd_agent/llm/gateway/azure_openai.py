"""Minimal Azure OpenAI chat-completions client."""

from __future__ import annotations

import json
from typing import Any

import httpx

from brd_agent.core.config import get_settings


class AzureOpenAIClient:
    def __init__(
        self,
        *,
        timeout_seconds: float = 45.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = get_settings()
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        endpoint = self._settings.azure_openai_endpoint.rstrip("/")
        deployment = self._settings.azure_openai_deployment
        api_key = self._settings.azure_openai_api_key
        if not endpoint or not deployment or not api_key:
            raise RuntimeError(
                "Azure OpenAI is not configured. Set AZURE_OPENAI_ENDPOINT, "
                "AZURE_OPENAI_DEPLOYMENT, and AZURE_OPENAI_API_KEY."
            )

        url = f"{endpoint}/openai/deployments/{deployment}/chat/completions"
        params = {"api-version": self._settings.azure_openai_api_version}
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "max_completion_tokens": self._settings.llm_max_completion_tokens,
        }

        async with httpx.AsyncClient(
            timeout=self._timeout_seconds,
            transport=self._transport,
        ) as client:
            response = await client.post(
                url,
                params=params,
                headers={"api-key": api_key},
                json=payload,
            )
            response.raise_for_status()

        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("Azure OpenAI returned an invalid chat response") from exc
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Azure OpenAI returned an empty response")

        try:
            result = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError("Azure OpenAI returned invalid JSON content") from exc
        if not isinstance(result, dict):
            raise ValueError("Azure OpenAI JSON response must be an object")
        return result
