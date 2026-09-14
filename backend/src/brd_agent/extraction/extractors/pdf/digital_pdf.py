from pathlib import Path
from uuid import uuid4

import fitz
IMAGE_OUTPUT_DIR = Path("output/images")
IMAGE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ocr = None


def _get_ocr():
    global ocr

    if ocr is None:
        from paddleocr import PaddleOCR

        ocr = PaddleOCR(
            lang="en",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )

    return ocr


def _id():
    return f"e_{uuid4().hex[:10]}"


def _clean(text):
    return " ".join(str(text).split())


def _bbox(value):
    return [round(float(x), 2) for x in value]


def _text_type(block):
    spans = [
        span
        for line in block.get("lines", [])
        for span in line.get("spans", [])
    ]

    text = _clean(
        " ".join(
            span.get("text", "")
            for span in spans
        )
    )

    if not text:
        return "paragraph"

    max_size = max(
        float(span.get("size", 0))
        for span in spans
    )

    if max_size >= 16:
        return "heading"

    if text.startswith(("-", "*", "•")):
        return "list"

    return "paragraph"


def _extract_text(page):
    elements = []

    for block in page.get_text("dict", sort=True).get("blocks", []):

        if block.get("type") != 0:
            continue

        text = _clean(
            " ".join(
                span.get("text", "")
                for line in block.get("lines", [])
                for span in line.get("spans", [])
            )
        )

        if not text:
            continue

        elements.append({
            "element_id": _id(),
            "type": _text_type(block),
            "content": text,
            "location": {
                "page": page.number + 1,
                "bbox": _bbox(block["bbox"]),
            },
        })

    return elements


def _extract_tables(page):
    elements = []

    try:
        tables = page.find_tables()
    except Exception:
        return elements

    for table in tables.tables:

        try:
            data = table.extract()
        except Exception:
            continue

        if not data:
            continue

        rows = [
            [
                _clean(cell) if cell is not None else ""
                for cell in row
            ]
            for row in data
        ]

        if not rows:
            continue

        element_id = _id()

        elements.append({
            "element_id": element_id,
            "type": "table",
            "content": {
                "headers": rows[0],
                "rows": rows[1:],
            },
            "location": {
                "page": page.number + 1,
                "bbox": _bbox(table.bbox),
            },
            "citation": {
                "page": page.number + 1,
                "element_id": element_id,
            },
        })

    return elements


def _extract_images(page, filename):
    elements = []

    for block in page.get_text("dict", sort=True).get("blocks", []):

        if block.get("type") != 1:
            continue

        image_bytes = block.get("image")

        if not image_bytes:
            continue

        element_id = _id()
        extension = block.get("ext", "png")

        image_path = (
            IMAGE_OUTPUT_DIR
            / f"{Path(filename).stem}_{element_id}.{extension}"
        )

        image_path.write_bytes(image_bytes)

        ocr_text = ""

        try:
            texts = []

            for result in _get_ocr().predict(str(image_path)):
                data = getattr(result, "json", None)

                if callable(data):
                    data = data()

                if isinstance(data, dict):
                    data = data.get("res", data)

                    texts.extend(
                        str(text)
                        for text in data.get("rec_texts", [])
                        if text
                    )

            ocr_text = _clean(" ".join(texts))

        except Exception:
            pass

        elements.append({
            "element_id": element_id,
            "type": "figure",
            "content": {
                "image_path": str(image_path),
                "ocr_text": ocr_text,
            },
            "location": {
                "page": page.number + 1,
                "bbox": _bbox(block["bbox"]),
            },
            "citation": {
                "page": page.number + 1,
                "element_id": element_id,
            },
        })

    return elements


def extract_digital_pdf(file_path: str) -> dict:
    path = Path(file_path)
    elements = []

    with fitz.open(path) as document:

        for page in document:

            page_elements = (
                _extract_text(page)
                + _extract_tables(page)
                + _extract_images(page, path.name)
            )

            page_elements.sort(
                key=lambda element: (
                    element["location"]["bbox"][1],
                    element["location"]["bbox"][0],
                )
            )

            elements.extend(page_elements)

        page_count = len(document)

    for order, element in enumerate(elements, start=1):
        element["location"]["order"] = order

    return {
        "document": {
            "document_id": f"doc_{uuid4().hex[:10]}",
            "filename": path.name,
            "file_type": "pdf",
            "page_count": page_count,
        },
        "elements": elements,
    }