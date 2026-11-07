"""Data models for persistent tasks and reminders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

VALID_PRIORITIES = frozenset({"low", "medium", "high"})
VALID_TASK_STATUSES = frozenset({"pending", "completed", "cancelled"})
VALID_REMINDER_STATUSES = frozenset({"scheduled", "fired", "cancelled"})


@dataclass(frozen=True)
class Task:
    """Represents a persistent to-do task item.

    Attributes:
        id: Unique numeric database identifier.
        title: Description of the task.
        status: Current state ('pending', 'completed', 'cancelled').
        priority: Priority tier ('low', 'medium', 'high').
        due_date: Optional ISO date/time string for task deadline.
        created_at: ISO timestamp of creation.
        updated_at: ISO timestamp of last status update.
    """

    id: Optional[int]
    title: str
    status: str = "pending"
    priority: str = "medium"
    due_date: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


@dataclass(frozen=True)
class Reminder:
    """Represents a scheduled timed reminder.

    Attributes:
        id: Unique numeric database identifier.
        message: The reminder notice or instruction.
        remind_at: ISO 8601 timestamp when the reminder is due to fire.
        status: Current state ('scheduled', 'fired', 'cancelled').
        created_at: ISO timestamp of creation.
    """

    id: Optional[int]
    message: str
    remind_at: str
    status: str = "scheduled"
    created_at: str = ""

