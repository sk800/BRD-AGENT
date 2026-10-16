from __future__ import annotations

import re
from typing import Any

from langchain_text_splitters.character import RecursiveCharacterTextSplitter


HEADING_TYPES = {"heading", "title", "section", "header"}
CONVERSATION_MESSAGE = re.compile(
    r"\[(?:\d{2}:\d{2}:\d{2}|\d{1,2}/\d{1,2}/\d{2,4},\s*"
    r"\d{1,2}:\d{2}\s*(?:am|pm))\]\s*[^:\n]{1,100}:",
    re.IGNORECASE,
)
EMAIL_HEADER = re.compile(
    r"^\s*From:\s*.+?\bTo:\s*.+?\b(?:Subject|Date):",
    re.IGNORECASE | re.DOTALL,
)


def _text_from_element(element: dict[str, Any]) -> str:
    """Convert an extracted element into plain text."""

    content = element.get("content", "")

    # Paragraphs, headings, lists, etc.
    if isinstance(content, str):
        return content.strip()

    # Structured content such as tables and figures.
    if isinstance(content, dict):

        # Tables
        if element.get("type") == "table":
            headers = content.get("headers", [])
            rows = content.get("rows", [])

            parts = []

            if headers:
                parts.append(
                    " | ".join(str(value) for value in headers)
                )

            for row in rows:
                parts.append(
                    " | ".join(str(value) for value in row)
                )

            return "\n".join(parts)

        # Figures
        if element.get("type") == "figure":
            return str(
                content.get("ocr_text", "")
            ).strip()

    return str(content).strip()


def _is_heading(element: dict[str, Any]) -> bool:
    """Check whether an extracted element is a heading."""

    return (
        element.get("type", "").lower()
        in HEADING_TYPES
    )


def _is_conversation_document(elements: list[dict[str, Any]]) -> bool:
    content_elements = [
        _text_from_element(element)
        for element in elements
        if not _is_heading(element) and _text_from_element(element)
    ]
    if not content_elements:
        return False

    marked_elements = sum(
        bool(CONVERSATION_MESSAGE.search(text))
        for text in content_elements
    )
    message_count = sum(
        len(CONVERSATION_MESSAGE.findall(text))
        for text in content_elements
    )
    return message_count >= 5 and marked_elements / len(content_elements) >= 0.5


def _split_conversation_messages(text: str) -> list[str]:
    matches = list(CONVERSATION_MESSAGE.finditer(text))
    if not matches:
        return [text.strip()] if text.strip() else []

    messages: list[str] = []
    if text[: matches[0].start()].strip():
        messages.append(text[: matches[0].start()].strip())
    messages.extend(
        text[match.start() : next_start].strip()
        for match, next_start in zip(
            matches,
            [match.start() for match in matches[1:]] + [len(text)],
            strict=True,
        )
        if text[match.start() : next_start].strip()
    )
    return messages


