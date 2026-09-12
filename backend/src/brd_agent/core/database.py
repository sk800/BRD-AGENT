from __future__ import annotations

from collections.abc import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from brd_agent.core.config import get_settings

settings = get_settings()

_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_url)
    return _client


def get_mongo_database() -> AsyncIOMotorDatabase:
    return get_mongo_client()[settings.mongodb_db_name]


async def get_database() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    yield get_mongo_database()


async def init_db() -> None:
    db = get_mongo_database()
    await db.users.create_index("email", unique=True)
    await db.conversations.create_index([("user_id", 1), ("updated_at", -1)])
    await db.messages.create_index([("conversation_id", 1), ("created_at", 1)])
    await db.messages.create_index([("user_id", 1), ("conversation_id", 1)])


async def close_db() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
