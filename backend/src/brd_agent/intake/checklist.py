"""Helpers for BRD requirement checklists."""

from __future__ import annotations

from typing import Any


def checklist_to_brd_points(checklist: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Map stable keys to the information needed to build the BRD."""

    points: dict[str, dict[str, Any]] = {}
    for item in checklist:
        key = str(item.get("key", "")).strip()
        if not key:
            continue
        points[key] = {
            "label": item.get("label"),
            "rationale": item.get("rationale"),
            "status": item.get("status", "missing"),
            "evidence_summary": item.get("evidence_summary"),
            "clarification_question": item.get("clarification_question"),
        }
    return points
