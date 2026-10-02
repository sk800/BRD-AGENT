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
        _log_chunking_results(extraction_state)
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

    _log_chunking_results(extraction_state)
    _log_vector_ingestion_results(extraction_state)
    logger.info("=" * 70)


def _log_chunking_results(ingestion_state: dict) -> None:
    chunking_status = ingestion_state.get("chunking_status")
    if chunking_status is None:
        return

    chunking_method = ingestion_state.get("chunking_method", "unknown")
    chunks = ingestion_state.get("chunks", [])

    logger.info("-" * 70)
    logger.info(
        "CHUNKING | method=%s status=%s chunks=%s",
        chunking_method,
        chunking_status,
        len(chunks),
    )

    for index, chunk in enumerate(chunks, start=1):
        chunk_type = chunk.get("chunk_type", "unknown")
        chunk_id = chunk.get("chunk_id", "n/a")
        text = str(chunk.get("text", ""))
        heading = chunk.get("metadata", {}).get("heading")
        parent_id = chunk.get("parent_id")
        parent_hint = f" parent_id={parent_id}" if parent_id else ""
        standalone = chunk.get("metadata", {}).get("standalone_parent")
        standalone_hint = (
            " standalone_parent=true" if standalone else ""
        )

        logger.info(
            "  %s. [%s%s%s] chunk_id=%s chars=%s heading=%s",
            index,
            chunk_type,
            parent_hint,
            standalone_hint,
            chunk_id,
            len(text),
            heading or "n/a",
        )
        if text:
            logger.info("       --- chunk text start ---")
            for line in text.splitlines():
                logger.info("       %s", line)
            logger.info("       --- chunk text end ---")
        else:
            logger.warning("       TEXT: <empty>")


def _log_vector_ingestion_results(ingestion_state: dict) -> None:
    status = ingestion_state.get("vector_ingestion_status")
    if status is None:
        return

    logger.info("-" * 70)
    logger.info(
        "VECTOR INGESTION | status=%s model=%s pipeline=%s vectors=%s skipped_attachments=%s",
        status,
        ingestion_state.get("embedding_model", "n/a"),
        ingestion_state.get("embedding_pipeline_version", "n/a"),
        ingestion_state.get("vectors_ingested", 0),
        ingestion_state.get("vector_ingestion_skipped_attachments", 0),
    )

    for item in ingestion_state.get("vector_ingestion_results", []):
        logger.info(
            "  attachment=%s status=%s vectors=%s key=%s",
            item.get("attachment_id"),
            item.get("status"),
            item.get("vector_count"),
            item.get("ingestion_key"),
        )


def log_lance_ingestion_rows(rows: list[dict]) -> None:
    """Print LanceDB payload metadata and embedding preview for each vector row."""

    if not rows:
        return

    logger.info("-" * 70)
    logger.info("LANCEDB UPSERT PAYLOAD | rows=%s", len(rows))

    for index, row in enumerate(rows, start=1):
        vector = row.get("vector") or []
        preview_values = [round(float(value), 6) for value in vector[:12]]

        logger.info(
            "  %s. vector_id=%s chunk_id=%s chunk_type=%s parent_id=%s",
            index,
            row.get("vector_id"),
            row.get("chunk_id"),
            row.get("chunk_type"),
            row.get("parent_id"),
        )
        logger.info(
            "       user_id=%s conversation_id=%s message_id=%s attachment_id=%s",
            row.get("user_id"),
            row.get("conversation_id"),
            row.get("message_id"),
            row.get("attachment_id"),
        )
        logger.info(
            "       content_sha256=%s ingestion_key=%s",
            row.get("content_sha256"),
            row.get("ingestion_key"),
        )
        logger.info(
            "       pipeline_version=%s heading=%s section_index=%s",
            row.get("pipeline_version"),
            row.get("heading"),
            row.get("section_index"),
        )
        logger.info("       embedding_dims=%s", len(vector))
        logger.info("       embedding_preview=%s", preview_values)
        logger.info(
            "       embedding_full=%s",
            json.dumps([round(float(value), 6) for value in vector]),
        )

        text = str(row.get("text", ""))
        if text:
            logger.info("       --- lance text start ---")
            for line in text.splitlines():
                logger.info("       %s", line)
            logger.info("       --- lance text end ---")
        else:
            logger.warning("       lance text: <empty>")


def log_lance_ingestion_skipped(
    *,
    attachment_id: str,
    status: str,
    ingestion_key: str | None = None,
    pipeline_version: str | None = None,
    error: str | None = None,
) -> None:
    logger.info("-" * 70)
    logger.info(
        "LANCEDB SKIP | attachment=%s status=%s key=%s pipeline=%s error=%s",
        attachment_id,
        status,
        ingestion_key,
        pipeline_version,
        error,
    )
