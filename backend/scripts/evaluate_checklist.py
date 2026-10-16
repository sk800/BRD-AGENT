"""Run a small, human-reviewable Azure checklist evaluation on synthetic cases."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT / "src"))

from brd_agent.core.config import get_settings  # noqa: E402
from brd_agent.intake.services.requirement_discovery_service import (  # noqa: E402
    RequirementDiscoveryService,
)


@dataclass(frozen=True)
class EvaluationCase:
    name: str
    project_context: str
    expected_gaps: dict[str, tuple[str, ...]]
    already_answered: dict[str, tuple[str, ...]]


CASES = (
    EvaluationCase(
        name="small_cafe_website",
        project_context=(
            "I need a website for my neighborhood cafe. Visitors should be able "
            "to see our menu, opening hours, and location. Customers should be "
            "able to reserve tables online. We do not want online payments."
        ),
        expected_gaps={
            "booking_policy": ("booking", "reservation", "reserve"),
            "booking_changes": ("cancel", "change", "modify"),
            "party_size_or_capacity": ("party size", "guest", "capacity", "group"),
        },
        already_answered={
            "online_payments": ("payment", "checkout", "transaction", "billing"),
            "menu": ("menu", "food", "drink"),
            "opening_hours": ("hours", "opening", "schedule"),
            "location": ("location", "address", "map"),
        },
    ),
    EvaluationCase(
        name="well_specified_portfolio",
        project_context=(
            "Build a simple portfolio website for an independent photographer. "
            "The audience is prospective clients. Include a bio, categorized "
            "photo gallery, and contact page. The contact form sends to the "
            "photographer's existing email. There are no user accounts, payments, "
            "online bookings, or admin panel. The photographer will update photos "
            "by replacing the gallery files; launch on the existing domain."
        ),
        expected_gaps={},
        already_answered={
            "audience": ("audience", "user", "client", "visitor"),
            "pages_or_content": ("page", "bio", "gallery", "contact", "portfolio"),
            "contact_handling": ("contact", "email", "message", "form"),
            "payments": ("payment", "checkout", "billing"),
            "accounts": ("account", "login", "authentication"),
            "hosting_or_domain": ("hosting", "domain", "deployment", "server"),
        },
    ),
    EvaluationCase(
        name="multi_site_employee_services",
        project_context=(
            "We are planning an employee self-service system for 1,800 staff at "
            "three factories and one head office. Phase one includes leave "
            "requests, expense claims, and attendance corrections. Managers "
            "approve requests, then HR handles exceptions; approvals must never "
            "happen automatically. Employees use SAP HCM as the master record, "
            "synced nightly. Claims need receipts and duplicate detection. "
            "Payroll receives monthly leave balances. The system must work on "
            "older phones and keep an audit history. We have not decided whether "
            "different plant or union policies need separate rules, how exceptions "
            "should be escalated, or what success measures to use."
        ),
        expected_gaps={
            "policy_variations": ("union", "plant policy", "policy difference", "location rule"),
            "exception_escalation": ("escalat", "exception", "override", "appeal"),
            "success_measures": ("success", "measure", "target", "acceptance", "outcome"),
        },
        already_answered={
            "employee_audience": ("employee", "staff", "worker"),
            "initial_scope": ("leave", "expense", "attendance"),
            "approval_flow": ("approv", "manager", "hr"),
            "automatic_approval": ("auto approv", "automatic approv"),
            "master_data_integration": ("sap", "master data", "nightly"),
            "payroll_integration": ("payroll", "monthly"),
            "receipt_and_duplicate_rules": ("receipt", "duplicate"),
            "older_phone_support": ("phone", "mobile"),
            "audit_history": ("audit", "history", "record"),
        },
    ),
)


def _mentions(text: str, phrases: tuple[str, ...]) -> bool:
    normalized = re.sub(r"\s+", " ", text.casefold())
    return any(phrase.casefold() in normalized for phrase in phrases)


def _score_case(
    case: EvaluationCase,
    result: dict[str, Any],
) -> dict[str, Any]:
    items = result["items"]
    labels = "\n".join(
        f"{item['label']}: {item['rationale']}" for item in items
    )
    covered = [
        topic
        for topic, phrases in case.expected_gaps.items()
        if _mentions(labels, phrases)
    ]
    unnecessary = [
        topic
        for topic, phrases in case.already_answered.items()
        if _mentions(labels, phrases)
    ]
    normalized_labels = [
        re.sub(r"[^a-z0-9]+", " ", item["label"].casefold()).strip()
        for item in items
    ]
    duplicate_labels = sorted(
        {
            label
            for label in normalized_labels
            if normalized_labels.count(label) > 1
        }
    )
    return {
        "checklist": result,
        "heuristic_expected_gaps_covered": covered,
        "heuristic_expected_gaps_missed": [
            topic for topic in case.expected_gaps if topic not in covered
        ],
        "heuristic_questions_on_answered_topics": unnecessary,
        "exact_duplicate_labels": duplicate_labels,
        "human_review_required": [
            "Does each question address a real, important information gap?",
            "Are multiple questions redundant or asking for excessive detail?",
            "Did the checklist avoid asking for facts already provided?",
            "Did it invent a requirement, feature, or project decision?",
            "Is the checklist short and understandable for this project?",
        ],
    }


async def _run(output_path: Path | None) -> int:
    settings = get_settings()
    if not (
        settings.azure_openai_endpoint
        and settings.azure_openai_api_key
        and settings.azure_openai_deployment
    ):
        print(
            "Azure OpenAI is not configured. Set "
            "AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, and "
            "AZURE_OPENAI_DEPLOYMENT in backend/.env.",
            file=sys.stderr,
        )
        return 2

    service = RequirementDiscoveryService()
    report: dict[str, Any] = {
        "evaluation": "BRD checklist discovery; synthetic inputs only",
        "cases": [],
    }
    for case in CASES:
        result = await service.discover_result(case.project_context)
        report["cases"].append(
            {
                "name": case.name,
                "expected_gap_topics": list(case.expected_gaps),
                "already_answered_topics": list(case.already_answered),
                **_score_case(case, result),
            }
        )

    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
        print(f"Saved checklist evaluation to {output_path}")
    else:
        print(rendered)
    print(
        "\nThe topic matches are heuristic hints, not an automatic quality score. "
        "Review each checklist and mark the human-review questions."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON report path; otherwise print the report to stdout.",
    )
    args = parser.parse_args()
    try:
        return asyncio.run(_run(args.output))
    except Exception as exc:
        print(f"Checklist evaluation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
