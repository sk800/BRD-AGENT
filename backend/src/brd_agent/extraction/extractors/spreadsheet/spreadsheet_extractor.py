
from pathlib import Path
from uuid import uuid4

import pandas as pd


def _id():
    return f"e_{uuid4().hex[:10]}"


def _clean(value):
    return "" if pd.isna(value) else str(value).strip()


def _table(dataframe, sheet=None):
    element_id = _id()

    return {
        "element_id": element_id,
        "type": "table",
        "content": {
            "headers": [str(column) for column in dataframe.columns],
            "rows": [
                [_clean(value) for value in row]
                for row in dataframe.values.tolist()
            ],
            **({"sheet": sheet} if sheet else {}),
        },
        "location": {
            **({"sheet": sheet} if sheet else {}),
            "order": 1,
        },
        "citation": {
            **({"sheet": sheet} if sheet else {}),
            "element_id": element_id,
        },
    }


def extract_spreadsheet(file_path: str) -> dict:
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".csv":
        dataframe = pd.read_csv(path)
        elements = [_table(dataframe)]

    elif extension == ".tsv":
        dataframe = pd.read_csv(path, sep="\t")
        elements = [_table(dataframe)]

    else:
        excel = pd.ExcelFile(path)
        elements = []

        for sheet in excel.sheet_names:
            dataframe = pd.read_excel(
                path,
                sheet_name=sheet,
            )

            element = _table(dataframe, sheet)
            element["location"]["order"] = len(elements) + 1
            elements.append(element)

    return {
        "document": {
            "document_id": f"doc_{uuid4().hex[:10]}",
            "filename": path.name,
            "file_type": extension.lstrip("."),
        },
        "elements": elements,
    }

