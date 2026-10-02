from typing import Any

from brd_agent.agents.state import AgentState
from brd_agent.orchestration.context_assembly_service import (
    ContentAssemblyService,
    EnterpriseSourceRequest,
)


async def context_assembly_node(state: AgentState) -> dict[str, Any]:
    """Assemble vector-retrieved uploads + live MCP enterprise context for BRD generation."""

    requirement = (state.get("requirement_text") or state.get("current_user_text") or "").strip()
    raw_sources = state.get("enterprise_sources") or []

    enterprise_sources = [
        EnterpriseSourceRequest(
            platform=item["platform"],
            action=item["action"],
            params=item.get("params") or {},
        )
        for item in raw_sources
        if item.get("platform") and item.get("action")
    ]

    service = ContentAssemblyService()
    assembled = await service.assemble_for_brd_generation(
        user_id=state.get("user_id", ""),
        conversation_id=state.get("conversation_id", ""),
        requirement_text=requirement,
        enterprise_sources=enterprise_sources,
        retrieval_top_k=state.get("retrieval_top_k"),
    )

    return {
        "assembled_context": assembled.to_dict(),
        "context_assembly_status": assembled.status,
        "current_stage": "context_assembly",
    }
