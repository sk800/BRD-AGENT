from typing import Any

from langgraph.graph import END, START, StateGraph

from brd_agent.agents.nodes.extraction import extraction_node
from brd_agent.agents.state import AgentState

_extraction_graph = None


def build_extraction_graph():
    graph = StateGraph(AgentState)
    graph.add_node("extraction", extraction_node)
    graph.add_edge(START, "extraction")
    graph.add_edge("extraction", END)
    return graph.compile()


def get_extraction_graph():
    global _extraction_graph
    if _extraction_graph is None:
        _extraction_graph = build_extraction_graph()
    return _extraction_graph


async def run_extraction(
    attachments: list[dict[str, Any]],
    *,
    user_id: str,
    conversation_id: str,
    message_id: str,
) -> dict[str, Any]:
    """Execute the extraction subgraph for one chat message."""
    initial_state: AgentState = {
        "user_id": user_id,
        "conversation_id": conversation_id,
        "message_id": message_id,
        "attachments": attachments,
        "extracted_documents": [],
        "extraction_errors": [],
        "extraction_status": "pending",
        "current_stage": "extraction",
        "errors": [],
    }

    graph = get_extraction_graph()
    return await graph.ainvoke(initial_state)
