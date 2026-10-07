from typing import Any

from brd_agent.agents.state import AgentState
from brd_agent.orchestration.context_assembly_service import (
    ContentAssemblyService,
    EnterpriseSourceRequest,
)


async def context_assembly_node(state: AgentState) -> dict[str, Any]:
    """Retrieve and assess context for a checklist or a single requirement."""

    raw_sources = state.get("enterprise_sources") or []

    invalid_sources = [
        index
        for index, item in enumerate(raw_sources)
        if not str(item.get("platform", "")).strip()
        or not str(item.get("action", "")).strip()
    ]
    if invalid_sources:
        raise ValueError(
            "Each enterprise source must include platform and action; "
            f"invalid entries at indexes: {invalid_sources}"
        )

    enterprise_sources = [
        EnterpriseSourceRequest(
            platform=item["platform"],
            action=item["action"],
            params=item.get("params") or {},
        )
        for item in raw_sources
    ]

    service = ContentAssemblyService()
    checklist = state.get("requirement_checklist") or []
    if checklist:
        assembled = await service.assemble_for_checklist(
            user_id=state.get("user_id", ""),
            conversation_id=state.get("conversation_id", ""),
            checklist=checklist,
            conversation=(state.get("conversation_history") or [])
            + (
                [{"role": "user", "text": state.get("current_user_text") or ""}]
                if state.get("current_user_text")
                else []
            ),
            enterprise_sources=enterprise_sources,
            retrieval_top_k=state.get("retrieval_top_k"),
        )
        open_questions = [
            item["clarification_question"]
            for item in assembled["items"]
            if item.get("clarification_question")
        ]
        if open_questions:
            assistant_message = (
                "I checked the project details and available sources. To complete "
                "the BRD checklist, could you clarify:\n"
                + "\n".join(f"- {question}" for question in open_questions)
            )
        else:
            assistant_message = (
                "I checked the project details and available sources. The current "
                "BRD checklist is supported by the information collected so far."
            )
        checklist_summary = [
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
            for item in assembled["items"]
        ]
        return {
            "assembled_context": assembled,
            "requirement_checklist": checklist_summary,
            "assembled_checklist_context": assembled["items"],
            "context_assembly_status": assembled["status"],
            "assistant_message": assistant_message,
            "current_stage": "context_assembly",
        }

    requirement = (state.get("requirement_text") or "").strip()
    if not requirement:
        has_project_input = bool(
            (state.get("current_user_text") or "").strip()
            or state.get("chunks")
            or state.get("prior_checklist")
        )
        return {
            "assembled_context": {
                "items": [],
                "status": "complete" if has_project_input else "empty",
            },
            "assembled_checklist_context": [],
            "context_assembly_status": "assembled" if has_project_input else "skipped",
            "assistant_message": (
                "The details provided cover the information currently needed "
                "for the BRD checklist."
                if has_project_input
                else "Tell me a little about the project you want to document."
            ),
            "current_stage": "context_assembly",
        }
    assembled = await service.assemble_for_requirement(
        user_id=state.get("user_id", ""),
        conversation_id=state.get("conversation_id", ""),
        requirement_text=requirement,
        enterprise_sources=enterprise_sources,
        retrieval_top_k=state.get("retrieval_top_k"),
    )

    return {
        "assembled_context": assembled.to_dict(),
        "context_assembly_status": assembled.status,
        "current_stage": "context_assembly",
    }