def _build_conversation_sections(
    elements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    heading: str | None = None

    for element in elements:
        text = _text_from_element(element)
        if not text:
            continue
        if _is_heading(element):
            heading = text
            continue

        for message_index, message in enumerate(_split_conversation_messages(text)):
            sections.append(
                {
                    "heading": heading,
                    "elements": [{"type": "paragraph", "content": message}],
                    "metadata": {
                        **(element.get("location") or {}),
                        "message_index": message_index,
                    },
                }
            )

    return sections


def _is_email_thread_document(elements: list[dict[str, Any]]) -> bool:
    content_elements = [
        _text_from_element(element)
        for element in elements
        if not _is_heading(element) and _text_from_element(element)
    ]
    if not content_elements:
        return False

    email_headers = sum(bool(EMAIL_HEADER.match(text)) for text in content_elements)
    return email_headers >= 5 and email_headers / len(content_elements) >= 0.1


def _build_email_thread_sections(
    elements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    heading: str | None = None
    current_section: dict[str, Any] | None = None

    def flush() -> None:
        nonlocal current_section
        if current_section is not None:
            sections.append(current_section)
            current_section = None

    for element in elements:
        text = _text_from_element(element)
        if not text:
            continue

        if _is_heading(element):
            flush()
            heading = text
            continue

        if EMAIL_HEADER.match(text):
            flush()
            current_section = {
                "heading": heading,
                "elements": [element],
                "metadata": {
                    **(element.get("location") or {}),
                    "email_thread": True,
                },
            }
        elif current_section is None:
            current_section = {
                "heading": heading,
                "elements": [element],
                "metadata": element.get("location") or {},
            }
        else:
            current_section["elements"].append(element)

    flush()
    return sections


def _build_sections(
    elements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Group extracted elements into document sections.

    A new section starts whenever a heading is encountered.
    """

    if _is_conversation_document(elements):
        return _build_conversation_sections(elements)
    if _is_email_thread_document(elements):
        return _build_email_thread_sections(elements)

    sections: list[dict[str, Any]] = []

    current_section: dict[str, Any] | None = None

    for element in elements:

        text = _text_from_element(element)

        if not text:
            continue

        # Start a new section when a heading is found.
        if _is_heading(element):

            current_section = {
                "heading": text,
                "elements": [],
                "metadata": {
                    "page": element.get(
                        "location", {}
                    ).get("page"),
                    "element_id": element.get(
                        "element_id"
                    ),
                },
            }

            sections.append(current_section)

        # Add normal content to the current section.
        elif current_section is not None:

            current_section["elements"].append(
                element
            )

        # Handle content appearing before the
        # first heading.
        else:

            current_section = {
                "heading": None,
                "elements": [element],
                "metadata": {
                    "page": element.get(
                        "location", {}
                    ).get("page"),
                },
            }

            sections.append(current_section)

    return sections


def structure_aware_parent_child(
    elements: list[dict[str, Any]],
    parent_chunk_size: int = 2000,
    child_chunk_size: int = 500,
    child_chunk_overlap: int = 50,
) -> list[dict[str, Any]]:
    """
    Structure-aware Parent-Child chunking.

    Pipeline:

        Extracted elements
                ↓
        Detect headings
                ↓
            Sections
                ↓
        Parent chunking
                ↓
         Child chunking

    Parent chunks preserve larger context.
    Child chunks are smaller chunks intended for retrieval.
    """

    # --------------------------------------------------
    # 1. Build sections using document structure
    # --------------------------------------------------

    sections = _build_sections(elements)

    # --------------------------------------------------
    # 2. Parent splitter
    # --------------------------------------------------

    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size=parent_chunk_size,
        chunk_overlap=0,
    )

    # --------------------------------------------------
    # 3. Child splitter
    # --------------------------------------------------

    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size=child_chunk_size,
        chunk_overlap=child_chunk_overlap,
    )

    chunks: list[dict[str, Any]] = []

    # --------------------------------------------------
    # 4. Process every section
    # --------------------------------------------------

    for section_index, section in enumerate(sections):

        heading = section["heading"]

        # Combine all elements belonging to this section.
        section_text = "\n\n".join(
            _text_from_element(element)
            for element in section["elements"]
        )

        # Keep the heading with the section content.
        if heading:
            section_text = (
                f"{heading}\n\n{section_text}"
            )

        # Skip empty sections.
        if not section_text.strip():
            continue

        # --------------------------------------------------
        # 5. Create parent chunks
        # --------------------------------------------------

        parent_texts = parent_splitter.split_text(
            section_text
        )

        for parent_index, parent_text in enumerate(
            parent_texts
        ):

            parent_id = (
                f"parent_{section_index}_{parent_index}"
            )

            child_texts = child_splitter.split_text(
                parent_text
            )

            # When the parent fits in one child window, child text equals
            # parent text — keep the parent only (no duplicate child row).
            standalone_parent = (
                len(child_texts) == 1
                and child_texts[0].strip() == parent_text.strip()
            )

            # ----------------------------------------------
            # Parent chunk
            # ----------------------------------------------

            parent = {
                "chunk_id": parent_id,
                "chunk_type": "parent",
                "text": parent_text,
                "metadata": {
                    **section["metadata"],
                    "heading": heading,
                    "section_index": section_index,
                    # False: embed/search children; True: this parent is the unit.
                    "standalone_parent": standalone_parent,
                },
            }

            chunks.append(parent)

            # ----------------------------------------------
            # 6. Create child chunks from parent
            # ----------------------------------------------

            if standalone_parent:
                continue

            for child_index, child_text in enumerate(
                child_texts
            ):

                child = {
                    "chunk_id": (
                        f"{parent_id}"
                        f"_child_{child_index}"
                    ),
                    "chunk_type": "child",
                    "parent_id": parent_id,
                    "text": child_text,
                    "metadata": {
                        **section["metadata"],
                        "heading": heading,
                        "section_index": section_index,
                        "parent_id": parent_id,
                    },
                }

                chunks.append(child)

    return chunks