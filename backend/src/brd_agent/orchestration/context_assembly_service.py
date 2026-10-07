"""Content assembly & context orchestration.

Uploaded files are ingested into the vector DB at upload time. For a requirement this
service gathers:
  1) relevant chunks from LanceDB (uploads only), and
  2) live enterprise knowledge via MCP (Confluence / ServiceNow) — not embedded.
The combined package is returned to the caller for later workflow stages.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

from brd_agent.core.config import get_settings
from brd_agent.intake.services.evidence_assessment_service import (
    EvidenceAssessmentService,
)
from brd_agent.ingestion.vector.retrieval import VectorRetrievalService
from brd_agent.services.enterprise_knowledge_service import EnterpriseKnowledgeService

logger = logging.getLogger(__name__)


@dataclass
class EnterpriseSourceRequest:
    platform: str
    action: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class AssembledContext:
    requirement_text: str
    uploaded_document_chunks: list[dict[str, Any]]
    enterprise_knowledge: list[dict[str, Any]]
    status: str = "assembled"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ContentAssemblyService:
    def __init__(
        self,
        retrieval: VectorRetrievalService | None = None,
        enterprise: EnterpriseKnowledgeService | None = None,
        assessor: EvidenceAssessmentService | None = None,
    ) -> None:
        self._retrieval = retrieval or VectorRetrievalService()
        self._enterprise = enterprise or EnterpriseKnowledgeService()
        self._assessor = assessor or EvidenceAssessmentService()

    async def assemble_for_requirement(
        self,
        *,
        user_id: str,
        conversation_id: str,
        requirement_text: str,
        enterprise_sources: list[EnterpriseSourceRequest] | None = None,
        retrieval_top_k: int | None = None,
    ) -> AssembledContext:
        settings = get_settings()
        top_k = (
            settings.context_retrieval_top_k
            if retrieval_top_k is None
            else retrieval_top_k
        )
        requirement = requirement_text.strip()
        if not requirement:
            raise ValueError("requirement_text is required for context assembly")
        if not user_id.strip() or not conversation_id.strip():
            raise ValueError("user_id and conversation_id are required for context assembly")
        if not 1 <= top_k <= 50:
            raise ValueError("retrieval_top_k must be between 1 and 50")

        uploaded_chunks = await self._retrieval.search_uploaded_documents(
            user_id=user_id,
            conversation_id=conversation_id,
            query=requirement,
            top_k=top_k,
        )

        enterprise_knowledge: list[dict[str, Any]] = []
        for source in enterprise_sources or []:
            result = await self._enterprise.fetch_from_platform(
                source.platform,
                source.action,
                source.params,
            )
            enterprise_knowledge.append(
                {
                    "platform": source.platform,
                    "action": source.action,
                    "params": source.params,
                    "result": result,
                }
            )

        logger.info(
            "Context assembly | conversation=%s uploads_hits=%s enterprise_fetches=%s",
            conversation_id,
            len(uploaded_chunks),
            len(enterprise_knowledge),
        )

        return AssembledContext(
            requirement_text=requirement,
            uploaded_document_chunks=uploaded_chunks,
            enterprise_knowledge=enterprise_knowledge,
        )

    async def assemble_for_checklist(
        self,
        *,
        user_id: str,
        conversation_id: str,
        checklist: list[dict[str, Any]],
        conversation: list[dict[str, str]],
        enterprise_sources: list[EnterpriseSourceRequest] | None = None,
        retrieval_top_k: int | None = None,
    ) -> dict[str, Any]:
        if not user_id.strip() or not conversation_id.strip():
            raise ValueError("user_id and conversation_id are required for context assembly")
        if not checklist:
            return {"items": [], "status": "empty"}

        settings = get_settings()
        top_k = (
            settings.context_retrieval_top_k
            if retrieval_top_k is None
            else retrieval_top_k
        )
        if not 1 <= top_k <= 50:
            raise ValueError("retrieval_top_k must be between 1 and 50")

        contexts: list[dict[str, Any]] = []
        for item in checklist:
            requirement = str(item.get("label", "")).strip()
            if not requirement:
                raise ValueError("Each checklist item must include a non-empty label")
            uploaded_chunks = await self._retrieval.search_uploaded_documents(
                user_id=user_id,
                conversation_id=conversation_id,
                query=requirement,
                top_k=min(top_k, 3),
            )
            enterprise_knowledge = await self._enterprise.search_for_requirement(
                requirement
            )
            for source in enterprise_sources or []:
                result = await self._enterprise.fetch_from_platform(
                    source.platform,
                    source.action,
                    source.params,
                )
                enterprise_knowledge.append(
                    {
                        "platform": source.platform,
                        "action": source.action,
                        "params": source.params,
                        "result": result,
                    }
                )
            contexts.append(
                {
                    "key": item["key"],
                    "requirement_text": requirement,
                    "uploaded_document_chunks": uploaded_chunks,
                    "enterprise_knowledge": enterprise_knowledge,
                }
            )

        assessments = await self._assessor.assess(
            checklist=checklist,
            conversation=conversation,
            evidence=contexts,
        )
        assessment_by_key = {item["key"]: item for item in assessments}
        assembled_items = []
        for item, context in zip(checklist, contexts, strict=True):
            assessment = assessment_by_key[item["key"]]
            assembled_items.append(
                {
                    **item,
                    **assessment,
                    "uploaded_document_chunks": context["uploaded_document_chunks"],
                    "enterprise_knowledge": context["enterprise_knowledge"],
                }
            )

        status = (
            "needs_user_input"
            if any(
                item["status"] in {"missing", "needs_clarification"}
                for item in assembled_items
            )
            else "assembled"
        )
        logger.info(
            "Checklist context assembly | conversation=%s items=%s status=%s",
            conversation_id,
            len(assembled_items),
            status,
        )
        return {"items": assembled_items, "status": status}
