from datetime import datetime

from pydantic import BaseModel, Field


class AttachmentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    mime_type: str
    size_bytes: int


class ExtractionErrorResponse(BaseModel):
    attachment_id: str | None = None
    original_filename: str | None = None
    error: str


class ExtractedDocumentResponse(BaseModel):
    attachment_id: str
    original_filename: str | None = None
    extraction: dict


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    text: str | None
    attachments: list[AttachmentResponse]
    extraction_status: str | None = None
    extracted_documents: list[ExtractedDocumentResponse] = Field(default_factory=list)
    extraction_errors: list[ExtractionErrorResponse] = Field(default_factory=list)
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
