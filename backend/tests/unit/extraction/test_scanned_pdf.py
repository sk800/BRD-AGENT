import fitz

from brd_agent.extraction.extractors.pdf import scanned_pdf


class FakePipeline:
	def predict(self, _path):
		return [{
			"res": {
				"parsing_res_list": [{
					"block_label": "text",
					"block_bbox": [0, 0, 100, 40],
					"block_content": "Scanned requirement",
				}],
			}
		}]


def test_extract_scanned_pdf_uses_pipeline_and_returns_page_metadata(tmp_path, monkeypatch):
	source = tmp_path / "scanned.pdf"
	document = fitz.open()
	document.new_page()
	document.save(source)
	document.close()
	monkeypatch.setattr(scanned_pdf, "pipeline", FakePipeline())
	monkeypatch.setattr(scanned_pdf, "OUTPUT_DIR", tmp_path / "output")
	(tmp_path / "output").mkdir()

	result = scanned_pdf.extract_scanned_pdf(str(source))

	assert result["document"]["page_count"] == 1
	assert result["elements"][0]["type"] == "paragraph"
	assert result["elements"][0]["content"] == "Scanned requirement"
	assert result["elements"][0]["location"]["page"] == 1
