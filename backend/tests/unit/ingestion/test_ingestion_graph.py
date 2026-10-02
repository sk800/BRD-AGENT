import pytest

from brd_agent.agents.graph.ingestion_graph import get_ingestion_graph


@pytest.mark.asyncio
async def test_ingestion_graph_runs_extraction_then_chunking(monkeypatch):
    async def fake_invoke(file_path: str) -> dict:
        return {
            "document": {"filename": file_path, "file_type": "txt"},
            "elements": [
                {"type": "heading", "content": "Scope"},
                {"type": "paragraph", "content": "The system shall support uploads."},
            ],
        }

    monkeypatch.setattr(
        "brd_agent.agents.nodes.extraction.invoke_extract_document",
        fake_invoke,
    )

    graph = get_ingestion_graph()
    result = await graph.ainvoke(
        {
            "user_id": "user-1",
            "conversation_id": "conv-1",
            "message_id": "msg-1",
            "attachments": [
                {
                    "id": "att-1",
                    "storage_path": "/tmp/sample.txt",
                    "original_filename": "sample.txt",
                }
            ],
            "extracted_documents": [],
            "extraction_errors": [],
            "extraction_status": "pending",
            "chunking_method": "recursive",
            "chunks": [],
            "chunking_status": "pending",
            "current_stage": "extraction",
            "errors": [],
        }
    )

    assert result["extraction_status"] == "done"
    assert result["chunking_status"] == "done"
    assert result["chunks"]
    assert all(chunk["chunk_type"] == "recursive" for chunk in result["chunks"])


@pytest.mark.asyncio
async def test_ingestion_graph_skips_chunking_when_extraction_fails(monkeypatch):
    async def failing_invoke(_: str) -> dict:
        raise ValueError("unsupported format")

    monkeypatch.setattr(
        "brd_agent.agents.nodes.extraction.invoke_extract_document",
        failing_invoke,
    )

    graph = get_ingestion_graph()
    result = await graph.ainvoke(
        {
            "user_id": "user-1",
            "conversation_id": "conv-1",
            "message_id": "msg-1",
            "attachments": [
                {
                    "id": "att-1",
                    "storage_path": "/tmp/bad.xyz",
                    "original_filename": "bad.xyz",
                }
            ],
            "extracted_documents": [],
            "extraction_errors": [],
            "extraction_status": "pending",
            "chunking_method": "recursive",
            "chunks": [],
            "chunking_status": "pending",
            "current_stage": "extraction",
            "errors": [],
        }
    )

    assert result["extraction_status"] == "failed"
    assert result["chunking_status"] == "skipped"
    assert result["chunks"] == []
