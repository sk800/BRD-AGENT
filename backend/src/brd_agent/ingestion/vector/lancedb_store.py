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

    def delete_obsolete_file_chunks(
        self,
        *,
        user_id: str,
        content_sha256: str,
        pipeline_version: str,
    ) -> int:
        """Remove superseded vectors for this file after its new vectors are stored."""

        if TABLE_NAME not in self._db.table_names():
            return 0

        table = self._db.open_table(TABLE_NAME)
        user = user_id.replace("'", "''")
        fingerprint = content_sha256.replace("'", "''")
        version = pipeline_version.replace("'", "''")
        predicate = (
            f"user_id = '{user}' AND content_sha256 = '{fingerprint}' "
            f"AND pipeline_version != '{version}'"
        )
        count = table.count_rows(filter=predicate)
        if count:
            table.delete(predicate)
            logger.info(
                "Deleted %s obsolete LanceDB rows for user=%s file=%s",
                count,
                user_id,
                content_sha256[:12],
            )
        return count

    def reassociate_conversation(
        self,
        *,
        user_id: str,
        content_sha256: str,
        conversation_id: str,
        message_id: str,
        attachment_id: str,
    ) -> int:
        """Point existing vectors at a new conversation (same file re-uploaded)."""

        if TABLE_NAME not in self._db.table_names():
            return 0

        table = self._db.open_table(TABLE_NAME)
        df = table.to_pandas()
        mask = (df["user_id"] == user_id) & (df["content_sha256"] == content_sha256)
        subset = df.loc[mask]
        if subset.empty:
            return 0

        rows: list[dict[str, Any]] = []
        for record in subset.to_dict(orient="records"):
            rows.append(
                {
                    **record,
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "attachment_id": attachment_id,
                }
            )

        count = self.upsert_chunks(rows)
        logger.info(
            "Reassociated %s LanceDB rows for user=%s file=%s → conversation=%s",
            count,
            user_id,
            content_sha256[:12],
            conversation_id,
        )
        return count
