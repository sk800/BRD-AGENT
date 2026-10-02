"""Live enterprise knowledge via MCP (Confluence, ServiceNow).

Used at BRD generation time by content assembly — not ingested into LanceDB.
Uploads alone go through the ingestion graph → vector store.
"""

from __future__ import annotations

from typing import Any

from brd_agent.knowledge.mcp.client import EnterpriseMCPClient

# Maps (platform, action) to MCP tool name for agent-friendly fetch API.
_PLATFORM_ACTION_TOOLS: dict[tuple[str, str], str] = {
    ("confluence", "read_page"): "confluence_read_page",
    ("confluence", "search"): "confluence_search",
    ("confluence", "create_page"): "confluence_create_page",
    ("confluence", "update_page"): "confluence_update_page",
    ("servicenow", "get_record"): "servicenow_get_record",
    ("servicenow", "query_records"): "servicenow_query_records",
    ("servicenow", "create_record"): "servicenow_create_record",
    ("servicenow", "update_record"): "servicenow_update_record",
}


class EnterpriseKnowledgeService:
    async def list_mcp_tools(self) -> list[dict[str, Any]]:
        async with EnterpriseMCPClient.connect() as client:
            return await client.list_tools()

    async def invoke_mcp_tool(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        async with EnterpriseMCPClient.connect() as client:
            return await client.call_tool(tool_name, arguments)

    async def fetch_from_platform(
        self,
        platform: str,
        action: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        key = (platform.strip().lower(), action.strip().lower())
        tool_name = _PLATFORM_ACTION_TOOLS.get(key)
        if tool_name is None:
            return {
                "ok": False,
                "error": f"Unknown platform/action: {platform}/{action}",
                "supported": [
                    f"{p}/{a}" for p, a in sorted(_PLATFORM_ACTION_TOOLS.keys())
                ],
            }
        async with EnterpriseMCPClient.connect() as client:
            return await client.call_tool(tool_name, params or {})
