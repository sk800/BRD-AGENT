"""Terminal logging for BRD requirement gathering and context assembly."""

from __future__ import annotations

import json
import logging
from typing import Any

from brd_agent.intake.checklist import checklist_to_brd_points

logger = logging.getLogger("brd_agent.requirements")


def _preview(text: str | None, limit: int = 200) -> str:
    if not text:
        return "<empty>"
    normalized = " ".join(str(text).split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."


def log_requirements_workflow(
    *,
    user_id: str,
    conversation_id: str,
    message_id: str | None,
    user_query: str | None,
    chunk_count: int,
    workflow_state: dict[str, Any],
) -> None:
    """Print requirement points and gathered context to the backend terminal."""

    logger.info("=" * 70)
    logger.info(
        "BRD REQUIREMENT GATHERING | user=%s conversation=%s message=%s",
        user_id,
        conversation_id,
        message_id or "n/a",
    )
    logger.info("-" * 70)
    logger.info("USER QUERY: %s", _preview(user_query, 500))
    logger.info("UPLOADED DOCUMENT CHUNKS (ingested): %s", chunk_count)

    route = workflow_state.get("conversation_route", "project")
    checklist_status = workflow_state.get("requirement_checklist_status", "unknown")
    logger.info(
        "REQUIREMENTS NODE | route=%s checklist_status=%s",
        route,
        checklist_status,
    )

    checklist = workflow_state.get("requirement_checklist") or []
    points = workflow_state.get("brd_requirement_points") or checklist_to_brd_points(
        checklist
    )

    logger.info("-" * 70)
    logger.info("BRD REQUIREMENT POINTS (dict) | count=%s", len(points))
    if not points:
        logger.info("  (no requirement points — upload a file or describe the project)")
    else:
        logger.info("%s", json.dumps(points, indent=2, ensure_ascii=False))
        for key, item in points.items():
            logger.info(
                "  • %s | %s | status=%s",
                key,
                item.get("label"),
                item.get("status"),
            )
            rationale = item.get("rationale")
            if rationale:
                logger.info("       rationale: %s", _preview(str(rationale), 300))

    assembled = workflow_state.get("assembled_checklist_context") or []
    assembly_status = workflow_state.get("context_assembly_status")
    if assembled or assembly_status:
        logger.info("-" * 70)
        logger.info(
            "CONTEXT GATHERING (vector DB + Confluence/ServiceNow) | status=%s",
            assembly_status,
        )
        for index, item in enumerate(assembled, start=1):
            key = item.get("key", f"item_{index}")
            logger.info(
                "  %s. [%s] %s | evidence_status=%s",
                index,
                key,
                item.get("label"),
                item.get("status"),
            )
            summary = item.get("evidence_summary")
            if summary:
                logger.info("       evidence_summary: %s", _preview(str(summary), 400))
            question = item.get("clarification_question")
            if question:
                logger.info("       clarification_question: %s", question)

            upload_hits = item.get("uploaded_document_chunks") or []
            logger.info("       lancedb_chunks: %s", len(upload_hits))
            for hit in upload_hits[:3]:
                logger.info(
                    "         - chunk_id=%s heading=%s text=%s",
                    hit.get("chunk_id"),
                    hit.get("heading"),
                    _preview(hit.get("text"), 160),
                )
            if len(upload_hits) > 3:
                logger.info("         ... and %s more chunk(s)", len(upload_hits) - 3)

            enterprise = item.get("enterprise_knowledge") or []
            logger.info("       enterprise_mcp_fetches: %s", len(enterprise))
            for fetch in enterprise[:3]:
                platform = fetch.get("platform")
                action = fetch.get("action")
                result = fetch.get("result") or {}
                ok = result.get("ok")
                logger.info(
                    "         - %s/%s ok=%s preview=%s",
                    platform,
                    action,
                    ok,
                    _preview(json.dumps(result.get("data"), ensure_ascii=False), 120),
                )

    assistant = workflow_state.get("assistant_message")
    if assistant:
        logger.info("-" * 70)
        logger.info("CLARIFICATION / ASSISTANT MESSAGE:")
        for line in str(assistant).splitlines():
            logger.info("  %s", line)

    logger.info("=" * 70)
