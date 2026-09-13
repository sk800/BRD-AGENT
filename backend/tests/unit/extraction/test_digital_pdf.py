import fitz

from brd_agent.extraction.extractors.pdf import digital_pdf


def test_extract_digital_pdf_returns_text_and_page_metadata(
    tmp_path,
):
    source = tmp_path / "requirements.pdf"

    document = fitz.open()
    page = document.new_page()
    page.insert_text(
        (72, 72),
        "The system shall support document uploads.",
    )
    document.save(source)
    document.close()

    result = digital_pdf.extract_digital_pdf(
        str(source)
    )

    assert result["document"]["file_type"] == "pdf"
    assert result["document"]["page_count"] == 1

    assert result["elements"][0]["type"] == "paragraph"
    assert "document uploads" in result["elements"][0]["content"]

    assert result["elements"][0]["location"]["page"] == 1
    assert "bbox" in result["elements"][0]["location"]