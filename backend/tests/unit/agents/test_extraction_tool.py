from pathlib import Path

from brd_agent.agents.tools.extraction_tools import extract_document


def test_extract_document_tool_routes_to_gateway(tmp_path: Path):
    source = tmp_path / "notes.txt"
    source.write_text("Requirement one\n\nRequirement two", encoding="utf-8")

    result = extract_document.invoke({"file_path": str(source)})

    assert result["document"]["filename"] == "notes.txt"
    assert len(result["elements"]) == 2
    assert result["elements"][0]["content"] == "Requirement one"
