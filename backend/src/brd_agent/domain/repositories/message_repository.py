import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

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

    async def update_ingestion_results(
        self,
        message_id: str,
        user_id: str,
        *,
        extracted_documents: list[dict],
        extraction_errors: list[dict],
        extraction_status: str,
        chunking_method: str | None,
        chunking_status: str | None,
        chunks: list[dict],
        vector_ingestion_status: str | None = None,
        vectors_ingested: int | None = None,
        vector_ingestion_skipped_attachments: int | None = None,
        vector_ingestion_results: list[dict] | None = None,
        embedding_model: str | None = None,
        embedding_pipeline_version: str | None = None,
    ) -> MessageInDB | None:
        result = await self._collection.find_one_and_update(
            {"_id": message_id, "user_id": user_id},
            {
                "$set": {
                    "extracted_documents": extracted_documents,
                    "extraction_errors": extraction_errors,
                    "extraction_status": extraction_status,
                    "chunking_method": chunking_method,
                    "chunking_status": chunking_status,
                    "chunks": chunks,
                    "vector_ingestion_status": vector_ingestion_status,
                    "vectors_ingested": vectors_ingested,
                    "vector_ingestion_skipped_attachments": (
                        vector_ingestion_skipped_attachments
                    ),
                    "vector_ingestion_results": vector_ingestion_results or [],
                    "embedding_model": embedding_model,
                    "embedding_pipeline_version": embedding_pipeline_version,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        if result is None:
            return None
        return MessageInDB.model_validate(result)

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
