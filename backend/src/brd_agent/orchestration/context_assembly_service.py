"""Content assembly & context orchestration (diagram: central green block).

Uploaded files are ingested into the vector DB at upload time. At BRD generation time
this service gathers:
  1) relevant chunks from LanceDB (uploads only), and
  2) live enterprise knowledge via MCP (Confluence / ServiceNow) — not embedded.
The combined package is passed to guardrails / LLM downstream.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

from brd_agent.core.config import get_settings
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
    ) -> None:
        self._retrieval = retrieval or VectorRetrievalService()
        self._enterprise = enterprise or EnterpriseKnowledgeService()

    async def assemble_for_brd_generation(
        self,
        *,
        user_id: str,
        conversation_id: str,
        requirement_text: str,
        enterprise_sources: list[EnterpriseSourceRequest] | None = None,
        retrieval_top_k: int | None = None,
    ) -> AssembledContext:
        settings = get_settings()
        top_k = retrieval_top_k or settings.context_retrieval_top_k
        requirement = requirement_text.strip()
        if not requirement:
            raise ValueError("requirement_text is required for BRD context assembly")

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
