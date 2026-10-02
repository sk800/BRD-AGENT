"""Retrieve uploaded-document chunks from LanceDB (ingestion layer only)."""

from __future__ import annotations

import logging
from typing import Any

from brd_agent.ingestion.pipeline.embedding.bge_embedder import embed_texts
from brd_agent.ingestion.vector.lancedb_store import LanceChunkStore, TABLE_NAME

logger = logging.getLogger(__name__)


def _escape_literal(value: str) -> str:
    return value.replace("'", "''")


class VectorRetrievalService:
    """Semantic search over chunks that were ingested from user uploads."""

    def __init__(self, store: LanceChunkStore | None = None) -> None:
        self._store = store or LanceChunkStore()

    async def search_uploaded_documents(
        self,
        *,
        user_id: str,
        query: str,
        conversation_id: str | None = None,
        top_k: int = 8,
    ) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            return []

        if TABLE_NAME not in self._store._db.table_names():
            return []

        vectors = await embed_texts([query])
        if not vectors:
            return []

        table = self._store._db.open_table(TABLE_NAME)
        uid = _escape_literal(user_id)
        filter_expr = f"user_id = '{uid}'"
        if conversation_id:
            cid = _escape_literal(conversation_id)
            filter_expr = f"{filter_expr} AND conversation_id = '{cid}'"

        search = table.search(vectors[0]).where(filter_expr).limit(max(1, min(top_k, 50)))
        df = search.to_pandas()

        hits: list[dict[str, Any]] = []
        for _, row in df.iterrows():
            hits.append(
                {
                    "source": "uploaded_documents",
                    "vector_id": row.get("vector_id"),
                    "chunk_id": row.get("chunk_id"),
                    "chunk_type": row.get("chunk_type"),
                    "heading": row.get("heading"),
                    "attachment_id": row.get("attachment_id"),
                    "message_id": row.get("message_id"),
                    "text": row.get("text"),
                    "distance": float(row.get("_distance", 0.0))
                    if row.get("_distance") is not None
                    else None,
                }
            )

        logger.info(
            "Vector retrieval | user=%s conversation=%s hits=%s",
            user_id,
            conversation_id,
            len(hits),
        )
        return hits
