from brd_agent.ingestion.pipeline.chunking.parent_child import (
    structure_aware_parent_child,
)
from brd_agent.ingestion.pipeline.chunking.recursive import (
    structure_aware_recursive,
)


def sample_elements():
    return [
        {
            "element_id": "e1",
            "type": "heading",
            "content": "Student Management System",
            "location": {"page": 1, "order": 1},
        },
        {
            "element_id": "e2",
            "type": "paragraph",
            "content": (
                "The system allows administrators to manage student "
                "records, courses, attendance and academic information."
            ),
            "location": {"page": 1, "order": 2},
        },
        {
            "element_id": "e3",
            "type": "heading",
            "content": "Student Registration",
            "location": {"page": 2, "order": 3},
        },
        {
            "element_id": "e4",
            "type": "paragraph",
            "content": (
                "Students can register for courses through the portal. "
                "The system validates the student's eligibility before "
                "completing registration."
            ),
            "location": {"page": 2, "order": 4},
        },
    ]


def test_parent_child_chunking():
    chunks = structure_aware_parent_child(
        sample_elements(),
        parent_chunk_size=2000,
        child_chunk_size=100,
        child_chunk_overlap=20,
    )

    # Chunks should be generated.
    assert len(chunks) > 0

    # There should be both parent and child chunks.
    parents = [
        chunk for chunk in chunks
        if chunk["chunk_type"] == "parent"
    ]

    children = [
        chunk for chunk in chunks
        if chunk["chunk_type"] == "child"
    ]

    assert len(parents) > 0
    assert len(children) > 0

    # Every child must reference an existing parent.
    parent_ids = {
        chunk["chunk_id"]
        for chunk in parents
    }

    for child in children:
        assert child["parent_id"] in parent_ids

    # Chunk IDs must be unique.
    chunk_ids = [
        chunk["chunk_id"]
        for chunk in chunks
    ]

    assert len(chunk_ids) == len(set(chunk_ids))

    # No chunk should be empty.
    for chunk in chunks:
        assert chunk["text"].strip() != ""

    # Structure metadata should be preserved.
    for chunk in chunks:
        assert "heading" in chunk["metadata"]
        assert "section_index" in chunk["metadata"]


def test_recursive_chunking():
    chunks = structure_aware_recursive(
        sample_elements(),
        chunk_size=100,
        chunk_overlap=20,
    )

    # Chunks should be generated.
    assert len(chunks) > 0

    # All chunks should be recursive chunks.
    for chunk in chunks:
        assert chunk["chunk_type"] == "recursive"

    # Chunk IDs must be unique.
    chunk_ids = [
        chunk["chunk_id"]
        for chunk in chunks
    ]

    assert len(chunk_ids) == len(set(chunk_ids))

    # No chunk should be empty.
    for chunk in chunks:
        assert chunk["text"].strip() != ""

    # Structure metadata should be preserved.
    for chunk in chunks:
        assert "heading" in chunk["metadata"]
        assert "section_index" in chunk["metadata"]