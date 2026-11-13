"""Short-term conversational context manager for multi-turn dialogue."""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Optional

from aura.memory.models import DialogueTurn

logger = logging.getLogger(__name__)

DEFAULT_MAX_TURNS = 6
MAX_CHARS_PER_TURN = 500


def _get_current_utc_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


class ConversationContext:
    """In-memory, session-scoped dialogue history ring buffer.

    Privacy & Operational Guarantees:
        1. Volatile RAM Only: Turns are held in a Python list in memory and are
           never written to SQLite or file storage.
        2. Session Scoped: Cleared upon application exit or via `memory session clear`.
        3. Strictly Bounded: Retains only the most recent `max_turns` interactions
           to keep LLM prompt token footprints minimal and avoid context pollution.
        4. Thread-Safe: Protected by `threading.RLock`.
    """

    def __init__(self, max_turns: int = DEFAULT_MAX_TURNS) -> None:
        self.max_turns = max(1, min(20, max_turns))
        self._turns: list[DialogueTurn] = []
        self._lock = threading.RLock()

    def add_turn(self, user_query: str, assistant_response: str) -> None:
        """Record an interaction turn in the session ring buffer.

        Args:
            user_query: The user prompt or question.
            assistant_response: The assistant's answer.
        """
        clean_user = user_query.strip()[:MAX_CHARS_PER_TURN]
        clean_resp = assistant_response.strip()[:MAX_CHARS_PER_TURN]

        if not clean_user or not clean_resp:
            return

        turn = DialogueTurn(
            user_query=clean_user,
            assistant_response=clean_resp,
            timestamp=_get_current_utc_iso(),
        )

        with self._lock:
            self._turns.append(turn)
            # Enforce ring buffer bounded capacity
            if len(self._turns) > self.max_turns:
                self._turns = self._turns[-self.max_turns :]

    def get_recent_turns(self) -> list[DialogueTurn]:
        """Return a copy of recent dialogue turns in chronological order."""
        with self._lock:
            return list(self._turns)

    def get_turn_count(self) -> int:
        """Return the number of active dialogue turns currently in session memory."""
        with self._lock:
            return len(self._turns)

    def clear(self) -> int:
        """Clear all session dialogue turns.

        Returns:
            Number of cleared turns.
        """
        with self._lock:
            count = len(self._turns)
            self._turns.clear()
            logger.info("Cleared %d session dialogue turns from volatile memory.", count)
            return count

