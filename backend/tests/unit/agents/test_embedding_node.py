import pytest

from brd_agent.agents.nodes.embedding import embedding_node


@pytest.mark.asyncio
async def test_embedding_node_skips_empty_chunks():
    result = await embedding_node({"chunks": []})

    assert result["embedding_status"] == "skipped"
    assert result["chunk_embeddings"] == []
    assert result["embedding_dimension"] == 0


@pytest.mark.asyncio
async def test_embedding_node_serializes_embeddings(monkeypatch):
    class FakeEmbeddings:
        def tolist(self):
            return [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

    class FakeEmbeddingService:
        def embed_documents(self, texts):
            assert texts == ["first chunk", "second chunk"]
            return FakeEmbeddings()

    monkeypatch.setattr(
        "brd_agent.agents.nodes.embedding.EmbeddingService",
        FakeEmbeddingService,
    )

    result = await embedding_node(
        {
            "chunks": [
                {"text": "first chunk"},
                {"text": ""},
                {"text": "second chunk"},
            ]
        }
    )

    assert result["embedding_status"] == "done"
    assert result["embedding_dimension"] == 3
    assert [chunk["text"] for chunk in result["embedded_chunks"]] == [
        "first chunk",
        "second chunk",
    ]
    assert result["embedded_chunks"][0]["embedding"] == [0.1, 0.2, 0.3]
    assert result["chunk_embeddings"] == [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
    ]