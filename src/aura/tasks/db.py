"""SQLite persistence engine for tasks and timed reminders."""

from __future__ import annotations

import logging
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, Optional, Union

from aura.tasks.models import (
    Reminder,
    Task,
    VALID_PRIORITIES,
    VALID_REMINDER_STATUSES,
    VALID_TASK_STATUSES,
)

logger = logging.getLogger(__name__)

MAX_TITLE_CHARS = 300
MAX_MESSAGE_CHARS = 300


def _get_current_utc_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


class TaskDatabase:
    """Thread-safe SQLite database manager for AURA tasks and reminders."""

    def __init__(self, db_path: Union[str, Path]) -> None:
        self.db_path = Path(db_path).resolve()
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_schema()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager providing an open SQLite connection with guaranteed cleanup."""
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
        """Initialize database tables and performance indices if not present."""
        with self._lock, self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    priority TEXT NOT NULL DEFAULT 'medium',
                    due_date TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    remind_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'scheduled',
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_reminders_status_remind_at "
                "ON reminders(status, remind_at);"
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # Task Operations
    # -----------------------------------------------------------------------

    def add_task(
        self,
        title: str,
        priority: str = "medium",
        due_date: Optional[str] = None,
    ) -> Task:
        """Add a new task to the database.

        Args:
            title: Description of the task.
            priority: 'low', 'medium', or 'high'.
            due_date: Optional deadline string.

        Returns:
            The created Task object with assigned ID.

        Raises:
            ValueError: If title is empty or arguments are invalid.
        """
        clean_title = (title or "").strip()
        if not clean_title:
            raise ValueError("Task title cannot be empty.")
        if len(clean_title) > MAX_TITLE_CHARS:
            clean_title = clean_title[:MAX_TITLE_CHARS].rstrip()

        norm_priority = (priority or "medium").lower().strip()
        if norm_priority not in VALID_PRIORITIES:
            norm_priority = "medium"

        now_iso = _get_current_utc_iso()

        with self._lock, self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tasks (title, status, priority, due_date, created_at, updated_at)
                VALUES (?, 'pending', ?, ?, ?, ?);
                """,
                (clean_title, norm_priority, due_date, now_iso, now_iso),
            )
            conn.commit()
            task_id = cursor.lastrowid

        return Task(
            id=task_id,
            title=clean_title,
            status="pending",
            priority=norm_priority,
            due_date=due_date,
            created_at=now_iso,
            updated_at=now_iso,
        )

    def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> list[Task]:
        """List tasks, optionally filtered by status and/or priority.

        Args:
            status: Filter by 'pending', 'completed', etc.
            priority: Filter by 'low', 'medium', 'high'.

        Returns:
            List of matching Task instances.
        """
        query = "SELECT id, title, status, priority, due_date, created_at, updated_at FROM tasks WHERE 1=1"
        params: list[str] = []

        if status:
            norm_status = status.lower().strip()
            if norm_status in VALID_TASK_STATUSES:
                query += " AND status = ?"
                params.append(norm_status)

        if priority:
            norm_prio = priority.lower().strip()
            if norm_prio in VALID_PRIORITIES:
                query += " AND priority = ?"
                params.append(norm_prio)

        query += " ORDER BY CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END, id ASC;"

        with self._lock, self._connection() as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            Task(
                id=row["id"],
                title=row["title"],
                status=row["status"],
                priority=row["priority"],
                due_date=row["due_date"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def get_task(self, task_id: int) -> Optional[Task]:
        """Retrieve a specific task by its ID."""
        with self._lock, self._connection() as conn:
            row = conn.execute(
                "SELECT id, title, status, priority, due_date, created_at, updated_at "
                "FROM tasks WHERE id = ?;",
                (task_id,),
            ).fetchone()

        if not row:
            return None

        return Task(
            id=row["id"],
            title=row["title"],
            status=row["status"],
            priority=row["priority"],
            due_date=row["due_date"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def complete_task(self, task_id: int) -> bool:
        """Mark a task as completed.

        Returns:
            True if task was updated, False if task_id does not exist.
        """
        now_iso = _get_current_utc_iso()
        with self._lock, self._connection() as conn:
            cursor = conn.execute(
                "UPDATE tasks SET status = 'completed', updated_at = ? "
                "WHERE id = ? AND status != 'completed';",
                (now_iso, task_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_task(self, task_id: int) -> bool:
        """Permanently delete a task by ID.

        Returns:
            True if deleted, False if task_id not found.
        """
        with self._lock, self._connection() as conn:
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?;", (task_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear_completed_tasks(self) -> int:
        """Remove all completed tasks from the database.

        Returns:
            Number of rows deleted.
        """
        with self._lock, self._connection() as conn:
            cursor = conn.execute("DELETE FROM tasks WHERE status = 'completed';")
            conn.commit()
            return cursor.rowcount

    # -----------------------------------------------------------------------
    # Reminder Operations
    # -----------------------------------------------------------------------

    def add_reminder(self, message: str, remind_at_iso: str) -> Reminder:
        """Schedule a new reminder.

        Args:
            message: The reminder text.
            remind_at_iso: ISO 8601 formatted datetime string.

        Returns:
            The created Reminder object with assigned ID.

        Raises:
            ValueError: If message or remind_at is invalid.
        """
        clean_msg = (message or "").strip()
        if not clean_msg:
            raise ValueError("Reminder message cannot be empty.")
        if len(clean_msg) > MAX_MESSAGE_CHARS:
            clean_msg = clean_msg[:MAX_MESSAGE_CHARS].rstrip()

        now_iso = _get_current_utc_iso()

        with self._lock, self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO reminders (message, remind_at, status, created_at)
                VALUES (?, ?, 'scheduled', ?);
                """,
                (clean_msg, remind_at_iso, now_iso),
            )
            conn.commit()
            reminder_id = cursor.lastrowid

        return Reminder(
            id=reminder_id,
            message=clean_msg,
            remind_at=remind_at_iso,
            status="scheduled",
            created_at=now_iso,
        )

    def get_due_reminders(self, current_iso: Optional[str] = None) -> list[Reminder]:
        """Fetch all scheduled reminders whose trigger time is <= current_iso.

        Args:
            current_iso: ISO timestamp string (defaults to current UTC time).

        Returns:
            List of due Reminder objects.
        """
        now_iso = current_iso or _get_current_utc_iso()

        with self._lock, self._connection() as conn:
            rows = conn.execute(
                """
                SELECT id, message, remind_at, status, created_at
                FROM reminders
                WHERE status = 'scheduled' AND remind_at <= ?
                ORDER BY remind_at ASC;
                """,
                (now_iso,),
            ).fetchall()

        return [
            Reminder(
                id=row["id"],
                message=row["message"],
                remind_at=row["remind_at"],
                status=row["status"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def mark_reminder_fired(self, reminder_id: int) -> bool:
        """Mark a reminder as fired.

        Returns:
            True if updated, False if reminder_id not found or not scheduled.
        """
        with self._lock, self._connection() as conn:
            cursor = conn.execute(
                "UPDATE reminders SET status = 'fired' WHERE id = ? AND status = 'scheduled';",
                (reminder_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def list_reminders(self, status: Optional[str] = None) -> list[Reminder]:
        """List reminders, optionally filtered by status ('scheduled', 'fired', 'cancelled')."""
        query = "SELECT id, message, remind_at, status, created_at FROM reminders WHERE 1=1"
        params: list[str] = []

        if status:
            norm_status = status.lower().strip()
            if norm_status in VALID_REMINDER_STATUSES:
                query += " AND status = ?"
                params.append(norm_status)

        query += " ORDER BY remind_at ASC;"

        with self._lock, self._connection() as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            Reminder(
                id=row["id"],
                message=row["message"],
                remind_at=row["remind_at"],
                status=row["status"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def cancel_reminder(self, reminder_id: int) -> bool:
        """Cancel a scheduled reminder.

        Returns:
            True if cancelled, False if not found or already fired/cancelled.
        """
        with self._lock, self._connection() as conn:
            cursor = conn.execute(
                "UPDATE reminders SET status = 'cancelled' WHERE id = ? AND status = 'scheduled';",
                (reminder_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
