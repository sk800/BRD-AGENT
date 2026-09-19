import time

from brd_agent.ingestion.pipeline.chunking.parent_child import (
    structure_aware_parent_child,
)
from brd_agent.ingestion.pipeline.chunking.recursive import (
    structure_aware_recursive,
)


def performance_elements():
    """Create a realistic BRD-like extracted document."""

    sections = [
        "Project Overview",
        "Business Requirements",
        "User Management",
        "Student Registration",
        "Course Management",
        "Attendance Management",
        "Fee Management",
        "Reports and Analytics",
        "Security Requirements",
        "System Constraints",
    ]

    elements = []

    for section_index, section_name in enumerate(sections):
        elements.append(
            {
                "element_id": f"h{section_index}",
                "type": "heading",
                "content": section_name,
                "location": {
                    "page": section_index + 1,
                    "order": section_index * 2 + 1,
                },
            }
        )

        paragraph = (
            "The system shall provide a reliable and secure platform "
            "for managing student information and academic activities. "
            "Users shall be able to access the required functionality "
            "based on their assigned roles and permissions. "
            "The system shall validate user input before processing "
            "any request and shall maintain accurate records. "
            "Administrators shall be able to manage users, courses, "
            "attendance, fees, reports and other academic information. "
            "All important operations shall be logged for auditing "
            "and monitoring purposes. "
        )

        # Create a reasonably large section
        content = paragraph * 30

        elements.append(
            {
                "element_id": f"p{section_index}",
                "type": "paragraph",
                "content": content,
                "location": {
                    "page": section_index + 1,
                    "order": section_index * 2 + 2,
                },
            }
        )

    return elements


def average(values):
    return sum(values) / len(values)


def test_compare_chunking_performance():

    elements = performance_elements()

    print("\n")
    print("=" * 60)
    print("STRUCTURE-AWARE CHUNKING PERFORMANCE COMPARISON")
    print("=" * 60)

    # ---------------------------------------------------------
    # Parent-Child
    # ---------------------------------------------------------

    start = time.perf_counter()

    parent_child_chunks = structure_aware_parent_child(
        elements,
        parent_chunk_size=2000,
        child_chunk_size=500,
        child_chunk_overlap=50,
    )

    parent_child_time = time.perf_counter() - start

    parents = [
        chunk
        for chunk in parent_child_chunks
        if chunk["chunk_type"] == "parent"
    ]

    children = [
        chunk
        for chunk in parent_child_chunks
        if chunk["chunk_type"] == "child"
    ]

    # ---------------------------------------------------------
    # Recursive
    # ---------------------------------------------------------

    start = time.perf_counter()

    recursive_chunks = structure_aware_recursive(
        elements,
        chunk_size=500,
        chunk_overlap=50,
    )

    recursive_time = time.perf_counter() - start

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    parent_sizes = [
        len(chunk["text"])
        for chunk in parents
    ]

    child_sizes = [
        len(chunk["text"])
        for chunk in children
    ]

    recursive_sizes = [
        len(chunk["text"])
        for chunk in recursive_chunks
    ]

    total_input_characters = sum(
        len(element.get("content", ""))
        for element in elements
        if isinstance(element.get("content"), str)
    )

    # ---------------------------------------------------------
    # Output
    # ---------------------------------------------------------

    print("\nINPUT DATA")
    print("-" * 60)
    print(f"Number of extracted elements : {len(elements)}")
    print(f"Input characters             : {total_input_characters:,}")

    print("\nPARENT-CHILD")
    print("-" * 60)
    print(f"Total chunks                 : {len(parent_child_chunks)}")
    print(f"Parent chunks                : {len(parents)}")
    print(f"Child chunks                 : {len(children)}")
    print(f"Average parent size          : {average(parent_sizes):.2f}")
    print(f"Average child size           : {average(child_sizes):.2f}")
    print(f"Processing time              : {parent_child_time:.6f} seconds")

    print("\nRECURSIVE")
    print("-" * 60)
    print(f"Total chunks                 : {len(recursive_chunks)}")
    print(f"Average chunk size           : {average(recursive_sizes):.2f}")
    print(f"Processing time              : {recursive_time:.6f} seconds")

    print("\nCOMPARISON")
    print("-" * 60)

    if parent_child_time < recursive_time:
        print("Parent-Child processing time : FASTER")
    elif recursive_time < parent_child_time:
        print("Recursive processing time    : FASTER")
    else:
        print("Processing time              : SAME")

    print("=" * 60)

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    assert parent_child_chunks
    assert recursive_chunks

    assert all(
        chunk["text"].strip()
        for chunk in parent_child_chunks
    )

    assert all(
        chunk["text"].strip()
        for chunk in recursive_chunks
    )