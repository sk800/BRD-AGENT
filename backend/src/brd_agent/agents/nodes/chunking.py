from typing import Any

from brd_agent.agents.state import AgentState
from brd_agent.ingestion.pipeline.chunking.parent_child import (
    structure_aware_parent_child,
)
from brd_agent.ingestion.pipeline.chunking.recursive import (
    structure_aware_recursive,
)


def _tag_chunks_with_attachment(
    chunks: list[dict[str, Any]],
    *,
    attachment_id: str,
    original_filename: str | None,
) -> list[dict[str, Any]]:
    for chunk in chunks:
        metadata = dict(chunk.get("metadata") or {})
        metadata["attachment_id"] = attachment_id
        if original_filename:
            metadata["original_filename"] = original_filename
        chunk["metadata"] = metadata
    return chunks


def _chunk_all_documents(
    state: AgentState,
    chunker,
) -> list[dict[str, Any]]:
    all_chunks: list[dict[str, Any]] = []

    for document in state.get("extracted_documents", []):
        extraction = document.get("extraction", {})
        if not isinstance(extraction, dict):
            continue

        elements = extraction.get("elements", [])
        if not isinstance(elements, list) or not elements:
            continue

        document_chunks = chunker(elements)
        all_chunks.extend(
            _tag_chunks_with_attachment(
                document_chunks,
                attachment_id=document.get("attachment_id", ""),
                original_filename=document.get("original_filename"),
            )
        )

    return all_chunks


async def parent_child_chunking_node(
    state: AgentState,
) -> dict[str, Any]:
    """Run the structure-aware parent-child pipeline."""

    chunks = _chunk_all_documents(state, structure_aware_parent_child)

    return {
        "chunks": chunks,
        "chunking_status": "done",
        "current_stage": "chunking",
    }


async def recursive_chunking_node(
    state: AgentState,
) -> dict[str, Any]:
    """Run the structure-aware recursive pipeline."""

    chunks = _chunk_all_documents(state, structure_aware_recursive)

    return {
        "chunks": chunks,
        "chunking_status": "done",
        "current_stage": "chunking",
    }


async def skip_chunking_node(
    state: AgentState,
) -> dict[str, Any]:
    """Skip chunking when extraction produced no documents."""

    return {
        "chunks": [],
        "chunking_status": "skipped",
        "current_stage": "chunking",
    }


def route_chunking(
    state: AgentState,
) -> str:
    """Select the chunking pipeline."""

    method = state.get(
        "chunking_method",
        "recursive",
    )

    if method == "parent_child":
        return "parent_child"

    return "recursive"