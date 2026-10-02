from typing import Any

from langgraph.graph import END, START, StateGraph

from brd_agent.agents.nodes.context_assembly import context_assembly_node
from brd_agent.agents.state import AgentState


def get_context_assembly_graph():
    graph = StateGraph(AgentState)
    graph.add_node("context_assembly", context_assembly_node)
    graph.add_edge(START, "context_assembly")
    graph.add_edge("context_assembly", END)
    return graph.compile()


async def run_context_assembly(
    *,
    user_id: str,
    conversation_id: str,
    requirement_text: str,
    enterprise_sources: list[dict[str, Any]] | None = None,
    retrieval_top_k: int | None = None,
) -> dict[str, Any]:
    graph = get_context_assembly_graph()
    return await graph.ainvoke(
        {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "requirement_text": requirement_text,
            "enterprise_sources": enterprise_sources or [],
            "retrieval_top_k": retrieval_top_k,
        }
    )
