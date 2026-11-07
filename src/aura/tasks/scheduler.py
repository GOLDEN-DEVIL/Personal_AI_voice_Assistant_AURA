"""Background scheduler daemon for polling and triggering due reminders."""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Optional

from aura.tasks.db import TaskDatabase
from aura.tasks.models import Reminder

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """Lightweight background thread that checks for due reminders and dispatches notifications."""

    def __init__(
        self,
        db: TaskDatabase,
        notification_callback: Optional[Callable[[Reminder], None]] = None,
        check_interval_seconds: float = 2.0,
    ) -> None:
        self.db = db
        self.notification_callback = notification_callback
        self.check_interval = check_interval_seconds
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the background reminder polling thread."""
        if self._thread and self._thread.is_alive():
            logger.debug("ReminderScheduler thread is already running.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="AuraReminderScheduler",
            daemon=True,
        )
        self._thread.start()
        logger.info("ReminderScheduler started (poll interval: %.1fs).", self.check_interval)

    def stop(self, timeout: float = 3.0) -> None:
        """Signal the background thread to stop and wait for termination."""
        if not self._thread or not self._thread.is_alive():
            return

        self._stop_event.set()
        self._thread.join(timeout=timeout)
        logger.info("ReminderScheduler stopped.")

    def is_running(self) -> bool:
        """Return True if background scheduler thread is active."""
        return bool(self._thread and self._thread.is_alive())

    def check_now(self) -> list[Reminder]:
        """Manually trigger a check for due reminders (useful for synchronous testing)."""
        return self._poll_and_dispatch()

    def _run_loop(self) -> None:
        """Internal daemon loop polling the database at regular intervals."""
        while not self._stop_event.is_set():
            try:
                self._poll_and_dispatch()
            except Exception as exc:
                logger.error("Error during reminder polling loop: %s", exc)

            # Sleep in short increments to allow rapid thread shutdown
            self._stop_event.wait(timeout=self.check_interval)

    def _poll_and_dispatch(self) -> list[Reminder]:
        """Query due reminders, mark them fired, and invoke notification callback."""
        due_reminders = self.db.get_due_reminders()
        dispatched: list[Reminder] = []

        for r in due_reminders:
            if r.id is None:
                continue

            # Atomically mark as fired to prevent duplicate alerts
            if self.db.mark_reminder_fired(r.id):
                dispatched.append(r)
                if self.notification_callback:
                    try:
                        self.notification_callback(r)
                    except Exception as err:
                        logger.error("Error in reminder notification callback: %s", err)

        return dispatched

