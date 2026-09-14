import pytest

from brd_agent.agents.nodes.extraction import extraction_node


@pytest.mark.asyncio
async def test_extraction_node_skips_when_no_attachments():
    result = await extraction_node({"attachments": []})

    assert result["extraction_status"] == "skipped"
    assert result["extracted_documents"] == []
    assert result["extraction_errors"] == []


@pytest.mark.asyncio
async def test_extraction_node_extracts_attachments(monkeypatch):
    async def fake_invoke(file_path: str) -> dict:
        return {
            "document": {"filename": file_path},
            "elements": [{"type": "paragraph", "content": "hello"}],
        }

    monkeypatch.setattr(
        "brd_agent.agents.nodes.extraction.invoke_extract_document",
        fake_invoke,
    )

    result = await extraction_node(
        {
            "attachments": [
                {
                    "id": "att-1",
                    "storage_path": "/tmp/sample.txt",
                    "original_filename": "sample.txt",
                }
            ]
        }
    )

    assert result["extraction_status"] == "done"
    assert len(result["extracted_documents"]) == 1
    assert result["extracted_documents"][0]["attachment_id"] == "att-1"
    assert result["extracted_documents"][0]["extraction"]["elements"][0]["content"] == "hello"


@pytest.mark.asyncio
async def test_extraction_node_records_errors(monkeypatch):
    async def failing_invoke(_: str) -> dict:
        raise ValueError("unsupported format")

    monkeypatch.setattr(
        "brd_agent.agents.nodes.extraction.invoke_extract_document",
        failing_invoke,
    )

    result = await extraction_node(
        {
            "attachments": [
                {
                    "id": "att-2",
                    "storage_path": "/tmp/bad.xyz",
                    "original_filename": "bad.xyz",
                }
            ]
        }
    )

    assert result["extraction_status"] == "failed"
    assert result["extracted_documents"] == []
    assert result["extraction_errors"][0]["error"] == "unsupported format"
