"""Read-only adapter for an explicitly bound legacy single-user conversation DB.

The old table has no owner/project columns: binding is caller-supplied context,
not authentication or row-level isolation. Never attach a mixed-user DB.
"""
import sqlite3
from pathlib import Path

from core.conversation_memory import (
    ConversationSource, MemoryScope, SourceBatch, checked_text, positive_id,
)


class ConversationSourceReader:
    def __init__(self, database_path, *, dataset_id, scope):
        checked_text(dataset_id, "dataset_id", 128)
        if not isinstance(scope, MemoryScope):
            raise ValueError("scope required")
        self.path = Path(database_path).resolve()
        self.dataset_id = dataset_id
        self.scope = scope

    def _read(self, query, parameters):
        # mode=ro refuses a missing DB and also prevents writes at SQLite level.
        connection = sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True)
        try:
            return connection.execute(query, parameters).fetchall()
        finally:
            connection.close()

    def _source(self, row):
        message_id, role, content, created_at = row
        return ConversationSource.from_row(self.dataset_id, message_id, role, content, created_at)

    def recent(self, limit=20):
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        rows = self._read(
            "SELECT id, role, content, created_at FROM conversations "
            "WHERE role IN ('user', 'assistant') ORDER BY id DESC LIMIT ?", (limit + 1,))
        return SourceBatch(self.scope, self.dataset_id,
                           tuple(self._source(row) for row in reversed(rows[:limit])),
                           has_older=len(rows) > limit)

    def by_ids(self, message_ids):
        ids = tuple(message_ids)
        if len(ids) > 100:
            raise ValueError("at most 100 IDs per read")
        for message_id in ids:
            positive_id(message_id)
        ids = tuple(dict.fromkeys(ids))
        if not ids:
            return SourceBatch(self.scope, self.dataset_id, ())
        placeholders = ",".join("?" for _ in ids)
        rows = self._read(
            "SELECT id, role, content, created_at FROM conversations "
            f"WHERE id IN ({placeholders}) AND role IN ('user', 'assistant') ORDER BY id", ids)
        sources = tuple(self._source(row) for row in rows)
        found = {source.ref.message_id for source in sources}
        return SourceBatch(self.scope, self.dataset_id, sources,
                           missing_ids=tuple(message_id for message_id in ids if message_id not in found))
