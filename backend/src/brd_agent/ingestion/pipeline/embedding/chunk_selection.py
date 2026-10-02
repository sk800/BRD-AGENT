"""Select which chunks should be embedded for retrieval."""

from __future__ import annotations

from typing import Any


def chunks_for_embedding(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Parent-child: embed child chunks and standalone parents.
    Recursive: embed all recursive chunks.
    """

    selected: list[dict[str, Any]] = []

    for chunk in chunks:
        chunk_type = chunk.get("chunk_type")
        metadata = chunk.get("metadata") or {}

        if chunk_type == "recursive":
            selected.append(chunk)
            continue

        if chunk_type == "child":
            selected.append(chunk)
            continue

        if chunk_type == "parent" and metadata.get("standalone_parent"):
            selected.append(chunk)

    return selected
