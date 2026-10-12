import logging

from brd_agent.core.logging.requirement_logger import log_requirements_workflow


def test_log_requirements_workflow_emits_points_dict(caplog):
    caplog.set_level(logging.INFO, logger="brd_agent.requirements")

    log_requirements_workflow(
        user_id="u1",
        conversation_id="c1",
        message_id="m1",
        user_query="Build a cafe website",
        chunk_count=3,
        workflow_state={
            "conversation_route": "project",
            "requirement_checklist_status": "ready",
            "requirement_checklist": [
                {
                    "key": "visitor_actions",
                    "label": "What visitors should do",
                    "rationale": "Defines the site journey.",
                    "status": "missing",
                }
            ],
            "brd_requirement_points": {
                "visitor_actions": {
                    "label": "What visitors should do",
                    "rationale": "Defines the site journey.",
                    "status": "missing",
                }
            },
            "assembled_checklist_context": [],
            "context_assembly_status": "assembled",
        },
    )

    text = caplog.text
    assert "BRD REQUIREMENT GATHERING" in text
    assert "BRD REQUIREMENT POINTS (dict)" in text
    assert "visitor_actions" in text
