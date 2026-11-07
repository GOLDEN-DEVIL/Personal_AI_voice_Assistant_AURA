"""Display formatting helpers for tasks and reminders in the CLI REPL."""

from __future__ import annotations

from typing import Optional

from aura.tasks.models import Reminder, Task


def format_tasks_list(tasks: list[Task], filter_name: Optional[str] = None) -> str:
    """Format a list of tasks into a structured, human-readable terminal table.

    Args:
        tasks: List of Task objects.
        filter_name: Optional filter label like 'pending', 'completed'.

    Returns:
        Formatted multi-line text string.
    """
    if not tasks:
        label = f" ({filter_name})" if filter_name else ""
        return f"No tasks found{label}. Use 'task add <title>' to create one."

    pending_count = sum(1 for t in tasks if t.status == "pending")
    completed_count = sum(1 for t in tasks if t.status == "completed")

    header_label = f"Tasks ({filter_name.title()})" if filter_name else f"Tasks ({pending_count} pending, {completed_count} completed)"
    lines = [
        header_label,
        "-" * 58,
    ]

    for t in tasks:
        prio_tag = f"[{t.priority.upper():^6}]"
        status_icon = "[DONE]" if t.status == "completed" else "[TODO]"
        due_str = f" (due: {t.due_date})" if t.due_date else ""
        lines.append(f"[#{t.id}] {status_icon} {prio_tag} {t.title}{due_str}")

    lines.append("-" * 58)
    lines.append("Commands: 'task add <title>', 'task done <id>', 'task delete <id>'")
    return "\n".join(lines)


def format_reminders_list(reminders: list[Reminder], filter_name: Optional[str] = None) -> str:
    """Format a list of reminders into a structured, human-readable terminal table.

    Args:
        reminders: List of Reminder objects.
        filter_name: Optional filter label like 'scheduled', 'fired'.

    Returns:
        Formatted multi-line text string.
    """
    if not reminders:
        label = f" ({filter_name})" if filter_name else ""
        return f"No reminders found{label}. Use 'remind <when> to <message>' to set one."

    lines = [
        f"Reminders ({len(reminders)} total)",
        "-" * 58,
    ]

    for r in reminders:
        status_tag = f"[{r.status.upper()}]"
        # Format the remind_at string for clean display
        time_display = r.remind_at.replace("T", " ")[:16]
        lines.append(f"[#{r.id}] {status_tag} At {time_display}: {r.message}")

    lines.append("-" * 58)
    lines.append("Commands: 'remind <when> to <message>', 'reminder cancel <id>'")
    return "\n".join(lines)

