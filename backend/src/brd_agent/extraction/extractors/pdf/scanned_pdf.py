from pathlib import Path
from uuid import uuid4

import fitz
from bs4 import BeautifulSoup
from PIL import Image
OUTPUT_DIR = Path("output/images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

pipeline = None


def _get_pipeline():
    global pipeline

    if pipeline is None:
        from paddleocr import PPStructureV3

        pipeline = PPStructureV3(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )

    return pipeline


def _id():
    return f"e_{uuid4().hex[:10]}"


def _clean(text):
    return " ".join(str(text).split())


def _bbox(value):
    return [round(float(x), 2) for x in value]


def _result_to_dict(result):
    data = getattr(result, "json", None)

    if callable(data):
        data = data()

    if isinstance(data, dict):
        return data.get("res", data)

    if isinstance(result, dict):
        return result.get("res", result)

    return {}


def _inside(box, region):
    x1, y1, x2, y2 = box
    rx1, ry1, rx2, ry2 = region

    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2

    return rx1 <= cx <= rx2 and ry1 <= cy <= ry2


def _ocr_text(data, region):
    ocr = data.get("overall_ocr_res", {})

    texts = ocr.get("rec_texts", [])
    boxes = ocr.get("rec_boxes", [])

    matches = []

    for text, box in zip(texts, boxes):

        if not text:
            continue

        box = list(box)

        if _inside(box, region):
            matches.append(
                (
                    box[1],
                    box[0],
                    _clean(text),
                )
            )

    matches.sort(key=lambda item: (item[0], item[1]))

    return _clean(" ".join(item[2] for item in matches))


def _table_from_html(html):
    soup = BeautifulSoup(html or "", "html.parser")

    table = soup.find("table")

    if not table:
        return None

    rows = []
    cells = []

    for row_index, row in enumerate(table.find_all("tr")):

        row_values = []

        for column_index, cell in enumerate(
            row.find_all(["th", "td"])
        ):
            text = _clean(
                cell.get_text(" ", strip=True)
            )

            rowspan = int(
                cell.get("rowspan", 1)
            )

            colspan = int(
                cell.get("colspan", 1)
            )

            row_values.append(text)

            cells.append({
                "row": row_index,
                "column": column_index,
                "text": text,
                "rowspan": rowspan,
                "colspan": colspan,
            })

        if row_values:
            rows.append(row_values)

    if not rows:
        return None

    return {
        "headers": rows[0],
        "rows": rows[1:],
        "cells": cells,
        "html": str(table),
    }


def _crop(image_path, bbox):
    image = Image.open(image_path)

    x1, y1, x2, y2 = map(int, bbox)

    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(image.width, x2)
    y2 = min(image.height, y2)

    return image.crop((x1, y1, x2, y2))


def _element_from_block(
    block,
    data,
    page_number,
    page_image,
    filename,
):
    label = block.get("block_label", "text")
    bbox = block.get("block_bbox", [])

    if len(bbox) != 4:
        return None

    element_id = _id()

    if label in {
        "doc_title",
        "paragraph_title",
        "title",
    }:
        element_type = "heading"

    elif label == "table":
        element_type = "table"

    elif label in {
        "image",
        "figure",
        "chart",
    }:
        element_type = "figure"

    elif label == "list":
        element_type = "list"

    else:
        element_type = "paragraph"

    location = {
        "page": page_number,
        "bbox": _bbox(bbox),
    }

    element = {
        "element_id": element_id,
        "type": element_type,
        "content": "",
        "location": location,
    }

    if element_type == "table":

        html = block.get("block_content", "")

        table = _table_from_html(html)

        if table:
            element["content"] = table
        else:
            element["content"] = {
                "text": _ocr_text(data, bbox)
            }

        element["citation"] = {
            "page": page_number,
            "element_id": element_id,
        }

        return element

    if element_type == "figure":

        cropped = _crop(
            page_image,
            bbox,
        )

        image_path = (
            OUTPUT_DIR
            / f"{Path(filename).stem}_{element_id}.png"
        )

        cropped.save(str(image_path))

        element["content"] = {
            "image_path": str(image_path),
            "ocr_text": _ocr_text(data, bbox),
        }

        element["citation"] = {
            "page": page_number,
            "element_id": element_id,
        }

        return element

    content = _clean(
        block.get("block_content", "")
    )

    if not content:
        content = _ocr_text(
            data,
            bbox,
        )

    if not content:
        return None

    element["content"] = content

    return element


def extract_scanned_pdf(file_path: str) -> dict:
    path = Path(file_path)
    elements = []

    with fitz.open(path) as document:

        page_count = len(document)

        for page_number, page in enumerate(
            document,
            start=1,
        ):

            pixmap = page.get_pixmap(
                dpi=200,
                alpha=False,
            )

            page_image = (
                OUTPUT_DIR
                / f"{path.stem}_page_{page_number}.png"
            )

            pixmap.save(str(page_image))

            try:
                results = _get_pipeline().predict(
                    str(page_image)
                )
            except Exception:
                results = []

            for result in results:

                data = _result_to_dict(result)

                parsing_blocks = data.get(
                    "parsing_res_list",
                    [],
                )

                page_elements = []

                for block in parsing_blocks:

                    element = _element_from_block(
                        block,
                        data,
                        page_number,
                        page_image,
                        path.name,
                    )

                    if element:
                        page_elements.append(element)

                # Fallback when parsing_res_list is unavailable.
                if not page_elements:

                    layout = data.get(
                        "layout_det_res",
                        {},
                    )

                    for box in layout.get(
                        "boxes",
                        [],
                    ):

                        block = {
                            "block_label": box.get(
                                "label",
                                "text",
                            ),
                            "block_bbox": box.get(
                                "coordinate",
                                [],
                            ),
                            "block_content": "",
                        }

                        element = _element_from_block(
                            block,
                            data,
                            page_number,
                            page_image,
                            path.name,
                        )

                        if element:
                            page_elements.append(element)

                page_elements.sort(
                    key=lambda element: (
                        element["location"]["bbox"][1],
                        element["location"]["bbox"][0],
                    )
                )

                elements.extend(page_elements)

    for order, element in enumerate(
        elements,
        start=1,
    ):
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