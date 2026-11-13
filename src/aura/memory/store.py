"""SQLite persistence engine for long-term user memory and preferences."""

from __future__ import annotations

import logging
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, Optional, Union

from aura.memory.models import MemoryItem

logger = logging.getLogger(__name__)

MAX_MEMORY_CHARS = 500
MAX_CATEGORY_CHARS = 50
MAX_STORED_MEMORIES = 500


def _get_current_utc_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


class MemoryStore:
    """Thread-safe SQLite storage for user facts, preferences, and notes.

    Privacy Guarantees:
        1. Explicit Opt-In: Operations are guarded by `enabled` state. If disabled,
           writing or retrieving memories is blocked unless explicitly enabled.
        2. Full User Control: Complete CRUD operations (list, search, update, delete, clear).
        3. Parameterized SQL: Protects against SQL injection attacks.
        4. Resource Safety: Context-managed connections preventing file locks on Windows.
    """

    def __init__(self, db_path: Union[str, Path], enabled: bool = False) -> None:
        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.enabled = enabled
        self._lock = threading.RLock()
        self._init_schema()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provide an open SQLite connection with guaranteed cleanup."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=10.0,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """Create the memories table and performance indexes if not present."""
        with self._lock, self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'general',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memories_category
                ON memories (category);
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memories_created_at
                ON memories (created_at);
                """
            )
            conn.commit()

    def is_enabled(self) -> bool:
        """Return whether persistent memory is enabled."""
        with self._lock:
            return self.enabled

    def set_enabled(self, enabled: bool) -> None:
        """Explicitly enable or disable the persistent memory system."""
        with self._lock:
            self.enabled = enabled
            logger.info("Memory store enabled set to: %s", enabled)

    def add_memory(self, content: str, category: str = "general") -> MemoryItem:
        """Add a new memory fact to persistent storage.

        Args:
            content: The text content of the fact (1-500 chars).
            category: Optional category tag (default 'general').

        Returns:
            The created MemoryItem.

        Raises:
            ValueError: If memory is disabled or validation fails.
        """
        if not self.is_enabled():
            raise ValueError(
                "Memory system is currently disabled. Use 'memory on' to enable persistent memory."
            )

        trimmed_content = content.strip()
        if not trimmed_content:
            raise ValueError("Memory content cannot be empty.")
        if len(trimmed_content) > MAX_MEMORY_CHARS:
            raise ValueError(
                f"Memory content exceeds maximum length of {MAX_MEMORY_CHARS} characters."
            )

        trimmed_cat = category.strip().lower() or "general"
        if len(trimmed_cat) > MAX_CATEGORY_CHARS:
            trimmed_cat = trimmed_cat[:MAX_CATEGORY_CHARS]

        with self._lock, self._connection() as conn:
            # Capacity check
            cursor = conn.execute("SELECT COUNT(*) FROM memories;")
            count = cursor.fetchone()[0]
            if count >= MAX_STORED_MEMORIES:
                raise ValueError(
                    f"Memory storage limit reached ({MAX_STORED_MEMORIES} facts). "
                    "Please delete older memories before adding new ones."
                )

            now_iso = _get_current_utc_iso()
            cursor = conn.execute(
                """
                INSERT INTO memories (content, category, created_at, updated_at)
                VALUES (?, ?, ?, ?);
                """,
                (trimmed_content, trimmed_cat, now_iso, now_iso),
            )
            memory_id = cursor.lastrowid
            conn.commit()

        logger.info("Saved memory fact #%d [%s]", memory_id, trimmed_cat)
        return MemoryItem(
            id=memory_id,
            content=trimmed_content,
            category=trimmed_cat,
            created_at=now_iso,
            updated_at=now_iso,
        )

    def list_memories(
        self, category: Optional[str] = None, limit: int = 100
    ) -> list[MemoryItem]:
        """List stored memories, optionally filtered by category.

        Args:
            category: Optional category filter.
            limit: Maximum items to return.

        Returns:
            List of MemoryItem objects ordered by creation date descending.
        """
        if not self.is_enabled():
            return []

        query = "SELECT id, content, category, created_at, updated_at FROM memories"
        params: list[Union[str, int]] = []

        if category:
            query += " WHERE category = ?"
            params.append(category.strip().lower())

        query += " ORDER BY id DESC LIMIT ?"
        params.append(max(1, limit))

        with self._lock, self._connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        return [
            MemoryItem(
                id=row["id"],
                content=row["content"],
                category=row["category"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def search_memories(self, search_term: str, limit: int = 20) -> list[MemoryItem]:
        """Search stored memories by keyword/substring in content or category.

        Args:
            search_term: Keyword or phrase to look for.
            limit: Maximum items to return.

        Returns:
            Matching MemoryItem objects.
        """
        if not self.is_enabled():
            return []

        clean_term = search_term.strip()
        if not clean_term:
            return self.list_memories(limit=limit)

        pattern = f"%{clean_term}%"
        with self._lock, self._connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, content, category, created_at, updated_at
                FROM memories
                WHERE content LIKE ? OR category LIKE ?
                ORDER BY id DESC LIMIT ?;
                """,
                (pattern, pattern, max(1, limit)),
            )
            rows = cursor.fetchall()

        return [
            MemoryItem(
                id=row["id"],
                content=row["content"],
                category=row["category"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def get_memory(self, memory_id: int) -> Optional[MemoryItem]:
        """Retrieve a single memory fact by ID."""
        with self._lock, self._connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, content, category, created_at, updated_at
                FROM memories WHERE id = ?;
                """,
                (memory_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return MemoryItem(
            id=row["id"],
            content=row["content"],
            category=row["category"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def update_memory(
        self, memory_id: int, new_content: str, category: Optional[str] = None
    ) -> Optional[MemoryItem]:
        """Update the content and/or category of an existing memory.

        Args:
            memory_id: Target memory ID.
            new_content: Replacement fact content.
            category: Optional replacement category.

        Returns:
            Updated MemoryItem, or None if not found.
        """
        if not self.is_enabled():
            raise ValueError("Memory system is currently disabled.")

        trimmed = new_content.strip()
        if not trimmed:
            raise ValueError("Memory content cannot be empty.")
        if len(trimmed) > MAX_MEMORY_CHARS:
            raise ValueError(
                f"Memory content exceeds maximum length of {MAX_MEMORY_CHARS} characters."
            )

        now_iso = _get_current_utc_iso()

        with self._lock, self._connection() as conn:
            if category:
                trimmed_cat = category.strip().lower()[:MAX_CATEGORY_CHARS]
                cursor = conn.execute(
                    """
                    UPDATE memories
                    SET content = ?, category = ?, updated_at = ?
                    WHERE id = ?;
                    """,
                    (trimmed, trimmed_cat, now_iso, memory_id),
                )
            else:
                cursor = conn.execute(
                    """
                    UPDATE memories
                    SET content = ?, updated_at = ?
                    WHERE id = ?;
                    """,
                    (trimmed, now_iso, memory_id),
                )

            if cursor.rowcount == 0:
                return None
            conn.commit()

        return self.get_memory(memory_id)

    def delete_memory(self, memory_id: int) -> bool:
        """Delete an individual memory fact by ID.

        Returns:
            True if deleted, False if item was not found.
        """
        with self._lock, self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM memories WHERE id = ?;",
                (memory_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def clear_memories(self) -> int:
        """Wipe all stored memories permanently (requires user confirmation at router level).

        Returns:
            Number of deleted memory items.
        """
        with self._lock, self._connection() as conn:
            cursor = conn.execute("DELETE FROM memories;")
            count = cursor.rowcount
            conn.commit()
        logger.info("Cleared all %d memories from store.", count)
        return count

    def get_count(self) -> int:
        """Return total count of stored memory items."""
        with self._lock, self._connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM memories;")
            return cursor.fetchone()[0]

