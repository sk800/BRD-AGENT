from typing import Any

from langgraph.graph import END, START, StateGraph

from brd_agent.agents.nodes.chunking import (
    parent_child_chunking_node,
    recursive_chunking_node,
    route_chunking,
)
from brd_agent.agents.state import AgentState


_chunking_graph = None


def build_chunking_graph():
    graph = StateGraph(AgentState)

    # Chunking nodes
    graph.add_node(
        "parent_child",
        parent_child_chunking_node,
    )

    graph.add_node(
        "recursive",
        recursive_chunking_node,
    )

    # START → Conditional Router
    graph.add_conditional_edges(
        START,
        route_chunking,
        {
            "parent_child": "parent_child",
            "recursive": "recursive",
        },
    )

    # Both chunking pipelines → END
    graph.add_edge(
        "parent_child",
        END,
    )

    graph.add_edge(
        "recursive",
        END,
    )

    return graph.compile()


def get_chunking_graph():
    global _chunking_graph

    if _chunking_graph is None:
        _chunking_graph = build_chunking_graph()

    return _chunking_graph


async def run_chunking(
    extracted_documents: list[dict[str, Any]],
    *,
    chunking_method: str = "recursive",
) -> dict[str, Any]:
    """Execute the selected chunking pipeline."""

    initial_state: AgentState = {
        "extracted_documents": extracted_documents,
        "chunking_method": chunking_method,
        "chunks": [],
        "current_stage": "chunking",
        "errors": [],
    }

    graph = get_chunking_graph()

    return await graph.ainvoke(initial_state)