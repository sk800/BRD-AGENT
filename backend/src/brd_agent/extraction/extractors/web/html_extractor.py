from pathlib import Path
from uuid import uuid4

from bs4 import BeautifulSoup


def _id():
    return f"e_{uuid4().hex[:10]}"


def _clean(text):
    return " ".join(text.split())


def extract_html(file_path: str) -> dict:
    path = Path(file_path)

    html = path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    elements = []

    for tag in soup.find_all(
        ["h1", "h2", "h3", "h4", "h5", "h6",
         "p", "li", "table"]
    ):
        text = _clean(tag.get_text(" ", strip=True))

        if not text:
            continue

        element_id = _id()

        if tag.name.startswith("h"):
            element_type = "heading"

        elif tag.name == "li":
            element_type = "list"

        elif tag.name == "table":
            rows = []

            for row in tag.find_all("tr"):
                cells = [
                    _clean(cell.get_text(" ", strip=True))
                    for cell in row.find_all(["th", "td"])
                ]

                if cells:
                    rows.append(cells)

            if not rows:
                continue

            elements.append({
                "element_id": element_id,
                "type": "table",
                "content": {
                    "headers": rows[0],
                    "rows": rows[1:],
                },
                "location": {
                    "order": len(elements) + 1,
                },
                "citation": {
                    "element_id": element_id,
                },
            })

            continue

        else:
            element_type = "paragraph"

        elements.append({
            "element_id": element_id,
            "type": element_type,
            "content": text,
            "location": {
                "order": len(elements) + 1,
            },
        })

    return {
        "document": {
            "document_id": f"doc_{uuid4().hex[:10]}",
            "filename": path.name,
            "file_type": "html",
        },
        "elements": elements,
    }