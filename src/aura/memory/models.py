"""Data models for persistent memory and short-term conversation context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MemoryItem:
    """An individual persistent fact remembered by AURA.

    Attributes:
        id: Unique database primary key.
        content: The text content of the saved memory fact.
        category: Logical grouping/tag (e.g. 'general', 'preference', 'project', 'profile').
        created_at: ISO 8601 UTC timestamp of creation.
        updated_at: ISO 8601 UTC timestamp of last update.
    """

    id: int
    content: str
    category: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class DialogueTurn:
    """An ephemeral dialogue turn in the current conversation session.

    Kept exclusively in RAM ring buffers for conversational coherence;
    NEVER written to disk.

    Attributes:
        user_query: The cleaned user query.
        assistant_response: The assistant's generated response.
        timestamp: ISO 8601 UTC timestamp.
    """

    user_query: str
    assistant_response: str
    timestamp: str

