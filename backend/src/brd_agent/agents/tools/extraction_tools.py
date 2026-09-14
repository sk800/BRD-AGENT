import asyncio

from langchain_core.tools import tool

from brd_agent.extraction.gateway import extract_file


@tool
def extract_document(file_path: str) -> dict:
    """Extract structured text, tables, and elements from a supported document.

    Routes through the extraction gateway for PDF, DOCX, PPTX, images, spreadsheets,
    email, HTML, and plain text files.
    """
    return extract_file(file_path)


async def invoke_extract_document(file_path: str) -> dict:
    """Async wrapper used by LangGraph nodes to call the extraction tool."""
    return await asyncio.to_thread(extract_document.invoke, {"file_path": file_path})
