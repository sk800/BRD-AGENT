from typing import Any

from langgraph.graph import END, START, StateGraph

from brd_agent.agents.nodes.embedding import embedding_node
from brd_agent.agents.state import AgentState

_embedding_graph = None


def build_embedding_graph():
    graph = StateGraph(AgentState)
    graph.add_node("embedding", embedding_node)
    graph.add_edge(START, "embedding")
    graph.add_edge("embedding", END)
    return graph.compile()


def get_embedding_graph():
    global _embedding_graph
    if _embedding_graph is None:
        _embedding_graph = build_embedding_graph()
    return _embedding_graph


async def run_embedding(
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Encode chunk text after the chunking graph completes."""
    initial_state: AgentState = {
        "chunks": chunks,
        "chunk_embeddings": [],
        "embedded_chunks": [],
        "embedding_dimension": 0,
        "embedding_status": "pending",
        "current_stage": "embedding",
        "errors": [],
    }
    return await get_embedding_graph().ainvoke(initial_state)