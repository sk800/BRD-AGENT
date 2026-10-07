"""LangGraph node for project-specific requirements discovery."""

from typing import Any

from brd_agent.agents.state import AgentState
from brd_agent.intake.services.requirement_discovery_service import (
    RequirementDiscoveryService,
)


async def requirements_node(
    state: AgentState,
    *,
    discovery_service: RequirementDiscoveryService | None = None,
) -> dict[str, Any]:
    request = (state.get("current_user_text") or state.get("requirement_text") or "").strip()
    history = state.get("conversation_history") or []
    prior_checklist = state.get("prior_checklist") or []
    memory_context = state.get("memory_context") or []
    history_text = "\n".join(
        f"{turn.get('role', 'unknown')}: {turn.get('text', '').strip()[:1500]}"
        for turn in history[-12:]
        if turn.get("text", "").strip()
    )
    document_sections: list[str] = []
    remaining_document_chars = 18_000
    for chunk in state.get("chunks") or []:
        text = str(chunk.get("text", "")).strip()
        if not text or remaining_document_chars <= 0:
            continue
        excerpt = text[: min(2_000, remaining_document_chars)]
        document_sections.append(excerpt)
        remaining_document_chars -= len(excerpt)
    document_context = "\n\n".join(document_sections)
    if not request and not document_context:
        return {
            "requirement_checklist": [],
            "requirement_checklist_status": "skipped",
            "current_stage": "requirements",
        }

    sections = []
    if history_text:
        sections.append(f"Conversation history:\n{history_text}")
    if request:
        sections.append(f"Current user request:\n{request}")
    elif document_context:
        sections.append(
            "Current user request:\nInfer the project requirements from these files."
        )
    if document_context:
        sections.append(f"Uploaded document context:\n{document_context}")
    if prior_checklist:
        checklist_context = [
            {
                key: item.get(key)
                for key in (
                    "key",
                    "label",
                    "rationale",
                    "status",
                    "evidence_summary",
                    "clarification_question",
                )
                if item.get(key) is not None
            }
            for item in prior_checklist
        ]
        sections.append(
            "Existing BRD checklist and earlier evidence:\n"
            f"{checklist_context}"
        )
    if memory_context:
        memory_text = "\n".join(str(memory)[:800] for memory in memory_context[:15])
        sections.append(f"Relevant project memories:\n{memory_text}")

    service = discovery_service or RequirementDiscoveryService()
    discovery = await service.discover_result("\n\n".join(sections))
    if discovery["route"] == "redirect":
        return {
            "requirement_checklist": prior_checklist,
            "requirement_checklist_status": "unchanged",
            "conversation_route": "redirect",
            "assistant_message": discovery["redirect_message"],
            "current_stage": "requirements",
        }

    merged: dict[str, dict[str, Any]] = {}
    for item in prior_checklist + discovery["items"]:
        key = str(item["key"])
        merged[key] = {**item, "status": "missing"}
    checklist = list(merged.values())
    return {
        "requirement_checklist": checklist,
        "requirement_checklist_status": "ready",
        "conversation_route": "project",
        "current_stage": "requirements",
    }
