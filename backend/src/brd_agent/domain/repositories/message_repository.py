import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase

from brd_agent.domain.models.chat import AttachmentInDB, MessageInDB, build_message_document


class MessageRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db.messages

    async def create(
        self,
        conversation_id: str,
        user_id: str,
        text: str | None,
        attachments: list[AttachmentInDB],
    ) -> MessageInDB:
        message_id = str(uuid.uuid4())
        attachment_docs = [attachment.model_dump() for attachment in attachments]
        document = build_message_document(
            message_id=message_id,
            conversation_id=conversation_id,
            user_id=user_id,
            text=text,
            attachments=attachment_docs,
        )
        await self._collection.insert_one(document)
        return MessageInDB.model_validate(document)

    async def list_by_conversation(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 100,
    ) -> list[MessageInDB]:
        cursor = (
            self._collection.find({"conversation_id": conversation_id, "user_id": user_id})
            .sort("created_at", 1)
            .limit(limit)
        )
        documents = await cursor.to_list(length=limit)
        return [MessageInDB.model_validate(doc) for doc in documents]
