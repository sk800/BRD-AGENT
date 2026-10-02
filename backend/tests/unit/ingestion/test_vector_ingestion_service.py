import pytest

from brd_agent.services.vector_ingestion_service import VectorIngestionService


class FakeVectorRepo:
    def __init__(self):
        self.keys: set[str] = set()

    async def find_by_key(self, ingestion_key: str):
        if ingestion_key in self.keys:
            return {"_id": ingestion_key}
        return None

    async def register(self, **kwargs):
        self.keys.add(kwargs["ingestion_key"])


@pytest.mark.asyncio
async def test_vector_ingestion_skips_duplicate_file(monkeypatch, tmp_path):
    repo = FakeVectorRepo()
    service = VectorIngestionService(repo)

    file_path = tmp_path / "doc.txt"
    file_path.write_text("same content", encoding="utf-8")

    async def fake_embed(texts):
        return [[0.1, 0.2, 0.3] for _ in texts]

    monkeypatch.setattr(
        "brd_agent.services.vector_ingestion_service.embed_texts",
        fake_embed,
    )
    monkeypatch.setattr(
        "brd_agent.services.vector_ingestion_service.LanceChunkStore.upsert_chunks",
        lambda self, rows: len(rows),
    )

    attachments = [
        {
            "id": "att-1",
            "storage_path": str(file_path),
            "content_sha256": "sha-same",
        }
    ]
    chunks = [
        {
            "chunk_id": "chunk_0_0",
            "chunk_type": "recursive",
            "text": "same content",
            "metadata": {"attachment_id": "att-1"},
        }
    ]

    first = await service.ingest_chunks(
        user_id="user-1",
        conversation_id="conv-1",
        message_id="msg-1",
        attachments=attachments,
        chunks=chunks,
        chunking_method="recursive",
    )
    second = await service.ingest_chunks(
        user_id="user-1",
        conversation_id="conv-1",
        message_id="msg-2",
        attachments=attachments,
        chunks=chunks,
        chunking_method="recursive",
    )

    assert first["vector_ingestion_status"] == "done"
    assert first["vectors_ingested"] == 1
    assert second["vector_ingestion_status"] == "skipped_duplicate"
    assert second["vectors_ingested"] == 0
