"""Run the enterprise knowledge MCP server over stdio (for agents and IDEs)."""

from brd_agent.knowledge.mcp.server import build_enterprise_mcp_server


def main() -> None:
    build_enterprise_mcp_server().run(transport="stdio")


if __name__ == "__main__":
    main()
