import json
import logging
from pathlib import Path

from brd_agent.extraction.gateway.gateway import (
    format_extraction_route,
    resolve_extraction_route,
)

logger = logging.getLogger("brd_agent.extraction")


def log_extraction_results(
    *,
    message_id: str,
    conversation_id: str,
    user_id: str,
    extraction_state: dict,
) -> None:
    """Print extracted document data to the backend terminal."""
    status = extraction_state.get("extraction_status", "unknown")
    extracted_documents = extraction_state.get("extracted_documents", [])
    extraction_errors = extraction_state.get("extraction_errors", [])

    logger.info("=" * 70)
    logger.info(
        "DOCUMENT EXTRACTION | user=%s conversation=%s message=%s status=%s",
        user_id,
        conversation_id,
        message_id,
        status,
    )

    if not extracted_documents and not extraction_errors:
        logger.info("No files to extract.")
        logger.info("=" * 70)
        return

    for item in extracted_documents:
        filename = item.get("original_filename", "unknown")
        extraction = item.get("extraction", {})
        document = extraction.get("document", {})
        elements = extraction.get("elements", [])

        logger.info("-" * 70)
        logger.info("FILE: %s", filename)
        route = document.get("extraction_route")
        if not route:
            storage_path = item.get("storage_path")
            if storage_path and Path(storage_path).is_file():
                route = resolve_extraction_route(storage_path)
        if route:
            logger.info("ROUTE: %s", format_extraction_route(route))
        logger.info(
            "TYPE: %s | DOCUMENT_ID: %s",
            document.get("file_type", "unknown"),
            document.get("document_id", "n/a"),
        )
        logger.info("ELEMENTS (%s):", len(elements))

        for index, element in enumerate(elements, start=1):
            element_type = element.get("type", "unknown")
            content = element.get("content", "")

            if element_type == "figure" and isinstance(content, dict):
                logger.info(
                    "  %s. [%s] image_path=%s",
                    index,
                    element_type,
                    content.get("image_path", "n/a"),
                )
                ocr_engine = content.get("ocr_engine")
                if ocr_engine:
                    logger.info("       OCR_ENGINE: %s", ocr_engine)
                ocr_text = content.get("ocr_text", "")
                if ocr_text:
                    logger.info("       OCR_TEXT: %s", ocr_text[:1000])
                else:
                    logger.warning("       OCR_TEXT: <empty>")
                ocr_warning = content.get("ocr_warning")
                if ocr_warning:
                    logger.warning("       OCR_WARNING: %s", ocr_warning)
                continue

            if isinstance(content, dict):
                content_preview = json.dumps(content, ensure_ascii=False)[:500]
            else:
                content_preview = str(content).replace("\n", " ")[:500]
            logger.info("  %s. [%s] %s", index, element_type, content_preview)

    for error in extraction_errors:
        filename = error.get("original_filename", "unknown")
        storage_path = error.get("storage_path")
        if storage_path and Path(storage_path).is_file():
            route = resolve_extraction_route(storage_path)
            logger.error(
                "EXTRACTION FAILED | file=%s | route=%s | error=%s",
                filename,
                format_extraction_route(route),
                error.get("error", "unknown error"),
            )
        else:
            logger.error(
                "EXTRACTION FAILED | file=%s | error=%s",
                filename,
                error.get("error", "unknown error"),
            )

    logger.info("=" * 70)
