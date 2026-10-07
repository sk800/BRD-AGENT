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
    conversation_history: list[dict[str, str]]

    # Extraction
    extracted_documents: list[dict[str, Any]]
    extraction_errors: list[dict[str, Any]]
    extraction_status: str

    # Chunking
    chunking_method: str
    chunks: list[dict[str, Any]]
    chunking_status: str

    # Vector ingestion (LanceDB + embeddings)
    vector_ingestion_status: str
    vectors_ingested: int
    vector_ingestion_skipped_attachments: int
    vector_ingestion_results: list[dict[str, Any]]
    embedding_model: str
    embedding_pipeline_version: str

    # Requirement discovery and context assembly
    requirement_text: str | None
    requirement_checklist: list[dict[str, Any]]
    requirement_checklist_status: str
    prior_checklist: list[dict[str, Any]]
    conversation_route: str
    assistant_message: str
    memory_context: list[dict[str, Any]]
    assembled_checklist_context: list[dict[str, Any]]
    enterprise_sources: list[dict[str, Any]]
    retrieval_top_k: int | None
    assembled_context: dict[str, Any]
    context_assembly_status: str

    # Workflow control
    current_stage: str
    errors: list[str]
