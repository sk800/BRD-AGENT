"""Content and pipeline fingerprints for vector deduplication."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def sha256_hex(value: str | bytes) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def file_content_fingerprint(file_bytes: bytes) -> str:
    return sha256_hex(file_bytes)


def pipeline_version(
    *,
    embedding_model: str,
    embedding_pipeline_version: int,
    chunking_method: str,
) -> str:
    return (
        f"embed={embedding_model}:v{embedding_pipeline_version}"
        f":chunk={chunking_method}"
    )


def ingestion_key(
    *,
    user_id: str,
    content_sha256: str,
    pipeline: str,
) -> str:
    return sha256_hex(f"{user_id}:{content_sha256}:{pipeline}")


def vector_chunk_id(
    *,
    user_id: str,
    content_sha256: str,
    pipeline: str,
    chunk: dict[str, Any],
) -> str:
    """Stable id for LanceDB upserts across re-uploads of the same file."""

    payload = {
        "user_id": user_id,
        "content_sha256": content_sha256,
        "pipeline": pipeline,
        "chunk_id": chunk.get("chunk_id"),
        "chunk_type": chunk.get("chunk_type"),
        "text": chunk.get("text", "").strip(),
    }
    return sha256_hex(json.dumps(payload, sort_keys=True, ensure_ascii=False)) 
