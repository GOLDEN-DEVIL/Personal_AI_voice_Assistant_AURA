"""Basic informational tools: time, date, and help."""

from __future__ import annotations

import datetime


def get_current_time() -> str:
    """Return the current local time with timezone info."""
    now = datetime.datetime.now().astimezone()
    return f"Current local time: {now.strftime('%I:%M:%S %p %Z')}"


def get_current_date() -> str:
    """Return the current local date."""
    now = datetime.datetime.now().astimezone()
    return f"Today's date: {now.strftime('%A, %B %d, %Y')}"


def format_help(commands: dict[str, str]) -> str:
    """Format available commands into a structured help message."""
    lines = [
        "================ Project AURA Commands ================",
        "Available commands:",
    ]
    for cmd, desc in commands.items():
        lines.append(f"  {cmd:<22} : {desc}")
    lines.append("------------------------------------------------------")
    lines.append("Type 'exit', 'quit', or 'bye' to close AURA.")
    lines.append("======================================================")
    return "\n".join(lines)
