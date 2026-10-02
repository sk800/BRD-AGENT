from typing import Any

from pydantic import BaseModel, Field


class MCPInvokeRequest(BaseModel):
    tool_name: str = Field(..., min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)


class PlatformFetchRequest(BaseModel):
    platform: str = Field(..., description="confluence | servicenow")
    action: str = Field(..., description="e.g. read_page, search, get_record")
    params: dict[str, Any] = Field(default_factory=dict)


class MCPToolInfo(BaseModel):
    name: str
    title: str | None = None
    description: str | None = None


class MCPListToolsResponse(BaseModel):
    tools: list[MCPToolInfo]


class MCPInvokeResponse(BaseModel):
    result: dict[str, Any]
