"""Single entry point for routing files to format-specific extractors."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

logger = logging.getLogger("brd_agent.extraction")


TEXT_FILES = frozenset({
    ".txt",
    ".md",
    ".markdown",
    ".log",
    ".rst",
    ".json",
    ".xml",
})

IMAGE_FILES = frozenset({
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".tif",
    ".tiff",
    ".bmp",
})

SPREADSHEET_FILES = frozenset({
    ".csv",
    ".xlsx",
    ".xlsm",
    ".xls",
    ".tsv",
})

EMAIL_FILES = frozenset({
    ".eml",
})

HTML_FILES = frozenset({
    ".html",
    ".htm",
})

SUPPORTED_FILES = (
    TEXT_FILES
    | IMAGE_FILES
    | SPREADSHEET_FILES
    | EMAIL_FILES
    | HTML_FILES
    | {".docx", ".pptx", ".pdf"}
)

Extractor = Callable[[str], dict]


def detect_pdf_type(file_path: str | Path) -> str:
    """
    Detect whether a PDF contains native/selectable text.

    Returns:
        "digital" if native text is found.
        "scanned" otherwise.
    """
    import fitz

    with fitz.open(file_path) as pdf:
        return (
            "digital"
            if any(page.get_text("text").strip() for page in pdf)
            else "scanned"
        )


def _pdf_extractor(file_path: str) -> dict:
    """Route PDF to the correct PDF extractor."""

    if detect_pdf_type(file_path) == "digital":
        from brd_agent.extraction.extractors.pdf.digital_pdf import (
            extract_digital_pdf,
        )

        return extract_digital_pdf(file_path)

    from brd_agent.extraction.extractors.pdf.scanned_pdf import (
        extract_scanned_pdf,
    )

    return extract_scanned_pdf(file_path)


def _email_extractor(file_path: str) -> dict:
    """Run the email extractor without changing its element semantics."""

    from uuid import uuid4

    from brd_agent.extraction.extractors.email.extractor import extract_email

    path = Path(file_path)

    return {
        "document": {
            "document_id": f"doc_{uuid4().hex[:10]}",
            "filename": path.name,
            "file_type": "eml",
        },
        "elements": extract_email(path),
    }


def _get_extractor(extension: str) -> Extractor:
    """
    Return the extractor for a file extension.

    Imports are intentionally lazy so that a missing dependency or extractor
    for one file type does not break unrelated file types.
    """

    if extension in TEXT_FILES:
        from brd_agent.extraction.extractors.text.text_extractor import (
            extract_text,
        )

        return extract_text

    if extension in IMAGE_FILES:
        from brd_agent.extraction.extractors.images.image_extractor import (
            extract_image,
        )

        return extract_image

    if extension in SPREADSHEET_FILES:
        from brd_agent.extraction.extractors.spreadsheet.spreadsheet_extractor import (
            extract_spreadsheet,
        )

        return extract_spreadsheet

    if extension in EMAIL_FILES:
        return _email_extractor

    if extension in HTML_FILES:
        from brd_agent.extraction.extractors.web.html_extractor import (
            extract_html,
        )

        return extract_html

    if extension == ".docx":
        from brd_agent.extraction.extractors.docx.docx_extractor import (
            extract_docx,
        )

        return extract_docx

    if extension == ".pptx":
        from brd_agent.extraction.extractors.pptx.pptx_extractor import (
            extract_pptx,
        )

        return extract_pptx

    if extension == ".pdf":
        return _pdf_extractor

    raise ValueError(
        f"Unsupported file type: {extension or '<none>'}"
    )


def resolve_extraction_route(file_path: str | Path) -> list[str]:
    """Return the ordered extraction path that will be followed for a file."""

    path = Path(file_path).expanduser().resolve()
    extension = path.suffix.lower()
    route = ["gateway", f"extension:{extension or 'none'}"]

    if extension in TEXT_FILES:
        route.extend(["category:text", "extractor:text.extract_text"])
    elif extension in IMAGE_FILES:
        route.extend(["category:image", "extractor:images.extract_image"])
    elif extension in SPREADSHEET_FILES:
        route.extend(
            ["category:spreadsheet", "extractor:spreadsheet.extract_spreadsheet"]
        )
    elif extension in EMAIL_FILES:
        route.extend(["category:email", "extractor:email.extract_email"])
    elif extension in HTML_FILES:
        route.extend(["category:html", "extractor:web.extract_html"])
    elif extension == ".docx":
        route.extend(["category:docx", "extractor:docx.extract_docx"])
    elif extension == ".pptx":
        route.extend(["category:pptx", "extractor:pptx.extract_pptx"])
    elif extension == ".pdf":
        route.append("category:pdf")
        pdf_type = detect_pdf_type(path)
        route.append(f"detect_pdf_type:{pdf_type}")
        if pdf_type == "digital":
            route.append("extractor:pdf.digital_pdf.extract_digital_pdf")
        else:
            route.append("extractor:pdf.scanned_pdf.extract_scanned_pdf")
    else:
        route.append("error:unsupported_file_type")

    return route


def format_extraction_route(route: list[str]) -> str:
    """Format a route list for terminal output."""
    return " -> ".join(route)


def route_file(file_path: str | Path) -> dict:
    """Select and run the correct extractor for one file."""

    path = Path(file_path).expanduser().resolve()

    if not path.is_file():
        raise FileNotFoundError(path)

    extension = path.suffix.lower()
    route = resolve_extraction_route(path)
    route_display = format_extraction_route(route)

    logger.info(
        "EXTRACTION ROUTE | file=%s | path=%s",
        path.name,
        route_display,
    )

    extractor = _get_extractor(extension)
    result = extractor(str(path))

    document = result.get("document")
    if isinstance(document, dict):
        document["extraction_route"] = route

    return result


def extract_file(file_path: str | Path) -> dict:
    """Public alias for extracting a single file."""
    return route_file(file_path)


def extract_path(input_path: str | Path) -> list[dict]:
    """Extract all supported files in deterministic order."""

    path = Path(input_path).expanduser()

    if path.is_dir():
        files = sorted(
            item
            for item in path.rglob("*")
            if item.is_file()
            and item.suffix.lower() in SUPPORTED_FILES
        )
    else:
        files = [path]

    return [extract_file(file_path) for file_path in files]