from typing import Any

from langgraph.graph import END, START, StateGraph

from brd_agent.agents.nodes.chunking import (
    parent_child_chunking_node,
    recursive_chunking_node,
    route_chunking,
    skip_chunking_node,
)
from brd_agent.agents.nodes.extraction import extraction_node
from brd_agent.agents.state import AgentState


_ingestion_graph = None


def route_after_extraction(state: AgentState) -> str:
    """Run chunking when at least one document was extracted."""

    if not state.get("extracted_documents"):
        return "skip_chunking"

    return route_chunking(state)


def build_ingestion_graph():
    graph = StateGraph(AgentState)

    graph.add_node("extraction", extraction_node)
    graph.add_node("skip_chunking", skip_chunking_node)
    graph.add_node("parent_child", parent_child_chunking_node)
    graph.add_node("recursive", recursive_chunking_node)

    graph.add_edge(START, "extraction")

    graph.add_conditional_edges(
        "extraction",
        route_after_extraction,
        {
            "skip_chunking": "skip_chunking",
            "parent_child": "parent_child",
            "recursive": "recursive",
        },
    )

    graph.add_edge("skip_chunking", END)
    graph.add_edge("parent_child", END)
    graph.add_edge("recursive", END)

    return graph.compile()


def get_ingestion_graph():
    global _ingestion_graph

    if _ingestion_graph is None:
        _ingestion_graph = build_ingestion_graph()

    return _ingestion_graph


async def run_ingestion(
    attachments: list[dict[str, Any]],
    *,
    user_id: str,
    conversation_id: str,
    message_id: str,
    chunking_method: str = "recursive",
) -> dict[str, Any]:
    """Extract uploaded files, then chunk extracted elements."""

    initial_state: AgentState = {
        "user_id": user_id,
        "conversation_id": conversation_id,
        "message_id": message_id,
        "attachments": attachments,
        "extracted_documents": [],
        "extraction_errors": [],
        "extraction_status": "pending",
        "chunking_method": chunking_method,
        "chunks": [],
        "chunking_status": "pending",
        "current_stage": "extraction",
        "errors": [],
    }

    graph = get_ingestion_graph()
    return await graph.ainvoke(initial_state)
