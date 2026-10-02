"""MCP server exposing enterprise knowledge tools (Confluence, ServiceNow)."""

from __future__ import annotations

import json
import traceback
from typing import Any

from mcp.server.mcpserver import MCPServer

from brd_agent.knowledge.connectors.confluence import ConfluenceClient
from brd_agent.knowledge.connectors.servicenow import (
    ServiceNowClient,
    parse_fields_json,
)

_server: MCPServer | None = None


def _ok(data: Any) -> str:
    return json.dumps({"ok": True, "data": data}, ensure_ascii=False)


def _err(message: str, *, detail: str | None = None) -> str:
    payload: dict[str, Any] = {"ok": False, "error": message}
    if detail:
        payload["detail"] = detail
    return json.dumps(payload, ensure_ascii=False)


def _handle(exc: Exception) -> str:
    return _err(str(exc), detail=traceback.format_exc())


def build_enterprise_mcp_server() -> MCPServer:
    global _server
    if _server is not None:
        return _server

    mcp = MCPServer(
        "brd-enterprise-knowledge",
        instructions=(
            "Tools to read and write enterprise knowledge from Confluence and ServiceNow. "
            "Results are fetched live for BRD context assembly; they are not embedded into "
            "the upload vector database. Configure credentials via environment variables."
        ),
    )

    @mcp.tool(
        title="List configured platforms",
        description="Returns which enterprise platforms have credentials configured.",
    )
    async def list_enterprise_platforms() -> str:
        confluence = ConfluenceClient()
        servicenow = ServiceNowClient()
        return _ok(
            {
                "confluence": {"configured": confluence.is_configured()},
                "servicenow": {"configured": servicenow.is_configured()},
            }
        )

    @mcp.tool(description="Read a Confluence page by ID.")
    async def confluence_read_page(page_id: str) -> str:
        try:
            data = await ConfluenceClient().read_page(page_id)
            return _ok(data)
        except Exception as exc:  # noqa: BLE001 — surface to MCP caller as JSON
            return _handle(exc)

    @mcp.tool(description="Search Confluence content with CQL.")
    async def confluence_search(cql: str, limit: int = 10) -> str:
        try:
            data = await ConfluenceClient().search(cql=cql, limit=limit)
            return _ok(data)
        except Exception as exc:  # noqa: BLE001
            return _handle(exc)

    @mcp.tool(description="Create a Confluence page in a space.")
    async def confluence_create_page(
        space_key: str,
        title: str,
        body: str,
        parent_id: str | None = None,
    ) -> str:
        try:
            data = await ConfluenceClient().create_page(
                space_key=space_key,
                title=title,
                body=body,
                parent_id=parent_id,
            )
            return _ok(data)
        except Exception as exc:  # noqa: BLE001
            return _handle(exc)

    @mcp.tool(description="Update an existing Confluence page (provide current version).")
    async def confluence_update_page(
        page_id: str,
        title: str,
        body: str,
        version: int,
    ) -> str:
        try:
            data = await ConfluenceClient().update_page(
                page_id=page_id,
                title=title,
                body=body,
                version=version,
            )
            return _ok(data)
        except Exception as exc:  # noqa: BLE001
            return _handle(exc)

    @mcp.tool(description="Fetch a single ServiceNow record by table and sys_id.")
    async def servicenow_get_record(table: str, sys_id: str) -> str:
        try:
            data = await ServiceNowClient().get_record(table, sys_id)
            return _ok(data)
        except Exception as exc:  # noqa: BLE001
            return _handle(exc)

    @mcp.tool(description="Query ServiceNow table records (sysparm_query syntax).")
    async def servicenow_query_records(
        table: str, query: str = "", limit: int = 10
    ) -> str:
        try:
            data = await ServiceNowClient().query_records(
                table=table, query=query, limit=limit
            )
            return _ok(data)
        except Exception as exc:  # noqa: BLE001
            return _handle(exc)

    @mcp.tool(description="Create a ServiceNow record; fields_json is a JSON object string.")
    async def servicenow_create_record(table: str, fields_json: str) -> str:
        try:
            fields = parse_fields_json(fields_json)
            data = await ServiceNowClient().create_record(table, fields)
            return _ok(data)
        except Exception as exc:  # noqa: BLE001
            return _handle(exc)

    @mcp.tool(description="Update a ServiceNow record; fields_json is a JSON object string.")
    async def servicenow_update_record(
        table: str, sys_id: str, fields_json: str
    ) -> str:
        try:
            fields = parse_fields_json(fields_json)
            data = await ServiceNowClient().update_record(table, sys_id, fields)
            return _ok(data)
        except Exception as exc:  # noqa: BLE001
            return _handle(exc)

    _server = mcp
    return mcp
