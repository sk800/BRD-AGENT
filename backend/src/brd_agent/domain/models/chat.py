from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class AttachmentInDB(BaseModel):
    id: str
    filename: str
    original_filename: str
    mime_type: str
    size_bytes: int
    storage_path: str


class MessageInDB(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    conversation_id: str
    user_id: str
    role: str = "user"
    text: str | None = None
    attachments: list[AttachmentInDB] = Field(default_factory=list)
    created_at: datetime


class ConversationInDB(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime


def build_conversation_document(conversation_id: str, user_id: str, title: str) -> dict:
    now = datetime.now(UTC)
    return {
        "_id": conversation_id,
        "user_id": user_id,
        "title": title,
        "created_at": now,
        "updated_at": now,
    }


def build_message_document(
    message_id: str,
    conversation_id: str,
    user_id: str,
    text: str | None,
    attachments: list[dict],
) -> dict:
    return {
        "_id": message_id,
        "conversation_id": conversation_id,
        "user_id": user_id,
        "role": "user",
        "text": text,
        "attachments": attachments,
        "created_at": datetime.now(UTC),
    }
