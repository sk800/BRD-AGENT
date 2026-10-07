"""Standalone LangGraph for requirement discovery."""

from typing import Any

from langgraph.graph import END, START, StateGraph

from brd_agent.agents.state import AgentState
from brd_agent.agents.nodes.requirements import requirements_node
from brd_agent.agents.nodes.context_assembly import context_assembly_node
from brd_agent.agents.nodes.project_memory import (
    project_memory_read_node,
    project_memory_update_node,
)


def _after_requirements(state: AgentState) -> str:
    return "redirect" if state.get("conversation_route") == "redirect" else "assemble"


def get_requirements_graph():
    graph = StateGraph(AgentState)
    graph.add_node("memory_read", project_memory_read_node)
    graph.add_node("requirements", requirements_node)
    graph.add_node("context_assembly", context_assembly_node)
    graph.add_node("memory_update", project_memory_update_node)
    graph.add_edge(START, "memory_read")
    graph.add_edge("memory_read", "requirements")
    graph.add_conditional_edges(
        "requirements",
        _after_requirements,
        {"assemble": "context_assembly", "redirect": END},
    )
    graph.add_edge("context_assembly", "memory_update")
    graph.add_edge("memory_update", END)
    return graph.compile()


async def run_requirements(
    *,
    request: str | None,
    chunks: list[dict[str, Any]] | None = None,
    conversation_history: list[dict[str, str]] | None = None,
    user_id: str | None = None,
    conversation_id: str | None = None,
    prior_checklist: list[dict[str, Any]] | None = None,
    enterprise_sources: list[dict[str, Any]] | None = None,
    retrieval_top_k: int | None = None,
) -> dict[str, Any]:
    return await get_requirements_graph().ainvoke(
        {
            "current_user_text": request,
            "chunks": chunks or [],
            "conversation_history": conversation_history or [],
            "user_id": user_id or "",
            "conversation_id": conversation_id or "",
            "prior_checklist": prior_checklist or [],
            "enterprise_sources": enterprise_sources or [],
            "retrieval_top_k": retrieval_top_k,
        }
    )
