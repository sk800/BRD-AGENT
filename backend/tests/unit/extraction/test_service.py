from pathlib import Path

import pytest

from brd_agent.extraction.gateway import extract_file, extract_path


def test_extract_text_file_returns_canonical_document(tmp_path: Path) -> None:
    source = tmp_path / "requirements.txt"
    source.write_text("Project scope\n\nThe system shall import documents.", encoding="utf-8")

    result = extract_file(source)

    assert result["document"]["file_type"] == "txt"
    assert result["elements"][0]["type"] == "paragraph"
    assert any("import documents" in element["content"] for element in result["elements"])


def test_extract_path_reads_supported_text_files(tmp_path: Path) -> None:
    (tmp_path / "one.md").write_text("One", encoding="utf-8")
    (tmp_path / "two.json").write_text('{"name": "Two"}', encoding="utf-8")

    results = extract_path(tmp_path)

    assert [item["document"]["filename"] for item in results] == ["one.md", "two.json"]


def test_extract_file_rejects_unknown_types(tmp_path: Path) -> None:
    source = tmp_path / "requirements.xyz"
    source.write_text("unsupported", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_file(source)


def test_extract_file_routes_email_to_email_extractor(tmp_path: Path) -> None:
    source = tmp_path / "requirements.eml"
    source.write_text(
        "From: product@example.com\n"
        "To: team@example.com\n"
        "Subject: Requirements\n\n"
        "The system shall support document uploads.\n",
        encoding="utf-8",
    )

    result = extract_file(source)

    assert result["document"]["file_type"] == "eml"
    assert len(result["elements"]) == 2
    assert result["elements"][0]["content"]["Subject"] == "Requirements"
    assert "document uploads" in result["elements"][1]["content"]


def test_extract_file_routes_delimited_spreadsheets(tmp_path: Path) -> None:
    csv_source = tmp_path / "requirements.csv"
    csv_source.write_text("Name,Priority\nUploads,High\n", encoding="utf-8")

    tsv_source = tmp_path / "requirements.tsv"
    tsv_source.write_text("Name\tPriority\nUploads\tHigh\n", encoding="utf-8")

    csv_result = extract_file(csv_source)
    tsv_result = extract_file(tsv_source)

    assert csv_result["elements"][0]["content"] == {
        "headers": ["Name", "Priority"],
        "rows": [["Uploads", "High"]],
    }
    assert tsv_result["elements"][0]["content"] == {
        "headers": ["Name", "Priority"],
        "rows": [["Uploads", "High"]],
    }