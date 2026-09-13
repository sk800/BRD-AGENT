import pandas as pd

from brd_agent.extraction.extractors.spreadsheet.spreadsheet_extractor import (
	extract_spreadsheet,
)


def test_extract_spreadsheet_supports_csv_and_tsv(tmp_path):
	for suffix, content in ((".csv", "Name,Priority\nUpload,High\n"), (".tsv", "Name\tPriority\nUpload\tHigh\n")):
		source = tmp_path / f"requirements{suffix}"
		source.write_text(content, encoding="utf-8")

		result = extract_spreadsheet(str(source))

		assert result["elements"][0]["content"]["headers"] == ["Name", "Priority"]
		assert result["elements"][0]["content"]["rows"] == [["Upload", "High"]]


def test_extract_spreadsheet_returns_one_table_per_excel_sheet(tmp_path):
	source = tmp_path / "requirements.xlsx"
	with pd.ExcelWriter(source) as writer:
		pd.DataFrame({"Name": ["Upload"]}).to_excel(writer, sheet_name="Scope", index=False)
		pd.DataFrame({"Priority": ["High"]}).to_excel(writer, sheet_name="Rules", index=False)

	result = extract_spreadsheet(str(source))

	assert [element["content"]["sheet"] for element in result["elements"]] == ["Scope", "Rules"]
