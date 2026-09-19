from __future__ import annotations

from typing import Any

from langchain_text_splitters.character import (
    RecursiveCharacterTextSplitter,
)

from brd_agent.ingestion.pipeline.chunking.parent_child import (
    _build_sections,
    _text_from_element,
)


def structure_aware_recursive(
    elements: list[dict[str, Any]],
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[dict[str, Any]]:
    """
    Structure-aware recursive chunking.

    1. Detect document sections using headings.
    2. Keep each section independent.
    3. Recursively split the section into smaller chunks.
    4. Preserve section metadata such as heading and page.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative")

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size"
        )

    # --------------------------------------------------
    # 1. Build sections from document structure
    # --------------------------------------------------

    sections = _build_sections(elements)

    # --------------------------------------------------
    # 2. Create recursive splitter
    # --------------------------------------------------

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks: list[dict[str, Any]] = []

    # --------------------------------------------------
    # 3. Process each section independently
    # --------------------------------------------------

    for section_index, section in enumerate(sections):

        heading = section["heading"]

        section_text = "\n\n".join(
            _text_from_element(element)
            for element in section["elements"]
        )

        # Keep heading with the section content.
        if heading:
            section_text = (
                f"{heading}\n\n{section_text}"
            )

        # Skip empty sections.
        if not section_text.strip():
            continue

        # --------------------------------------------------
        # 4. Recursively split section
        # --------------------------------------------------

        split_texts = splitter.split_text(
            section_text
        )

        # --------------------------------------------------
        # 5. Create chunk objects
        # --------------------------------------------------

        for chunk_index, chunk_text in enumerate(
            split_texts
        ):

            if not chunk_text.strip():
                continue

            chunks.append(
                {
                    "chunk_id": (
                        f"chunk_"
                        f"{section_index}_"
                        f"{chunk_index}"
                    ),
                    "chunk_type": "recursive",
                    "text": chunk_text,
                    "metadata": {
                        **section["metadata"],
                        "heading": heading,
                        "section_index": section_index,
                    },
                }
            )

    return chunks