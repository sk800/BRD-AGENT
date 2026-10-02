from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase


class VectorIngestionRepository:
    """Tracks completed vector ingestions to skip duplicate file processing."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db.vector_ingestions

    async def find_by_key(self, ingestion_key: str) -> dict | None:
        return await self._collection.find_one({"_id": ingestion_key})

    async def register(
        self,
        *,
        ingestion_key: str,
        user_id: str,
        content_sha256: str,
        pipeline_version: str,
        attachment_id: str,
        message_id: str,
        conversation_id: str,
        vector_count: int,
    ) -> None:
        await self._collection.update_one(
            {"_id": ingestion_key},
            {
                "$set": {
                    "user_id": user_id,
                    "content_sha256": content_sha256,
                    "pipeline_version": pipeline_version,
                    "attachment_id": attachment_id,
                    "message_id": message_id,
                    "conversation_id": conversation_id,
                    "vector_count": vector_count,
                    "updated_at": datetime.now(UTC),
                },
                "$setOnInsert": {
                    "created_at": datetime.now(UTC),
                },
            },
            upsert=True,
        )
