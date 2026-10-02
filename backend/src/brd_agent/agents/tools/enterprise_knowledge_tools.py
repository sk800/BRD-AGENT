"""LangGraph-ready helpers that call enterprise MCP tools."""

from __future__ import annotations

from typing import Any

from brd_agent.services.enterprise_knowledge_service import EnterpriseKnowledgeService


async def fetch_enterprise_knowledge(
    platform: str,
    action: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Live MCP fetch for BRD context assembly (not vector ingestion)."""
    service = EnterpriseKnowledgeService()
    return await service.fetch_from_platform(platform, action, params or {})
