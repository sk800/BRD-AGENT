import asyncio
import re
import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from brd_agent.core.config import get_settings
from brd_agent.core.exceptions import ChatError
from brd_agent.domain.models.chat import AttachmentInDB

settings = get_settings()


def sanitize_filename(filename: str) -> str:
    cleaned = Path(filename).name
    cleaned = re.sub(r"[^\w.\-]", "_", cleaned)
    return cleaned or "file"


class FileStorageService:
    def __init__(self) -> None:
        self._upload_root = Path(settings.upload_dir)

    async def ensure_upload_dir(self) -> None:
        await asyncio.to_thread(self._upload_root.mkdir, parents=True, exist_ok=True)

    async def save_files(
        self,
        user_id: str,
        files: list[UploadFile],
    ) -> list[AttachmentInDB]:
        if len(files) > settings.max_files_per_message:
            raise ChatError(
                f"Maximum {settings.max_files_per_message} files allowed per message",
                status_code=400,
            )

        user_dir = self._upload_root / user_id
        await asyncio.to_thread(user_dir.mkdir, parents=True, exist_ok=True)

        attachments: list[AttachmentInDB] = []
        max_bytes = settings.max_file_size_mb * 1024 * 1024

        for upload in files:
            if not upload.filename:
                raise ChatError("Uploaded file must have a filename", status_code=400)

            content = await upload.read()
            if not content:
                raise ChatError(f"File '{upload.filename}' is empty", status_code=400)

            if len(content) > max_bytes:
                raise ChatError(
                    f"File '{upload.filename}' exceeds {settings.max_file_size_mb}MB limit",
                    status_code=400,
                )

            file_id = str(uuid.uuid4())
            safe_name = sanitize_filename(upload.filename)
            stored_filename = f"{file_id}_{safe_name}"
            storage_path = user_dir / stored_filename

            async with aiofiles.open(storage_path, "wb") as file_handle:
                await file_handle.write(content)

            attachments.append(
                AttachmentInDB(
                    id=file_id,
                    filename=stored_filename,
                    original_filename=upload.filename,
                    mime_type=upload.content_type or "application/octet-stream",
                    size_bytes=len(content),
                    storage_path=str(storage_path),
                )
            )

            await upload.close()

        return attachments
