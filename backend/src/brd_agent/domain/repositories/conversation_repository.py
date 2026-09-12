import uuid
from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from brd_agent.domain.models.chat import ConversationInDB, build_conversation_document


class ConversationRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db.conversations

    async def create(self, user_id: str, title: str) -> ConversationInDB:
        conversation_id = str(uuid.uuid4())
        document = build_conversation_document(conversation_id, user_id, title)
        await self._collection.insert_one(document)
        return ConversationInDB.model_validate(document)

    async def get_by_id(self, conversation_id: str, user_id: str) -> ConversationInDB | None:
        document = await self._collection.find_one(
            {"_id": conversation_id, "user_id": user_id},
        )
        if document is None:
            return None
        return ConversationInDB.model_validate(document)

    async def list_by_user(self, user_id: str, limit: int = 50) -> list[ConversationInDB]:
        cursor = self._collection.find({"user_id": user_id}).sort("updated_at", -1).limit(limit)
        documents = await cursor.to_list(length=limit)
        return [ConversationInDB.model_validate(doc) for doc in documents]

    async def touch(self, conversation_id: str) -> None:
        await self._collection.update_one(
            {"_id": conversation_id},
            {"$set": {"updated_at": datetime.now(UTC)}},
        )
