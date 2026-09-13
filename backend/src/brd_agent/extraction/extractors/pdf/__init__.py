from pathlib import Path

from brd_agent.extraction.extractors.pdf.digital_pdf import extract_digital_pdf
from brd_agent.extraction.extractors.pdf.scanned_pdf import extract_scanned_pdf


def extract_pdf(file_path: str | Path) -> dict:
	import fitz

	with fitz.open(file_path) as pdf:
		is_digital = any(page.get_text("text").strip() for page in pdf)
	extractor = extract_digital_pdf if is_digital else extract_scanned_pdf
	return extractor(str(file_path))

__all__ = ["extract_pdf"]
