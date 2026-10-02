"""LanceDB storage for chunk embeddings."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import lancedb

from brd_agent.core.config import get_settings

logger = logging.getLogger(__name__)

TABLE_NAME = "document_chunks"


class LanceChunkStore:
    def __init__(self, db_path: str | None = None) -> None:
        settings = get_settings()
        path = Path(db_path or settings.lance_db_path)
        path.mkdir(parents=True, exist_ok=True)
        self._db = lancedb.connect(str(path))

    def upsert_chunks(self, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0

        now = datetime.now(UTC).isoformat()
        for row in rows:
            row.setdefault("updated_at", now)

        if TABLE_NAME not in self._db.table_names():
            self._db.create_table(TABLE_NAME, data=rows)
            logger.info("Created LanceDB table %s with %s rows", TABLE_NAME, len(rows))
            return len(rows)

        table = self._db.open_table(TABLE_NAME)
        table.merge_insert("vector_id").when_matched_update_all().when_not_matched_insert_all().execute(
            rows
        )
        logger.info("Upserted %s rows into LanceDB table %s", len(rows), TABLE_NAME)
        return len(rows)
