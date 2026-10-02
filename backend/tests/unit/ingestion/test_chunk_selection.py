from brd_agent.ingestion.pipeline.embedding.chunk_selection import chunks_for_embedding


def test_parent_child_selects_children_and_standalone_parents():
    chunks = [
        {"chunk_type": "parent", "text": "big", "metadata": {}},
        {
            "chunk_type": "parent",
            "text": "small",
            "metadata": {"standalone_parent": True},
        },
        {"chunk_type": "child", "text": "part", "metadata": {}},
    ]

    selected = chunks_for_embedding(chunks)

    assert len(selected) == 2
    assert selected[0]["chunk_type"] == "parent"
    assert selected[0]["metadata"]["standalone_parent"] is True
    assert selected[1]["chunk_type"] == "child"


def test_recursive_selects_recursive_chunks_only():
    chunks = [
        {"chunk_type": "recursive", "text": "one"},
        {"chunk_type": "parent", "text": "two", "metadata": {}},
    ]

    selected = chunks_for_embedding(chunks)

    assert len(selected) == 1
    assert selected[0]["chunk_type"] == "recursive"
