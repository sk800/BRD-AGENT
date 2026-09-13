import logging
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn
from PIL import Image, UnidentifiedImageError

from brd_agent.core.config import get_settings


logger = logging.getLogger(__name__)
IMAGE_DIR = Path("output/images")


def _id():
    return f"e_{uuid4().hex[:10]}"


def _clean(text):
    return " ".join(str(text).split())


def _blocks(document):
    """Yield paragraphs and tables in document order."""
    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield Table(child, document)


def extract_docx(file_path: str) -> dict:
    path = Path(file_path)
    settings = get_settings()
    max_bytes = settings.max_file_size_mb * 1024 * 1024

    if path.stat().st_size > max_bytes:
        raise ValueError(
            f"DOCX exceeds the configured {settings.max_file_size_mb}MB limit"
        )

    document = Document(str(path))
    elements = []

    for block in _blocks(document):

        # Paragraphs and headings
        if isinstance(block, Paragraph):
            text = _clean(block.text)

            if text:
                style = (
                    block.style.name.lower()
                    if block.style
                    else ""
                )

                if "heading" in style or "title" in style:
                    element_type = "heading"
                elif "list" in style or text.startswith(("-", "*", "•")):
                    element_type = "list"
                else:
                    element_type = "paragraph"

                elements.append({
                    "element_id": _id(),
                    "type": element_type,
                    "content": text,
                    "location": {
                        "order": len(elements) + 1
                    }
                })

            # Images inside the paragraph
            for run in block.runs:
                for drawing in run._r.xpath(".//w:drawing"):
                    for blip in drawing.xpath(".//a:blip"):

                        rel_id = blip.get(
                            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
                        )

                        if not rel_id:
                            continue

                        try:
                            image = block.part.related_parts[rel_id]
                        except KeyError:
                            continue

                        image_id = _id()
                        extension = (
                            Path(str(image.partname)).suffix.lower()
                            or ".png"
                        )

                        image_path = (
                            IMAGE_DIR
                            / f"{path.stem}_{image_id}{extension}"
                        )

                        image_bytes = image.blob
                        if len(image_bytes) > max_bytes:
                            raise ValueError(
                                f"Embedded image exceeds the configured {settings.max_file_size_mb}MB limit"
                            )

                        try:
                            with Image.open(BytesIO(image_bytes)) as embedded_image:
                                embedded_image.verify()
                        except (
                            Image.DecompressionBombError,
                            UnidentifiedImageError,
                            OSError,
                        ) as exc:
                            logger.warning(
                                "Skipping invalid embedded image in %s",
                                path,
                            )
                            raise ValueError(
                                f"Invalid embedded image in {path.name}"
                            ) from exc

                        IMAGE_DIR.mkdir(parents=True, exist_ok=True)
                        image_path.write_bytes(image_bytes)

                        elements.append({
                            "element_id": image_id,
                            "type": "figure",
                            "content": {
                                "image_path": str(image_path)
                            },
                            "location": {
                                "order": len(elements) + 1
                            },
                            "citation": {
                                "element_id": image_id
                            }
                        })

        # Tables
        elif isinstance(block, Table):
            rows = [
                [_clean(cell.text) for cell in row.cells]
                for row in block.rows
            ]

            if rows:
                table_id = _id()

                elements.append({
                    "element_id": table_id,
                    "type": "table",
                    "content": {
                        "headers": rows[0],
                        "rows": rows[1:]
                    },
                    "location": {
                        "order": len(elements) + 1
                    },
                    "citation": {
                        "element_id": table_id
                    }
                })

    return {
        "document": {
            "document_id": f"doc_{uuid4().hex[:10]}",
            "filename": path.name,
            "file_type": "docx"
        },
        "elements": elements
    }

