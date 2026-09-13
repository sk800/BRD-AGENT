import pytest
from PIL import Image

from brd_agent.extraction.extractors.images import image_extractor


class FakeResult:
    @property
    def json(self):
        return {
            "res": {
                "rec_texts": [
                    "Document Upload",
                    "High Priority",
                ]
            }
        }


class FakeOCR:
    def predict(self, _path):
        return [FakeResult()]


def test_extract_image_returns_figure_and_ocr_text(
    tmp_path,
    monkeypatch,
):
    source = tmp_path / "requirements.png"

    image = Image.new("RGB", (200, 100), "white")
    image.save(source)

    monkeypatch.setattr(
        image_extractor,
        "ocr",
        FakeOCR(),
    )

    monkeypatch.setattr(
        image_extractor,
        "IMAGE_OUTPUT_DIR",
        tmp_path / "output",
    )

    (tmp_path / "output").mkdir()

    result = image_extractor.extract_image(
        str(source)
    )

    assert result["document"]["file_type"] == "png"

    element = result["elements"][0]

    assert element["type"] == "figure"
    assert "image_path" in element["content"]

    assert element["content"]["ocr_text"] == (
        "Document Upload High Priority"
    )

    assert "citation" in element


def test_extract_image_rejects_invalid_image(tmp_path):
    source = tmp_path / "not-an-image.png"
    source.write_text("not an image", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid image file"):
        image_extractor.extract_image(str(source))


def test_extract_image_rejects_decompression_bomb(tmp_path, monkeypatch):
    source = tmp_path / "large-image.png"
    source.write_bytes(b"image")

    def raise_decompression_bomb(_path):
        raise Image.DecompressionBombError("image too large")

    monkeypatch.setattr(image_extractor.Image, "open", raise_decompression_bomb)

    with pytest.raises(ValueError, match="Invalid image file"):
        image_extractor.extract_image(str(source))


def test_extract_image_returns_empty_ocr_text_when_ocr_fails(
    tmp_path,
    monkeypatch,
):
    source = tmp_path / "requirements.png"
    Image.new("RGB", (20, 20), "white").save(source)

    class FailingOCR:
        def predict(self, _path):
            raise RuntimeError("OCR unavailable")

    monkeypatch.setattr(image_extractor, "ocr", FailingOCR())
    monkeypatch.setattr(image_extractor, "IMAGE_OUTPUT_DIR", tmp_path / "output")

    result = image_extractor.extract_image(str(source))

    assert result["elements"][0]["content"]["ocr_text"] == ""