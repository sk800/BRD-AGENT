"""MCP client for the BRD enterprise knowledge server."""

from __future__ import annotations

import json
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator

from mcp import Client
from mcp.client.stdio import StdioServerParameters
from mcp_types import CallToolResult, TextContent

from brd_agent.core.config import get_settings
from brd_agent.knowledge.mcp.server import build_enterprise_mcp_server


def call_tool_result_text(result: CallToolResult) -> str:
    parts: list[str] = []
    for block in result.content:
        if isinstance(block, TextContent):
            parts.append(block.text)
        elif hasattr(block, "text"):
            parts.append(str(block.text))
    return "\n".join(parts)


def parse_tool_json(result: CallToolResult) -> dict[str, Any]:
    text = call_tool_result_text(result).strip()
    if not text:
        return {"ok": False, "error": "Empty tool response"}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {"ok": True, "raw": text}
    if isinstance(payload, dict):
        return payload
    return {"ok": True, "data": payload}


@dataclass
class EnterpriseMCPClient:
    """Connects to the enterprise MCP server (in-process or stdio subprocess)."""

    _client: Client

    @classmethod
    def _server_target(cls) -> Any:
        settings = get_settings()
        if settings.mcp_enterprise_use_inprocess:
            return build_enterprise_mcp_server()
        command = settings.mcp_enterprise_server_command or sys.executable
        args = settings.mcp_enterprise_server_args
        if not args:
            args = ["-m", "brd_agent.knowledge.mcp"]
        return StdioServerParameters(command=command, args=args)

    @classmethod
    @asynccontextmanager
    async def connect(cls) -> AsyncIterator[EnterpriseMCPClient]:
        async with Client(cls._server_target()) as client:
            yield cls(_client=client)

    async def list_tools(self) -> list[dict[str, Any]]:
        result = await self._client.list_tools()
        tools: list[dict[str, Any]] = []
        for tool in result.tools:
            tools.append(
                {
                    "name": tool.name,
                    "title": tool.title,
                    "description": tool.description,
                }
            )
        return tools

    async def call_tool(
        self, name: str, arguments: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        result = await self._client.call_tool(name, arguments or {})
        return parse_tool_json(result)
