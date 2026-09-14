
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Any
from uuid import uuid4


def _id():
    return f"e_{uuid4().hex[:10]}"


def extract_email(path: Path) -> list[dict[str, Any]]:
    with path.open("rb") as file:
        message = BytesParser(policy=policy.default).parse(file)

    elements = []

    # Email headers
    headers = {
        name: message.get(name)
        for name in ("From", "To", "Date", "Subject")
        if message.get(name)
    }

    if headers:
        elements.append({
            "element_id": _id(),
            "type": "email_headers",
            "content": headers,
            "location": {
                "order": len(elements) + 1
            },
        })

    # Email body
    plain_parts = []

    for part in message.walk():
        if (
            part.get_content_type() == "text/plain"
            and not part.get_filename()
        ):
            text = part.get_content().strip()

            if text:
                plain_parts.append(text)

    body = "\n\n".join(plain_parts)

    if body:
        elements.append({
            "element_id": _id(),
            "type": "paragraph",
            "content": body,
            "location": {
                "order": len(elements) + 1
            },
        })

    return elements


