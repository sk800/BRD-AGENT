import pytest

from brd_agent.agents.graph.chunking_graph import (
    get_chunking_graph,
)


def sample_extracted_documents():
    return [
        {
            "attachment_id": "test-1",
            "original_filename": "sample.txt",
            "extraction": {
                "elements": [
                    {
                        "element_id": "e1",
                        "type": "heading",
                        "content": "Student Management",
                        "location": {"page": 1, "order": 1},
                    },
                    {
                        "element_id": "e2",
                        "type": "paragraph",
                        "content": (
                            "The system allows administrators "
                            "to manage student records and courses."
                        ),
                        "location": {"page": 1, "order": 2},
                    },
                ]
            },
        }
    ]


@pytest.mark.asyncio
async def test_parent_child_routing():
    graph = get_chunking_graph()

    result = await graph.ainvoke(
        {
            "extracted_documents": sample_extracted_documents(),
            "chunking_method": "parent_child",
            "chunks": [],
            "current_stage": "chunking",
            "errors": [],
        }
    )

    assert result["chunks"]
    assert any(
        chunk["chunk_type"] == "parent"
        for chunk in result["chunks"]
    )


@pytest.mark.asyncio
async def test_recursive_routing():
    graph = get_chunking_graph()

    result = await graph.ainvoke(
        {
            "extracted_documents": sample_extracted_documents(),
            "chunking_method": "recursive",
            "chunks": [],
            "current_stage": "chunking",
            "errors": [],
        }
    )

    assert result["chunks"]
    assert all(
        chunk["chunk_type"] == "recursive"
        for chunk in result["chunks"]
    )