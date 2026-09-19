from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """Shared LangGraph state for the BRD agent pipeline."""

    # Session
    user_id: str
    conversation_id: str
    message_id: str
    run_id: str

    # User input
    current_user_text: str | None
    attachments: list[dict[str, Any]]

    # Extraction
    extracted_documents: list[dict[str, Any]]
    extraction_errors: list[dict[str, Any]]
    extraction_status: str

    # Chunking
    chunking_method: str
    chunks: list[dict[str, Any]]
    
    # Workflow control
    current_stage: str
    errors: list[str]
