from pathlib import Path
from uuid import uuid4


def _id():
    return f"e_{uuid4().hex[:10]}"


def extract_text(file_path: str) -> dict:
    path = Path(file_path)

    content = path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    elements = []

    blocks = [
        block.strip()
        for block in content.split("\n\n")
        if block.strip()
    ]

    for order, block in enumerate(blocks, start=1):

        first_line = block.splitlines()[0].strip()

        element_type = (
            "heading"
            if first_line.startswith("#")
            else "paragraph"
        )

        elements.append({
            "element_id": _id(),
            "type": element_type,
            "content": block,
            "location": {
                "order": order,
            },
        })

    return {
        "document": {
            "document_id": f"doc_{uuid4().hex[:10]}",
            "filename": path.name,
            "file_type": path.suffix.lower().lstrip("."),
        },
        "elements": elements,
    }