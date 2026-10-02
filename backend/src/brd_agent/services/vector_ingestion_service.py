from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from brd_agent.core.config import get_settings
from brd_agent.domain.repositories.vector_ingestion_repository import (
    VectorIngestionRepository,
)
from brd_agent.ingestion.pipeline.embedding.bge_embedder import embed_texts
from brd_agent.ingestion.pipeline.embedding.chunk_selection import chunks_for_embedding
from brd_agent.ingestion.pipeline.embedding.fingerprint import (
    file_content_fingerprint,
    ingestion_key,
    pipeline_version,
    vector_chunk_id,
)
from brd_agent.core.logging.extraction_logger import (
    log_lance_ingestion_rows,
    log_lance_ingestion_skipped,
)
from brd_agent.ingestion.vector.lancedb_store import LanceChunkStore

logger = logging.getLogger(__name__)


class VectorIngestionService:
    def __init__(self, vector_repo: VectorIngestionRepository) -> None:
        self._vector_repo = vector_repo
        self._lance = LanceChunkStore()

    async def ingest_chunks(
        self,
        *,
        user_id: str,
        conversation_id: str,
        message_id: str,
        attachments: list[dict[str, Any]],
        chunks: list[dict[str, Any]],
        chunking_method: str,
    ) -> dict[str, Any]:
        settings = get_settings()
        pipeline = pipeline_version(
            embedding_model=settings.embedding_model,
            embedding_pipeline_version=settings.embedding_pipeline_version,
            chunking_method=chunking_method,
        )

        attachment_map = {item["id"]: item for item in attachments}
        chunks_by_attachment: dict[str, list[dict[str, Any]]] = {}

        for chunk in chunks:
            attachment_id = (chunk.get("metadata") or {}).get("attachment_id")
            if not attachment_id:
                continue
            chunks_by_attachment.setdefault(attachment_id, []).append(chunk)

        ingested_vectors = 0
        skipped_attachments = 0
        results: list[dict[str, Any]] = []

        for attachment_id, attachment_chunks in chunks_by_attachment.items():
            attachment = attachment_map.get(attachment_id)
            if attachment is None:
                continue

            content_sha256 = attachment.get("content_sha256")
            if not content_sha256:
                storage_path = attachment.get("storage_path")
                if storage_path and Path(storage_path).is_file():
                    content_sha256 = file_content_fingerprint(
                        Path(storage_path).read_bytes()
                    )
                else:
                    log_lance_ingestion_skipped(
                        attachment_id=attachment_id,
                        status="failed",
                        error="Missing content_sha256 and storage_path",
                    )
                    results.append(
                        {
                            "attachment_id": attachment_id,
                            "status": "failed",
                            "error": "Missing content_sha256 and storage_path",
                        }
                    )
                    continue

            key = ingestion_key(
                user_id=user_id,
                content_sha256=content_sha256,
                pipeline=pipeline,
            )
            existing = await self._vector_repo.find_by_key(key)
            if existing is not None:
                skipped_attachments += 1
                log_lance_ingestion_skipped(
                    attachment_id=attachment_id,
                    status="skipped_duplicate",
                    ingestion_key=key,
                    pipeline_version=pipeline,
                )
                results.append(
                    {
                        "attachment_id": attachment_id,
                        "status": "skipped_duplicate",
                        "ingestion_key": key,
                        "pipeline_version": pipeline,
                    }
                )
                continue

            embeddable = chunks_for_embedding(attachment_chunks)
            if not embeddable:
                log_lance_ingestion_skipped(
                    attachment_id=attachment_id,
                    status="skipped_empty",
                    ingestion_key=key,
                    pipeline_version=pipeline,
                )
                results.append(
                    {
                        "attachment_id": attachment_id,
                        "status": "skipped_empty",
                    }
                )
                continue

            texts = [chunk.get("text", "").strip() for chunk in embeddable]
            vectors = await embed_texts(texts)

            rows: list[dict[str, Any]] = []
            for chunk, vector in zip(embeddable, vectors, strict=True):
                vid = vector_chunk_id(
                    user_id=user_id,
                    content_sha256=content_sha256,
                    pipeline=pipeline,
                    chunk=chunk,
                )
                metadata = chunk.get("metadata") or {}
                rows.append(
                    {
                        "vector_id": vid,
                        "user_id": user_id,
                        "conversation_id": conversation_id,
                        "message_id": message_id,
                        "attachment_id": attachment_id,
                        "content_sha256": content_sha256,
                        "ingestion_key": key,
                        "pipeline_version": pipeline,
                        "chunk_id": chunk.get("chunk_id"),
                        "chunk_type": chunk.get("chunk_type"),
                        "parent_id": chunk.get("parent_id"),
                        "heading": metadata.get("heading"),
                        "section_index": metadata.get("section_index"),
                        "text": chunk.get("text", ""),
                        "vector": vector,
                    }
                )

            log_lance_ingestion_rows(rows)
            count = self._lance.upsert_chunks(rows)
            ingested_vectors += count

            await self._vector_repo.register(
                ingestion_key=key,
                user_id=user_id,
                content_sha256=content_sha256,
                pipeline_version=pipeline,
                attachment_id=attachment_id,
                message_id=message_id,
                conversation_id=conversation_id,
                vector_count=count,
            )

            results.append(
                {
                    "attachment_id": attachment_id,
                    "status": "ingested",
                    "ingestion_key": key,
                    "pipeline_version": pipeline,
                    "vector_count": count,
                }
            )

        if not chunks_by_attachment:
            status = "skipped"
        elif ingested_vectors == 0 and skipped_attachments > 0:
            status = "skipped_duplicate"
        elif ingested_vectors > 0:
            status = "done"
        else:
            status = "skipped"

        return {
            "vector_ingestion_status": status,
            "vectors_ingested": ingested_vectors,
            "vector_ingestion_skipped_attachments": skipped_attachments,
            "vector_ingestion_results": results,
            "embedding_model": settings.embedding_model,
            "embedding_pipeline_version": pipeline,
        }
