from typing import Any

from brd_agent.agents.state import AgentState
from brd_agent.memory.service import ProjectMemoryService


async def project_memory_read_node(state: AgentState) -> dict[str, Any]:
    user_id = state.get("user_id", "")
    conversation_id = state.get("conversation_id", "")
    if not user_id or not conversation_id:
        return {"memory_context": []}
    memories = await ProjectMemoryService().load_context(
        user_id=user_id,
        conversation_id=conversation_id,
    )
    return {"memory_context": memories}


async def project_memory_update_node(state: AgentState) -> dict[str, Any]:
    user_text = (state.get("current_user_text") or "").strip()
    user_id = state.get("user_id", "")
    conversation_id = state.get("conversation_id", "")
    if not user_text or not user_id or not conversation_id:
        return {"current_stage": "memory"}
    await ProjectMemoryService().remember_turn(
        user_id=user_id,
        conversation_id=conversation_id,
        user_text=user_text,
        assistant_text=state.get("assistant_message", ""),
    )
    return {"current_stage": "memory"}
