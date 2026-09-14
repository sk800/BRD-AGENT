from brd_agent.extraction.extractors.web.html_extractor import extract_html


def test_extract_html_returns_headings_paragraphs_and_lists(tmp_path):
    source = tmp_path / "requirements.html"

    source.write_text(
        "<html><body>"
        "<h1>Requirements</h1>"
        "<p>The system shall import files.</p>"
        "<ul><li>PDF</li><li>DOCX</li></ul>"
        "</body></html>",
        encoding="utf-8",
    )

    result = extract_html(str(source))

    assert result["document"]["file_type"] == "html"

    assert [element["type"] for element in result["elements"]] == [
        "heading",
        "paragraph",
        "list",
        "list",
    ]

    assert result["elements"][0]["content"] == "Requirements"
    assert result["elements"][1]["content"] == "The system shall import files."