"""Discover a concise, project-specific checklist with Azure OpenAI."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import ValidationError

from brd_agent.intake.models import RequirementChecklist, RequirementDiscoveryResult
from brd_agent.intake.prompts.requirement_discovery import (
    REQUIREMENT_DISCOVERY_SYSTEM_PROMPT,
)
from brd_agent.llm.gateway.azure_openai import AzureOpenAIClient


class JsonChatClient(Protocol):
    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]: ...


class RequirementDiscoveryService:
    def __init__(self, client: JsonChatClient | None = None) -> None:
        self._client = client or AzureOpenAIClient()

    async def discover(self, discovery_input: str) -> list[dict[str, Any]]:
        result = await self.discover_result(discovery_input)
        return result["items"]

    async def discover_result(self, discovery_input: str) -> dict[str, Any]:
        if not discovery_input.strip():
            raise ValueError("Requirement discovery input cannot be empty")

        result = await self._client.complete_json(
            system_prompt=REQUIREMENT_DISCOVERY_SYSTEM_PROMPT,
            user_prompt=discovery_input.strip(),
        )
        if "route" not in result:
            try:
                discovery = RequirementDiscoveryResult.model_validate(
                    RequirementChecklist.model_validate(result).model_dump()
                )
            except ValidationError as nested_exc:
                raise ValueError(
                    "Azure OpenAI returned an invalid requirements checklist"
                ) from nested_exc
        else:
            try:
                discovery = RequirementDiscoveryResult.model_validate(result)
            except ValidationError as exc:
                raise ValueError(
                    "Azure OpenAI returned an invalid requirements checklist"
                ) from exc

        if discovery.route == "redirect":
            if not discovery.redirect_message or not discovery.redirect_message.strip():
                raise ValueError("Azure OpenAI returned an empty redirect message")
            return {
                "route": "redirect",
                "redirect_message": discovery.redirect_message.strip(),
                "items": [],
            }

        seen_keys: set[str] = set()
        seen_labels: set[str] = set()
        normalized_items: list[dict[str, Any]] = []
        for item in discovery.items:
            key = item.key.casefold()
            label = item.label.strip()
            label_key = label.casefold()
            if key in seen_keys or label_key in seen_labels:
                continue
            seen_keys.add(key)
            seen_labels.add(label_key)
            normalized_items.append(
                {
                    **item.model_dump(),
                    "label": label,
                    "status": "missing",
                }
            )

        return {
            "route": "project",
            "redirect_message": None,
            "items": normalized_items,
        }
