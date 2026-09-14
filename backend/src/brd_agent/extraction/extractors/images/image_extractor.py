import logging
from pathlib import Path
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

from brd_agent.core.config import get_settings


logger = logging.getLogger(__name__)

IMAGE_OUTPUT_DIR = Path("output/images")

# PP-OCRv6 models are incompatible with paddlepaddle 3.0 on macOS Intel.
PADDLE_OCR_VERSION = "PP-OCRv4"

ocr = None


def _get_ocr():
    global ocr

    if ocr is None:
        from paddleocr import PaddleOCR

        ocr = PaddleOCR(
            lang="en",
            ocr_version=PADDLE_OCR_VERSION,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )

    return ocr


def _id():
    return f"e_{uuid4().hex[:10]}"


def _clean(text):
    return " ".join(str(text).split())


def _run_paddle_ocr(path: Path) -> list[str]:
    texts: list[str] = []

    for result in _get_ocr().predict(str(path)):
        data = result.json

        if callable(data):
            data = data()

        data = data.get("res", data)

        texts.extend(text for text in data.get("rec_texts", []) if text)

    return texts


def _extract_ocr_text(path: Path) -> tuple[str, str | None, str | None]:
    """Return OCR text, engine name, and optional warning message."""

    try:
        texts = _run_paddle_ocr(path)
        ocr_text = _clean(" ".join(texts))
        if ocr_text:
            return ocr_text, "paddleocr", None
        return "", "paddleocr", "No text detected in image"
    except ModuleNotFoundError:
        warning = (
            "paddleocr is not installed. Install with: pip install -e \".[layout]\""
        )
        logger.warning("PaddleOCR unavailable for %s: %s", path.name, warning)
        return "", None, warning
    except Exception as exc:
        warning = str(exc)
        logger.warning("PaddleOCR failed for %s: %s", path.name, warning)
        return "", None, warning


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

    ocr_text, ocr_engine, ocr_warning = _extract_ocr_text(path)

    if ocr_warning:
        logger.warning("Image OCR warning for %s: %s", path.name, ocr_warning)
    elif ocr_text:
        logger.info(
            "Image OCR complete for %s via %s (%s chars)",
            path.name,
            ocr_engine,
            len(ocr_text),
        )

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
                    "ocr_engine": ocr_engine,
                    "ocr_warning": ocr_warning,
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
