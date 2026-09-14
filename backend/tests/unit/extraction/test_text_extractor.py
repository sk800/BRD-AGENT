from brd_agent.extraction.extractors.text.text_extractor import extract_text


def test_extract_text_preserves_paragraphs_and_markdown_headings(tmp_path):
	source = tmp_path / "requirements.md"
	source.write_text("# Scope\n\nThe system shall import files.", encoding="utf-8")

	result = extract_text(str(source))

	assert result["document"]["filename"] == "requirements.md"
	assert [element["type"] for element in result["elements"]] == ["heading", "paragraph"]
	assert result["elements"][1]["content"] == "The system shall import files."


def test_extract_text_replaces_invalid_bytes(tmp_path):
	source = tmp_path / "notes.txt"
	source.write_bytes(b"valid\xfftext")

	result = extract_text(str(source))

	assert result["elements"][0]["content"] == "valid\ufffdtext"
