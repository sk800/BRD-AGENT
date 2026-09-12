from datetime import datetime

from pydantic import BaseModel, Field


class AttachmentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    mime_type: str
    size_bytes: int


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    text: str | None
    attachments: list[AttachmentResponse]
    created_at: datetime


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class SendMessageResponse(BaseModel):
    conversation: ConversationResponse
    message: MessageResponse


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]


class MessageListResponse(BaseModel):
    conversation_id: str
    messages: list[MessageResponse]
