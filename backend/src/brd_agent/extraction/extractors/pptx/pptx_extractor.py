
from pathlib import Path
from uuid import uuid4

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE


IMAGE_DIR = Path("output/images")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def _id():
    return f"e_{uuid4().hex[:10]}"


def _clean(text):
    return " ".join(str(text).split())


def _bbox(shape):
    return [
        shape.left,
        shape.top,
        shape.left + shape.width,
        shape.top + shape.height,
    ]


def extract_pptx(file_path: str) -> dict:
    path = Path(file_path)
    presentation = Presentation(str(path))
    elements = []

    for slide_no, slide in enumerate(presentation.slides, start=1):

        for shape in slide.shapes:

            location = {
                "slide": slide_no,
                "bbox": _bbox(shape),
                "order": len(elements) + 1,
            }

            # Table
            if shape.has_table:
                rows = [
                    [_clean(cell.text) for cell in row.cells]
                    for row in shape.table.rows
                ]

                if rows:
                    element_id = _id()

                    elements.append({
                        "element_id": element_id,
                        "type": "table",
                        "content": {
                            "headers": rows[0],
                            "rows": rows[1:],
                        },
                        "location": location,
                        "citation": {
                            "slide": slide_no,
                            "element_id": element_id,
                        },
                    })

                continue

            # Image
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                element_id = _id()
                image = shape.image
                extension = image.ext or "png"

                image_path = (
                    IMAGE_DIR / f"{path.stem}_{element_id}.{extension}"
                )
                image_path.write_bytes(image.blob)

                elements.append({
                    "element_id": element_id,
                    "type": "figure",
                    "content": {
                        "image_path": str(image_path),
                    },
                    "location": location,
                    "citation": {
                        "slide": slide_no,
                        "element_id": element_id,
                    },
                })

                continue

            # Text
            if not getattr(shape, "has_text_frame", False):
                continue

            text = _clean(shape.text)

            if not text:
                continue

            is_title = (
                getattr(shape, "is_placeholder", False)
                and shape.placeholder_format.type == 1
            )

            elements.append({
                "element_id": _id(),
                "type": "heading" if is_title else "paragraph",
                "content": text,
                "location": location,
            })

    return {
        "document": {
            "document_id": f"doc_{uuid4().hex[:10]}",
            "filename": path.name,
            "file_type": "pptx",
            "slide_count": len(presentation.slides),
        },
        "elements": elements,
    }
