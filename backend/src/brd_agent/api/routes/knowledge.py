from fastapi import APIRouter, Depends

from brd_agent.api.dependencies.auth import get_current_user
from brd_agent.api.schemas.knowledge import (
    MCPInvokeRequest,
    MCPInvokeResponse,
    MCPListToolsResponse,
    MCPToolInfo,
    PlatformFetchRequest,
)
from brd_agent.domain.models.user import UserPublic
from brd_agent.services.enterprise_knowledge_service import EnterpriseKnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/mcp/tools", response_model=MCPListToolsResponse)
async def list_mcp_tools(
    _: UserPublic = Depends(get_current_user),
) -> MCPListToolsResponse:
    service = EnterpriseKnowledgeService()
    tools = await service.list_mcp_tools()
    return MCPListToolsResponse(
        tools=[MCPToolInfo(**item) for item in tools],
    )


@router.post("/mcp/invoke", response_model=MCPInvokeResponse)
async def invoke_mcp_tool(
    body: MCPInvokeRequest,
    _: UserPublic = Depends(get_current_user),
) -> MCPInvokeResponse:
    service = EnterpriseKnowledgeService()
    result = await service.invoke_mcp_tool(body.tool_name, body.arguments)
    return MCPInvokeResponse(result=result)


@router.post("/fetch", response_model=MCPInvokeResponse)
async def fetch_from_platform(
    body: PlatformFetchRequest,
    _: UserPublic = Depends(get_current_user),
) -> MCPInvokeResponse:
    service = EnterpriseKnowledgeService()
    result = await service.fetch_from_platform(
        body.platform, body.action, body.params
    )
    return MCPInvokeResponse(result=result)
