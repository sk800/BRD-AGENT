from typing import Any

from brd_agent.agents.state import AgentState
from brd_agent.agents.tools.extraction_tools import invoke_extract_document


async def extraction_node(state: AgentState) -> dict[str, Any]:
    """Run the extraction gateway for each uploaded attachment via the LangGraph tool."""
    attachments = state.get("attachments") or []

    if not attachments:
        return {
            "extracted_documents": [],
            "extraction_errors": [],
            "extraction_status": "skipped",
            "current_stage": "extraction",
        }

    extracted_documents: list[dict[str, Any]] = []
    extraction_errors: list[dict[str, Any]] = []

    for attachment in attachments:
        attachment_id = attachment.get("id")
        file_path = attachment.get("storage_path")
        original_filename = attachment.get("original_filename")

        if not file_path:
            extraction_errors.append(
                {
                    "attachment_id": attachment_id,
                    "original_filename": original_filename,
                    "error": "Missing storage_path for attachment",
                }
            )
            continue

        try:
            extraction = await invoke_extract_document(file_path)
            extracted_documents.append(
                {
                    "attachment_id": attachment_id,
                    "original_filename": original_filename,
                    "storage_path": file_path,
                    "extraction": extraction,
                }
            )
        except Exception as exc:
            extraction_errors.append(
                {
                    "attachment_id": attachment_id,
                    "original_filename": original_filename,
                    "storage_path": file_path,
                    "error": str(exc),
                }
            )

    if extraction_errors and extracted_documents:
        extraction_status = "partial"
    elif extraction_errors:
        extraction_status = "failed"
    else:
        extraction_status = "done"

    return {
        "extracted_documents": extracted_documents,
        "extraction_errors": extraction_errors,
        "extraction_status": extraction_status,
        "current_stage": "extraction",
    }
