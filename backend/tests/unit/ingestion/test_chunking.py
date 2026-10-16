from brd_agent.ingestion.pipeline.chunking.parent_child import (
    structure_aware_parent_child,
)
from brd_agent.ingestion.pipeline.chunking.recursive import (
    structure_aware_recursive,
)
from brd_agent.ingestion.pipeline.embedding.chunk_selection import (
    chunks_for_embedding,
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


def test_parent_child_keeps_conversation_messages_in_separate_chunks():
    elements = [
        {"type": "heading", "content": "Project discussion"},
        {
            "type": "paragraph",
            "content": "[00:01:00] Alex: Agents need ticket assignment.",
        },
        {
            "type": "paragraph",
            "content": "[00:02:00] Blair: Lunch is at noon.",
        },
        {
            "type": "paragraph",
            "content": "[00:03:00] Alex: Team leads may mark urgent.",
        },
        {
            "type": "paragraph",
            "content": "[00:04:00] Blair: The printer is still broken.",
        },
        {
            "type": "paragraph",
            "content": "[00:05:00] Alex: Keep an audit trail.",
        },
    ]

    chunks = chunks_for_embedding(structure_aware_parent_child(elements))
    texts = [chunk["text"] for chunk in chunks]

    assert len(texts) == 5
    assert any("Team leads may mark urgent" in text for text in texts)
    assert not any(
        "Team leads may mark urgent" in text and "printer is still broken" in text
        for text in texts
    )


def test_parent_child_keeps_whatsapp_messages_in_separate_chunks():
    elements = [
        {"type": "heading", "content": "Clinic group chat"},
        {
            "type": "paragraph",
            "content": (
                "[22/08/26, 9:00 am] Alex: Patients book online. "
                "[22/08/26, 9:05 am] Blair: New patient slots are 20 minutes."
            ),
        },
        {
            "type": "paragraph",
            "content": "[22/08/26, 9:10 am] Alex: Reminder time is undecided.",
        },
        {
            "type": "paragraph",
            "content": "[22/08/26, 9:15 am] Blair: Use the current patient ID.",
        },
        {
            "type": "paragraph",
            "content": "[22/08/26, 9:20 am] Alex: We need a clinic report.",
        },
        {
            "type": "paragraph",
            "content": "[22/08/26, 9:25 am] Blair: Thank you.",
        },
    ]

    chunks = chunks_for_embedding(structure_aware_parent_child(elements))
    message_chunks = [
        chunk
        for chunk in chunks
        if "Patients book online." in chunk["text"]
        or "New patient slots are 20 minutes." in chunk["text"]
    ]

    assert len(message_chunks) == 2
    assert all(
        not (
            "Patients book online." in chunk["text"]
            and "New patient slots are 20 minutes." in chunk["text"]
        )
        for chunk in message_chunks
    )


def test_parent_child_keeps_email_threads_in_separate_chunks():
    elements = [{"type": "heading", "content": "Email export"}]
    for index in range(5):
        elements.extend(
            [
                {
                    "type": "paragraph",
                    "content": (
                        f"From: person{index}@example.com To: team@example.com "
                        f"Subject: Thread {index}"
                    ),
                },
                {
                    "type": "paragraph",
                    "content": f"Requirement {index} must be retained.",
                },
                {
                    "type": "paragraph",
                    "content": f"Unrelated note {index}.",
                },
            ]
        )

    chunks = chunks_for_embedding(structure_aware_parent_child(elements))
    texts = [chunk["text"] for chunk in chunks]

    assert any("Requirement 2 must be retained." in text for text in texts)
    assert not any(
        "Requirement 2 must be retained." in text
        and "Requirement 3 must be retained." in text
        for text in texts
    )