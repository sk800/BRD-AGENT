from pathlib import Path

from brd_agent.extraction.extractors.email.extractor import extract_email


def test_extract_email_returns_headers_and_body(tmp_path: Path):
    source = tmp_path / "requirements.eml"

    source.write_text(
        "From: product@example.com\n"
        "To: team@example.com\n"
        "Subject: Requirements\n\n"
        "The system shall support document uploads.\n",
        encoding="utf-8",
    )

    result = extract_email(source)

    assert len(result) == 2

    assert result[0]["type"] == "email_headers"
    assert result[0]["content"]["Subject"] == "Requirements"

    assert result[1]["type"] == "paragraph"
    assert "document uploads" in result[1]["content"]