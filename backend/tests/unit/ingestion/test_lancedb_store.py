from brd_agent.ingestion.vector.lancedb_store import LanceChunkStore


def test_delete_obsolete_file_chunks_keeps_current_and_other_file_rows(tmp_path):
    store = LanceChunkStore(db_path=str(tmp_path))
    store.upsert_chunks(
        [
            {
                "vector_id": "old-version",
                "user_id": "user-1",
                "content_sha256": "same-file",
                "pipeline_version": "v1",
                "text": "old chunking",
                "vector": [0.1, 0.2],
            },
            {
                "vector_id": "current-version",
                "user_id": "user-1",
                "content_sha256": "same-file",
                "pipeline_version": "v2",
                "text": "current chunking",
                "vector": [0.2, 0.1],
            },
            {
                "vector_id": "other-user",
                "user_id": "user-2",
                "content_sha256": "same-file",
                "pipeline_version": "v1",
                "text": "other user's chunk",
                "vector": [0.3, 0.1],
            },
            {
                "vector_id": "other-file",
                "user_id": "user-1",
                "content_sha256": "other-file",
                "pipeline_version": "v1",
                "text": "other file chunk",
                "vector": [0.1, 0.3],
            },
        ]
    )

    deleted = store.delete_obsolete_file_chunks(
        user_id="user-1",
        content_sha256="same-file",
        pipeline_version="v2",
    )

    rows = store._db.open_table("document_chunks").to_pandas()
    assert deleted == 1
    assert set(rows["vector_id"]) == {
        "current-version",
        "other-user",
        "other-file",
    }
