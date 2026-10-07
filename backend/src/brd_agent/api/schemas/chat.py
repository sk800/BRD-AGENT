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


class ChunkResponse(BaseModel):
    chunk_id: str
    chunk_type: str
    text: str
    metadata: dict = Field(default_factory=dict)
    parent_id: str | None = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    text: str | None
    attachments: list[AttachmentResponse]
    extraction_status: str | None = None
    extracted_documents: list[ExtractedDocumentResponse] = Field(default_factory=list)
    extraction_errors: list[ExtractionErrorResponse] = Field(default_factory=list)
    chunking_method: str | None = None
    chunking_status: str | None = None
    chunks: list[ChunkResponse] = Field(default_factory=list)
    created_at: datetime


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class SendMessageResponse(BaseModel):
    conversation: ConversationResponse
    message: MessageResponse


class RequirementDiscoveryResponse(BaseModel):
    conversation_id: str
    message_id: str
    requirement_checklist: list[dict]
    requirement_checklist_status: str
    assembled_checklist_context: list[dict] = Field(default_factory=list)
    context_assembly_status: str | None = None
    conversation_route: str = "project"
    assistant_message: str | None = None


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]


class MessageListResponse(BaseModel):
    conversation_id: str
    messages: list[MessageResponse]
