
import logging
from pathlib import Path
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

from brd_agent.core.config import get_settings


logger = logging.getLogger(__name__)

IMAGE_OUTPUT_DIR = Path("output/images")

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


def extract_image(file_path: str) -> dict:
    path = Path(file_path)
    element_id = _id()
    settings = get_settings()
    max_bytes = settings.max_file_size_mb * 1024 * 1024

    if path.stat().st_size > max_bytes:
        raise ValueError(
            f"Image exceeds the configured {settings.max_file_size_mb}MB limit"
        )

    try:
        with Image.open(path) as image:
            image.verify()
    except (
        Image.DecompressionBombError,
        UnidentifiedImageError,
        OSError,
    ) as exc:
        raise ValueError(f"Invalid image file: {path.name}") from exc

    # Preserve the original image
    IMAGE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_image = (
        IMAGE_OUTPUT_DIR / f"{path.stem}_{element_id}{path.suffix}"
    )
    output_image.write_bytes(path.read_bytes())

    # OCR
    texts = []

    try:
        for result in _get_ocr().predict(str(path)):
            data = result.json

            if callable(data):
                data = data()

            data = data.get("res", data)

            texts.extend(
                text for text in data.get("rec_texts", [])
                if text
            )

    except Exception:
        logger.exception("OCR failed for image %s", path)

    ocr_text = _clean(" ".join(texts))

    return {
        "document": {
            "document_id": f"doc_{uuid4().hex[:10]}",
            "filename": path.name,
            "file_type": path.suffix.lower().lstrip("."),
        },
        "elements": [
            {
                "element_id": element_id,
                "type": "figure",
                "content": {
                    "image_path": str(output_image),
                    "ocr_text": ocr_text,
                },
                "location": {
                    "order": 1,
                },
                "citation": {
                    "element_id": element_id,
                },
            }
        ],
    }

