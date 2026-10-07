"""Assess whether gathered evidence answers the BRD checklist."""

from __future__ import annotations

import json
from typing import Any, Protocol

from pydantic import ValidationError

from brd_agent.intake.models import RequirementEvidenceAssessment
from brd_agent.intake.prompts.evidence_assessment import (
    EVIDENCE_ASSESSMENT_SYSTEM_PROMPT,
)
from brd_agent.llm.gateway.azure_openai import AzureOpenAIClient


class JsonChatClient(Protocol):
    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]: ...


class EvidenceAssessmentService:
    def __init__(self, client: JsonChatClient | None = None) -> None:
        self._client = client or AzureOpenAIClient()

    async def assess(
        self,
        *,
        checklist: list[dict[str, Any]],
        conversation: list[dict[str, str]],
        evidence: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not checklist:
            return []

        input_payload = {
            "conversation": [
                {
                    "role": turn.get("role", ""),
                    "text": str(turn.get("text", ""))[:1000],
                }
                for turn in conversation[-12:]
            ],
            "checklist": checklist,
            "evidence": [
                {
                    "key": item.get("key"),
                    "requirement_text": item.get("requirement_text", ""),
                    "uploaded_document_chunks": [
                        {
                            "chunk_id": chunk.get("chunk_id"),
                            "text": str(chunk.get("text", ""))[:1500],
                        }
                        for chunk in item.get("uploaded_document_chunks", [])[:3]
                    ],
                    "enterprise_knowledge": [
                        {
                            "platform": source.get("platform"),
                            "action": source.get("action"),
                            "result": json.dumps(
                                source.get("result", {}),
                                ensure_ascii=False,
                                default=str,
                            )[:4000],
                        }
                        for source in item.get("enterprise_knowledge", [])
                    ],
                }
                for item in evidence
            ],
        }
        result = await self._client.complete_json(
            system_prompt=EVIDENCE_ASSESSMENT_SYSTEM_PROMPT,
            user_prompt=json.dumps(input_payload, ensure_ascii=False),
        )
        try:
            assessments = [
                RequirementEvidenceAssessment.model_validate(item)
                for item in result["items"]
            ]
        except (KeyError, TypeError, ValidationError) as exc:
            raise ValueError(
                "Azure OpenAI returned invalid checklist evidence assessments"
            ) from exc

        expected_keys = [str(item["key"]) for item in checklist]
        actual_keys = [item.key for item in assessments]
        if len(actual_keys) != len(set(actual_keys)) or set(actual_keys) != set(
            expected_keys
        ):
            raise ValueError(
                "Azure OpenAI evidence assessments must include each checklist key once"
            )

        by_key = {item.key: item.model_dump() for item in assessments}
        return [by_key[key] for key in expected_keys]
