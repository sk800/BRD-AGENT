"""Schemas for the requirement-discovery stage."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class RequirementItem(BaseModel):
    key: str = Field(
        min_length=1,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Stable machine-readable snake_case identifier.",
    )
    label: str = Field(min_length=1, description="Concise checklist item for the user.")
    rationale: str = Field(
        min_length=1,
        description="Why this information is needed to prepare the BRD.",
    )
    status: str = "missing"

    @field_validator("key", "label", "rationale")
    @classmethod
    def require_non_whitespace_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("must not be blank")
        return normalized


class RequirementChecklist(BaseModel):
    items: list[RequirementItem]


class RequirementDiscoveryResult(BaseModel):
    route: Literal["project", "redirect"] = "project"
    redirect_message: str | None = None
    items: list[RequirementItem] = Field(default_factory=list)


class RequirementEvidenceAssessment(BaseModel):
    key: str
    status: Literal["answered", "missing", "needs_clarification"]
    evidence_summary: str = ""
    clarification_question: str | None = None

    @field_validator("key", "evidence_summary")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("clarification_question")
    @classmethod
    def strip_optional_question(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None
