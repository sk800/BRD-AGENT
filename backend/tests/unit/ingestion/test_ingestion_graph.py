import pytest

from brd_agent.agents.graph.ingestion_graph import get_ingestion_graph
from brd_agent.services.vector_ingestion_service import VectorIngestionService


@pytest.fixture(autouse=True)
def mock_vector_ingestion(monkeypatch):
    async def fake_ingest(self, **kwargs):
        return {
            "vector_ingestion_status": "done",
            "vectors_ingested": 1,
            "vector_ingestion_skipped_attachments": 0,
            "vector_ingestion_results": [],
            "embedding_model": "test-model",
            "embedding_pipeline_version": "test-pipeline",
        }

    monkeypatch.setattr(VectorIngestionService, "ingest_chunks", fake_ingest)


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
                    "content_sha256": "abc123",
                }
            ],
            "extracted_documents": [],
            "extraction_errors": [],
            "extraction_status": "pending",
            "chunking_method": "recursive",
            "chunks": [],
            "chunking_status": "pending",
            "vector_ingestion_status": "pending",
            "vectors_ingested": 0,
            "vector_ingestion_skipped_attachments": 0,
            "vector_ingestion_results": [],
            "current_stage": "extraction",
            "errors": [],
        }
    )

    assert result["extraction_status"] == "done"
    assert result["chunking_status"] == "done"
    assert result["vector_ingestion_status"] == "done"
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
            "vector_ingestion_status": "pending",
            "vectors_ingested": 0,
            "vector_ingestion_skipped_attachments": 0,
            "vector_ingestion_results": [],
            "current_stage": "extraction",
            "errors": [],
        }
    )

    assert result["extraction_status"] == "failed"
    assert result["chunking_status"] == "skipped"
    assert result["chunks"] == []
