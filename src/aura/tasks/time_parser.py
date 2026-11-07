"""Natural time parsing utilities for scheduling reminders and deadlines."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple


def parse_time_expression(
    expr: str,
    base_time: Optional[datetime] = None,
) -> Optional[datetime]:
    """Parse a relative or absolute time expression into a timezone-aware UTC datetime.

    Supports:
        - Relative: 'in 5m', 'in 10 minutes', 'in 2h', 'in 1 hour 30m', 'in 45 seconds', 'in 1 day'
        - Time of day: 'at 15:30', 'at 3pm', 'at 9:30am' (rolls over to tomorrow if past)
        - Tomorrow: 'tomorrow at 9:00', 'tomorrow at 10am', 'tomorrow'
        - Absolute: '2026-11-08 14:30', '2026-11-08T14:30:00'

    Args:
        expr: Time description string.
        base_time: Base reference datetime (defaults to current UTC time).

    Returns:
        Target datetime in UTC, or None if expression could not be parsed.
    """
    clean = expr.strip().lower()
    if not clean:
        return None

    now = base_time or datetime.now(timezone.utc)

    # 1. Relative "in X [hours/minutes/seconds/days]" pattern
    if clean.startswith("in "):
        rel_str = clean[3:].strip()
        delta = _parse_duration(rel_str)
        if delta is not None:
            return now + delta

    # 2. "tomorrow [at X]"
    if clean.startswith("tomorrow"):
        rest = clean[8:].strip()
        target_day = (now + timedelta(days=1)).date()
        if not rest:
            # Default to tomorrow at 9:00 AM local/base
            return datetime(target_day.year, target_day.month, target_day.day, 9, 0, tzinfo=now.tzinfo)
        if rest.startswith("at "):
            rest = rest[3:].strip()
        parsed_time = _parse_clock_time(rest)
        if parsed_time is not None:
            h, m = parsed_time
            return datetime(target_day.year, target_day.month, target_day.day, h, m, tzinfo=now.tzinfo)

    # 3. "at HH:MM [am/pm]" or "at Ham/pm"
    if clean.startswith("at "):
        clock_str = clean[3:].strip()
        parsed_time = _parse_clock_time(clock_str)
        if parsed_time is not None:
            h, m = parsed_time
            target = now.replace(hour=h, minute=m, second=0, microsecond=0)
            # If the target time is earlier today, roll forward to tomorrow
            if target <= now:
                target += timedelta(days=1)
            return target

    # 4. Direct clock time like "15:30" or "4pm"
    direct_time = _parse_clock_time(clean)
    if direct_time is not None:
        h, m = direct_time
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target

    # 5. Direct relative without "in" like "10m", "2h", "30s"
    direct_delta = _parse_duration(clean)
    if direct_delta is not None:
        return now + direct_delta

    # 6. Absolute date/time strings
    abs_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d",
    ]
    for fmt in abs_formats:
        try:
            parsed = datetime.strptime(clean, fmt)
            if "%H" not in fmt:
                parsed = parsed.replace(hour=9, minute=0)
            return parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


def _parse_duration(duration_str: str) -> Optional[timedelta]:
    """Parse relative duration string like '10m', '2 hours 15 mins', '45s'."""
    pattern = re.compile(
        r"(?:(\d+)\s*(?:d|day|days))?\s*"
        r"(?:(\d+)\s*(?:h|hr|hrs|hour|hours))?\s*"
        r"(?:(\d+)\s*(?:m|min|mins|minute|minutes))?\s*"
        r"(?:(\d+)\s*(?:s|sec|secs|second|seconds))?",
        re.IGNORECASE,
    )
    match = pattern.fullmatch(duration_str.strip())
    if not match:
        return None

    days_s, hours_s, mins_s, secs_s = match.groups()
    if not any([days_s, hours_s, mins_s, secs_s]):
        return None

    days = int(days_s) if days_s else 0
    hours = int(hours_s) if hours_s else 0
    minutes = int(mins_s) if mins_s else 0
    seconds = int(secs_s) if secs_s else 0

    return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


def _parse_clock_time(time_str: str) -> Optional[Tuple[int, int]]:
    """Parse clock formats like '15:30', '3:30pm', '9am', '12:00'."""
    pattern = re.compile(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$", re.IGNORECASE)
    match = pattern.match(time_str.strip())
    if not match:
        return None

    hour_s, min_s, meridiem = match.groups()
    hour = int(hour_s)
    minute = int(min_s) if min_s else 0

    if minute < 0 or minute > 59:
        return None

    if meridiem:
        meridiem_lower = meridiem.lower()
        if hour < 1 or hour > 12:
            return None
        if meridiem_lower == "pm" and hour != 12:
            hour += 12
        elif meridiem_lower == "am" and hour == 12:
            hour = 0
    else:
        if hour < 0 or hour > 23:
            return None

    return hour, minute


def parse_reminder_command(args: str) -> Tuple[Optional[datetime], Optional[str], Optional[str]]:
    """Extract target time and message from a reminder command argument.

    Examples:
        - 'in 15m to take a stretch break' -> (dt, 'take a stretch break', None)
        - 'tomorrow at 9am to submit quarterly report' -> (dt, 'submit quarterly report', None)
        - '"in 10m" check oven' -> (dt, 'check oven', None)

    Returns:
        Tuple of (target_datetime, reminder_message, error_message).
    """
    trimmed = args.strip()
    if not trimmed:
        return None, None, "Usage: remind <when> to <message> (e.g. 'remind in 15m to drink water')"

    # Pattern A: Quoted time e.g. "in 15m" message
    quoted_match = re.match(r'^["\']([^"\']+)["\']\s+(?:to\s+)?(.+)$', trimmed, re.IGNORECASE)
    if quoted_match:
        time_part, msg_part = quoted_match.groups()
        dt = parse_time_expression(time_part)
        if not dt:
            return None, None, f"Could not parse time expression: '{time_part}'"
        return dt, msg_part.strip(), None

    # Pattern B: <when> to <message>
    if " to " in trimmed.lower():
        # Split on the first occurrence of " to "
        idx = trimmed.lower().find(" to ")
        time_part = trimmed[:idx].strip()
        msg_part = trimmed[idx + 4:].strip()
        dt = parse_time_expression(time_part)
        if dt and msg_part:
            return dt, msg_part, None

    # Pattern C: First token is duration like "10m" or "1h"
    tokens = trimmed.split(maxsplit=1)
    if len(tokens) == 2:
        dt = parse_time_expression(tokens[0])
        if dt:
            msg = tokens[1].strip()
            if msg.lower().startswith("to "):
                msg = msg[3:].strip()
            if msg:
                return dt, msg, None

    # Pattern D: "in X minutes <message>" without "to"
    match_in = re.match(r"^(in\s+\d+\s*(?:m|min|mins|minutes|h|hr|hours|s|sec|seconds))\s+(.+)$", trimmed, re.IGNORECASE)
    if match_in:
        time_part, msg_part = match_in.groups()
        dt = parse_time_expression(time_part)
        if dt:
            return dt, msg_part.strip(), None

    return (
        None,
        None,
        f"Unable to parse time and message from: '{args}'.\n"
        "Format: remind <when> to <message> (e.g., 'remind in 20m to submit report' or 'remind at 17:00 to clock out')",
    )

