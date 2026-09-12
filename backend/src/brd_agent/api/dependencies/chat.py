from typing import Annotated

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from brd_agent.core.database import get_database
from brd_agent.services.chat_service import ChatService


async def get_chat_service(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> ChatService:
    return ChatService(db)
