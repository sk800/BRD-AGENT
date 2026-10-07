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

    async def search_for_requirement(
        self, requirement_text: str
    ) -> list[dict[str, Any]]:
        """Search configured Confluence content using a safely quoted CQL phrase."""
        async with EnterpriseMCPClient.connect() as client:
            platforms = await client.call_tool("list_enterprise_platforms")
            if not platforms.get("ok"):
                raise RuntimeError(
                    "MCP could not report configured enterprise platforms: "
                    f"{platforms.get('error', 'unknown error')}"
                )
            platform_data = platforms.get("data")
            configured = (
                platform_data.get("confluence", {})
                if isinstance(platform_data, dict)
                else {}
            )
            if not configured.get("configured"):
                return []

            phrase = requirement_text.strip()[:200]
            phrase = phrase.replace("\\", "\\\\").replace('"', '\\"')
            result = await client.call_tool(
                "confluence_search",
                {"cql": f'text ~ "{phrase}"', "limit": 5},
            )
            if not result.get("ok"):
                raise RuntimeError(
                    "Confluence MCP search failed: "
                    f"{result.get('error', 'unknown error')}"
                )
            return [
                {
                    "platform": "confluence",
                    "action": "search",
                    "params": {"query": requirement_text},
                    "result": result,
                }
            ]
