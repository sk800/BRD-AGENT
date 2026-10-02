from fastapi import UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase

from brd_agent.agents.graph import run_ingestion
from brd_agent.core.config import get_settings
from brd_agent.core.exceptions import ChatError
from brd_agent.core.logging import log_extraction_results
from brd_agent.domain.models.chat import ConversationInDB, MessageInDB
from brd_agent.domain.repositories.conversation_repository import ConversationRepository
from brd_agent.domain.repositories.message_repository import MessageRepository
from brd_agent.services.file_storage_service import FileStorageService


class ChatService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._conversations = ConversationRepository(db)
        self._messages = MessageRepository(db)
        self._file_storage = FileStorageService()

    async def send_message(
        self,
        user_id: str,
        text: str | None,
        files: list[UploadFile],
        conversation_id: str | None = None,
    ) -> tuple[ConversationInDB, MessageInDB]:
        normalized_text = text.strip() if text and text.strip() else None

        if normalized_text is None and not files:
            raise ChatError("Provide a message, files, or both", status_code=400)

        conversation: ConversationInDB
        if conversation_id:
            existing = await self._conversations.get_by_id(conversation_id, user_id)
            if existing is None:
                raise ChatError("Conversation not found", status_code=404)
            conversation = existing
        else:
            title = self._derive_title(normalized_text, files)
            conversation = await self._conversations.create(user_id, title)

        attachments = await self._file_storage.save_files(user_id, files) if files else []

        message = await self._messages.create(
            conversation_id=conversation.id,
            user_id=user_id,
            text=normalized_text,
            attachments=attachments,
        )

        if attachments:
            settings = get_settings()
            ingestion_state = await run_ingestion(
                [attachment.model_dump() for attachment in attachments],
                user_id=user_id,
                conversation_id=conversation.id,
                message_id=message.id,
                chunking_method=settings.default_chunking_method,
            )
            log_extraction_results(
                message_id=message.id,
                conversation_id=conversation.id,
                user_id=user_id,
                extraction_state=ingestion_state,
            )
            updated_message = await self._messages.update_ingestion_results(
                message_id=message.id,
                user_id=user_id,
                extracted_documents=ingestion_state.get("extracted_documents", []),
                extraction_errors=ingestion_state.get("extraction_errors", []),
                extraction_status=ingestion_state.get("extraction_status", "failed"),
                chunking_method=ingestion_state.get("chunking_method"),
                chunking_status=ingestion_state.get("chunking_status"),
                chunks=ingestion_state.get("chunks", []),
                vector_ingestion_status=ingestion_state.get(
                    "vector_ingestion_status"
                ),
                vectors_ingested=ingestion_state.get("vectors_ingested"),
                vector_ingestion_skipped_attachments=ingestion_state.get(
                    "vector_ingestion_skipped_attachments"
                ),
                vector_ingestion_results=ingestion_state.get(
                    "vector_ingestion_results", []
                ),
                embedding_model=ingestion_state.get("embedding_model"),
                embedding_pipeline_version=ingestion_state.get(
                    "embedding_pipeline_version"
                ),
            )
            if updated_message is not None:
                message = updated_message

        await self._conversations.touch(conversation.id)

        return conversation, message

    async def list_conversations(self, user_id: str) -> list[ConversationInDB]:
        return await self._conversations.list_by_user(user_id)

    async def list_messages(
        self,
        user_id: str,
        conversation_id: str,
    ) -> list[MessageInDB]:
        conversation = await self._conversations.get_by_id(conversation_id, user_id)
        if conversation is None:
            raise ChatError("Conversation not found", status_code=404)

        return await self._messages.list_by_conversation(conversation_id, user_id)

    @staticmethod
    def _derive_title(text: str | None, files: list[UploadFile]) -> str:
        if text:
            return text[:80] + ("..." if len(text) > 80 else "")

        if files and files[0].filename:
            return f"Upload: {files[0].filename}"

        return "New conversation"
