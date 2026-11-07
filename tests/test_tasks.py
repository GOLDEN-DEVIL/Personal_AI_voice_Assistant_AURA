"""Unit and integration tests for tasks, reminders, SQLite persistence, and scheduler."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import pytest

from aura.config import AuraConfig
from aura.router import CommandRouter
from aura.tasks.db import TaskDatabase
from aura.tasks.models import Task, Reminder
from aura.tasks.scheduler import ReminderScheduler
from aura.tasks.time_parser import parse_reminder_command, parse_time_expression


# ---------------------------------------------------------------------------
# 1. Database & Persistence Tests
# ---------------------------------------------------------------------------

def test_add_task_success(tmp_path):
    """Adding a valid task should persist it with default status and assigned ID."""
    db = TaskDatabase(tmp_path / "test.db")
    task = db.add_task("Prepare presentation", priority="high", due_date="2026-11-10")

    assert task.id == 1
    assert task.title == "Prepare presentation"
    assert task.priority == "high"
    assert task.status == "pending"
    assert task.due_date == "2026-11-10"
    assert task.created_at != ""


def test_add_task_validation_empty_title(tmp_path):
    """Adding a task with an empty title should raise ValueError."""
    db = TaskDatabase(tmp_path / "test.db")
    with pytest.raises(ValueError, match="cannot be empty"):
        db.add_task("   ")


def test_add_task_title_length_bounded(tmp_path):
    """Titles exceeding 300 characters should be cleanly bounded."""
    db = TaskDatabase(tmp_path / "test.db")
    long_title = "A" * 500
    task = db.add_task(long_title)
    assert len(task.title) <= 300


def test_list_tasks_and_filtering(tmp_path):
    """list_tasks should support filtering by status and priority."""
    db = TaskDatabase(tmp_path / "test.db")
    t1 = db.add_task("Task 1", priority="low")
    t2 = db.add_task("Task 2", priority="high")
    t3 = db.add_task("Task 3", priority="medium")

    db.complete_task(t1.id)

    pending = db.list_tasks(status="pending")
    assert len(pending) == 2
    assert t1.id not in [t.id for t in pending]

    high_prio = db.list_tasks(priority="high")
    assert len(high_prio) == 1
    assert high_prio[0].id == t2.id


def test_complete_task(tmp_path):
    """complete_task should change status to 'completed' and update timestamp."""
    db = TaskDatabase(tmp_path / "test.db")
    t = db.add_task("Write docs")
    assert db.complete_task(t.id) is True

    updated = db.get_task(t.id)
    assert updated.status == "completed"

    # Non-existent ID returns False
    assert db.complete_task(999) is False


def test_delete_task(tmp_path):
    """delete_task should permanently remove the task."""
    db = TaskDatabase(tmp_path / "test.db")
    t = db.add_task("Delete me")
    assert db.delete_task(t.id) is True
    assert db.get_task(t.id) is None
    assert db.delete_task(t.id) is False


def test_clear_completed_tasks(tmp_path):
    """clear_completed_tasks should only delete completed tasks."""
    db = TaskDatabase(tmp_path / "test.db")
    t1 = db.add_task("Keep me")
    t2 = db.add_task("Clear me")
    db.complete_task(t2.id)

    cleared = db.clear_completed_tasks()
    assert cleared == 1
    remaining = db.list_tasks()
    assert len(remaining) == 1
    assert remaining[0].id == t1.id


# ---------------------------------------------------------------------------
# 2. Reminder Database Tests
# ---------------------------------------------------------------------------

def test_add_reminder_and_list(tmp_path):
    """Reminders should be created in 'scheduled' state."""
    db = TaskDatabase(tmp_path / "test.db")
    future_iso = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    rem = db.add_reminder("Take vitamins", future_iso)

    assert rem.id == 1
    assert rem.message == "Take vitamins"
    assert rem.status == "scheduled"
    assert len(db.list_reminders()) == 1


def test_get_due_reminders_and_mark_fired(tmp_path):
    """get_due_reminders returns only items past their trigger time."""
    db = TaskDatabase(tmp_path / "test.db")
    past_iso = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    future_iso = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()

    r_due = db.add_reminder("Due now", past_iso)
    r_future = db.add_reminder("Due later", future_iso)

    due = db.get_due_reminders()
    assert len(due) == 1
    assert due[0].id == r_due.id

    # Mark fired
    assert db.mark_reminder_fired(r_due.id) is True
    assert len(db.get_due_reminders()) == 0


def test_cancel_reminder(tmp_path):
    """Cancelling a reminder transitions it to 'cancelled'."""
    db = TaskDatabase(tmp_path / "test.db")
    future_iso = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    rem = db.add_reminder("Stretch", future_iso)

    assert db.cancel_reminder(rem.id) is True
    cancelled = db.list_reminders(status="cancelled")
    assert len(cancelled) == 1
    assert cancelled[0].id == rem.id


# ---------------------------------------------------------------------------
# 3. Time Parser Tests
# ---------------------------------------------------------------------------

def test_parse_time_relative_durations():
    """Relative expressions should add the correct timedelta to base time."""
    base = datetime(2026, 11, 7, 12, 0, 0, tzinfo=timezone.utc)

    # Minutes
    t1 = parse_time_expression("in 15m", base_time=base)
    assert t1 == base + timedelta(minutes=15)

    # Hours
    t2 = parse_time_expression("in 2h", base_time=base)
    assert t2 == base + timedelta(hours=2)

    # Days
    t3 = parse_time_expression("in 1 day", base_time=base)
    assert t3 == base + timedelta(days=1)


def test_parse_time_clock():
    """Clock times should correctly determine target time and handle roll-over."""
    base = datetime(2026, 11, 7, 10, 0, 0, tzinfo=timezone.utc)

    # Later today
    t1 = parse_time_expression("at 15:30", base_time=base)
    assert t1.hour == 15 and t1.minute == 30 and t1.day == 7

    # Earlier today rolls to tomorrow
    t2 = parse_time_expression("at 8:00", base_time=base)
    assert t2.hour == 8 and t2.minute == 0 and t2.day == 8


def test_parse_reminder_command_syntax():
    """parse_reminder_command should split when-clause and reminder message."""
    dt, msg, err = parse_reminder_command("in 20m to submit timesheet")
    assert err is None
    assert msg == "submit timesheet"
    assert dt is not None

    dt2, msg2, err2 = parse_reminder_command('"in 10m" stretch and drink water')
    assert err2 is None
    assert msg2 == "stretch and drink water"
    assert dt2 is not None

    _, _, err3 = parse_reminder_command("nonsense invalid string")
    assert err3 is not None


# ---------------------------------------------------------------------------
# 4. Background Scheduler Tests
# ---------------------------------------------------------------------------

def test_scheduler_fires_due_reminders(tmp_path):
    """Scheduler background thread should trigger notification callback."""
    db = TaskDatabase(tmp_path / "test.db")
    past_iso = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    db.add_reminder("Drink water", past_iso)

    fired_messages = []
    scheduler = ReminderScheduler(
        db,
        notification_callback=lambda r: fired_messages.append(r.message),
        check_interval_seconds=0.05,
    )

    scheduler.start()
    assert scheduler.is_running() is True
    time.sleep(0.2)
    scheduler.stop()

    assert "Drink water" in fired_messages
    assert len(db.list_reminders(status="fired")) == 1


# ---------------------------------------------------------------------------
# 5. CommandRouter Integration Tests
# ---------------------------------------------------------------------------

def test_router_task_add_and_list(tmp_path):
    """Router executes 'task add' and 'task list' commands."""
    cfg = AuraConfig(app_name="AURA", version="0.1.0", workspace_dir=tmp_path, log_level="INFO")
    db = TaskDatabase(tmp_path / "test.db")
    router = CommandRouter(cfg, task_db=db)

    resp_add, _ = router.execute("task add Review project pull request --priority high")
    assert "Task #1 created: 'Review project pull request' [HIGH]" in resp_add

    resp_list, _ = router.execute("task list")
    assert "[#1]" in resp_list
    assert "Review project pull request" in resp_list
    assert "[TODO]" in resp_list
    assert "HIGH" in resp_list


def test_router_task_done_and_delete(tmp_path):
    """Router executes 'task done' and 'task delete'."""
    cfg = AuraConfig(app_name="AURA", version="0.1.0", workspace_dir=tmp_path, log_level="INFO")
    db = TaskDatabase(tmp_path / "test.db")
    router = CommandRouter(cfg, task_db=db)

    router.execute("task add Test task")
    resp_done, _ = router.execute("task done 1")
    assert "Task #1 marked as completed!" in resp_done

    resp_del, _ = router.execute("task delete 1")
    assert "Task #1 deleted." in resp_del


def test_router_remind_and_reminders(tmp_path):
    """Router executes 'remind <when> to <msg>' and 'reminders'."""
    cfg = AuraConfig(app_name="AURA", version="0.1.0", workspace_dir=tmp_path, log_level="INFO")
    db = TaskDatabase(tmp_path / "test.db")
    router = CommandRouter(cfg, task_db=db)

    resp_rem, _ = router.execute("remind in 15m to take a walk")
    assert "Reminder #1 scheduled for" in resp_rem
    assert "take a walk" in resp_rem

    resp_list, _ = router.execute("reminders")
    assert "[#1] [SCHEDULED]" in resp_list
    assert "take a walk" in resp_list

    resp_cancel, _ = router.execute("reminder cancel 1")
    assert "Reminder #1 has been cancelled." in resp_cancel
