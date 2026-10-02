from typing import Any

from pydantic import BaseModel, Field


class EnterpriseSourceSpec(BaseModel):
    platform: str = Field(..., description="confluence | servicenow")
    action: str = Field(..., description="e.g. read_page, search, query_records")
    params: dict[str, Any] = Field(default_factory=dict)


class AssembleBrdContextRequest(BaseModel):
    conversation_id: str
    requirement_text: str = Field(
        ...,
        description="Clarified requirement / BRD generation ask (drives vector retrieval query).",
    )
    enterprise_sources: list[EnterpriseSourceSpec] = Field(
        default_factory=list,
        description="Live MCP fetches — not stored in the vector DB.",
    )
    retrieval_top_k: int | None = Field(default=None, ge=1, le=50)


class AssembledContextResponse(BaseModel):
    requirement_text: str
    uploaded_document_chunks: list[dict[str, Any]]
    enterprise_knowledge: list[dict[str, Any]]
    status: str
    context_assembly_status: str | None = None
