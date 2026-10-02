import pytest

from brd_agent.knowledge.connectors.servicenow import parse_fields_json
from brd_agent.knowledge.mcp.client import EnterpriseMCPClient
from brd_agent.knowledge.mcp.server import build_enterprise_mcp_server


@pytest.mark.asyncio
async def test_mcp_lists_enterprise_tools():
    async with EnterpriseMCPClient.connect() as client:
        tools = await client.list_tools()
    names = {t["name"] for t in tools}
    assert "confluence_read_page" in names
    assert "servicenow_query_records" in names
    assert "list_enterprise_platforms" in names


@pytest.mark.asyncio
async def test_list_platforms_reports_unconfigured_by_default():
    async with EnterpriseMCPClient.connect() as client:
        result = await client.call_tool("list_enterprise_platforms", {})
    assert result["ok"] is True
    assert result["data"]["confluence"]["configured"] is False
    assert result["data"]["servicenow"]["configured"] is False


@pytest.mark.asyncio
async def test_confluence_read_page_via_mcp_with_mocked_http(monkeypatch):
    async def fake_read_page(self, page_id: str):
        return {
            "id": page_id,
            "title": "BRD Draft",
            "body_text": "Requirements overview",
        }

    monkeypatch.setattr(
        "brd_agent.knowledge.mcp.server.ConfluenceClient.read_page",
        fake_read_page,
    )
    async with EnterpriseMCPClient.connect() as client:
        result = await client.call_tool(
            "confluence_read_page", {"page_id": "12345"}
        )
    assert result["ok"] is True
    assert result["data"]["title"] == "BRD Draft"


def test_parse_fields_json_rejects_invalid():
    with pytest.raises(ValueError):
        parse_fields_json("not-json")


def test_build_server_is_singleton():
    a = build_enterprise_mcp_server()
    b = build_enterprise_mcp_server()
    assert a is b
