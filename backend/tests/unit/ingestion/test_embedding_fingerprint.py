from brd_agent.ingestion.pipeline.embedding.fingerprint import (
    ingestion_key,
    pipeline_version,
    vector_chunk_id,
)


def test_pipeline_version_is_stable():
    first = pipeline_version(
        embedding_model="BAAI/bge-small-en-v1.5",
        embedding_pipeline_version=1,
        chunking_method="recursive",
    )
    second = pipeline_version(
        embedding_model="BAAI/bge-small-en-v1.5",
        embedding_pipeline_version=1,
        chunking_method="recursive",
    )
    assert first == second
    assert "recursive" in first


def test_ingestion_key_changes_when_file_changes():
    pipeline = pipeline_version(
        embedding_model="BAAI/bge-small-en-v1.5",
        embedding_pipeline_version=1,
        chunking_method="recursive",
    )
    key_a = ingestion_key(
        user_id="user-1",
        content_sha256="aaa",
        pipeline=pipeline,
    )
    key_b = ingestion_key(
        user_id="user-1",
        content_sha256="bbb",
        pipeline=pipeline,
    )
    assert key_a != key_b


def test_vector_chunk_id_is_stable_for_same_chunk():
    pipeline = "embed=test:v1:chunk=recursive"
    chunk = {
        "chunk_id": "chunk_0_0",
        "chunk_type": "recursive",
        "text": "hello world",
    }
    first = vector_chunk_id(
        user_id="user-1",
        content_sha256="abc",
        pipeline=pipeline,
        chunk=chunk,
    )
    second = vector_chunk_id(
        user_id="user-1",
        content_sha256="abc",
        pipeline=pipeline,
        chunk=chunk,
    )
    assert first == second
