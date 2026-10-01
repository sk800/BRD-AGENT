from typing import Any

from brd_agent.agents.state import AgentState
from brd_agent.knowledge.retrieval.embeddings import EmbeddingService


async def embedding_node(state: AgentState) -> dict[str, Any]:
    """Encode chunk text for the downstream vector-storage stage."""
    chunks = state.get("chunks") or []
    texts = [
        chunk.get("text", "")
        for chunk in chunks
        if chunk.get("text", "").strip()
    ]

    if not texts:
        return {
            "chunk_embeddings": [],
            "embedded_chunks": [],
            "embedding_dimension": 0,
            "embedding_status": "skipped",
            "current_stage": "embedding",
        }

    embeddings = EmbeddingService().embed_documents(texts)
    serialized_embeddings = embeddings.tolist()
    embedded_chunks = []
    for chunk, embedding in zip(
        (chunk for chunk in chunks if chunk.get("text", "").strip()),
        serialized_embeddings,
    ):
        embedded_chunks.append({**chunk, "embedding": embedding})

    return {
        "chunk_embeddings": serialized_embeddings,
        "embedded_chunks": embedded_chunks,
        "embedding_dimension": len(serialized_embeddings[0]),
        "embedding_status": "done",
        "current_stage": "embedding",
    }