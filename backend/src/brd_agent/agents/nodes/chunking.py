from typing import Any

from brd_agent.agents.state import AgentState
from brd_agent.ingestion.pipeline.chunking.parent_child import (
    structure_aware_parent_child,
)
from brd_agent.ingestion.pipeline.chunking.recursive import (
    structure_aware_recursive,
)


def _get_all_elements(
    state: AgentState,
) -> list[dict[str, Any]]:
    """Collect extracted elements from all documents."""

    elements: list[dict[str, Any]] = []

    for document in state.get("extracted_documents", []):
        extraction = document.get("extraction", {})

        if not isinstance(extraction, dict):
            continue

        document_elements = extraction.get(
            "elements", []
        )

        if isinstance(document_elements, list):
            elements.extend(document_elements)

    return elements


async def parent_child_chunking_node(
    state: AgentState,
) -> dict[str, Any]:
    """Run the structure-aware parent-child pipeline."""

    elements = _get_all_elements(state)

    chunks = structure_aware_parent_child(
        elements
    )

    return {
        "chunks": chunks,
        "current_stage": "chunking",
    }


async def recursive_chunking_node(
    state: AgentState,
) -> dict[str, Any]:
    """Run the structure-aware recursive pipeline."""

    elements = _get_all_elements(state)

    chunks = structure_aware_recursive(
        elements
    )

    return {
        "chunks": chunks,
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