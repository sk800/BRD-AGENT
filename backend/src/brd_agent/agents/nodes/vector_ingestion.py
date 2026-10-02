from typing import Any

from brd_agent.agents.state import AgentState
from brd_agent.core.database import get_mongo_database
from brd_agent.domain.repositories.vector_ingestion_repository import (
    VectorIngestionRepository,
)
from brd_agent.services.vector_ingestion_service import VectorIngestionService


async def vector_ingestion_node(state: AgentState) -> dict[str, Any]:
    """Embed retrievable chunks and upsert vectors into LanceDB."""

    chunks = state.get("chunks") or []
    if not chunks:
        return {
            "vector_ingestion_status": "skipped",
            "vectors_ingested": 0,
            "vector_ingestion_skipped_attachments": 0,
            "vector_ingestion_results": [],
            "current_stage": "vector_ingestion",
        }

    service = VectorIngestionService(
        VectorIngestionRepository(get_mongo_database())
    )

    result = await service.ingest_chunks(
        user_id=state.get("user_id", ""),
        conversation_id=state.get("conversation_id", ""),
        message_id=state.get("message_id", ""),
        attachments=state.get("attachments") or [],
        chunks=chunks,
        chunking_method=state.get("chunking_method", "recursive"),
    )

    return {
        **result,
        "current_stage": "vector_ingestion",
    }
