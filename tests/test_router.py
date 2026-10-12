"""Unit tests for CommandRouter."""

from pathlib import Path
import pytest

from aura.config import AuraConfig
from aura.router import CommandRouter


@pytest.fixture
def router(tmp_path: Path) -> CommandRouter:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "test.csv").write_text("x,y\n1,2", encoding="utf-8")
    cfg = AuraConfig(
        app_name="AURA_TEST",
        version="0.1.0-test",
        workspace_dir=data_dir,
        log_level="DEBUG",
    )
    return CommandRouter(cfg)


def test_router_help(router: CommandRouter):
    response, should_exit = router.execute("help")
    assert "Available commands:" in response
    assert not should_exit


def test_router_time_and_date(router: CommandRouter):
    resp_time, exit_time = router.execute("time")
    assert "Current local time:" in resp_time
    assert not exit_time

    resp_date, exit_date = router.execute("date")
    assert "Today's date:" in resp_date
    assert not exit_date


def test_router_exit(router: CommandRouter):
    for exit_cmd in ["exit", "quit", "bye", "q"]:
        resp, should_exit = router.execute(exit_cmd)
        assert should_exit
        assert "Goodbye" in resp


def test_router_calc(router: CommandRouter):
    resp, should_exit = router.execute("calc 50 * 2")
    assert "Result: 100" in resp
    assert not should_exit


def test_router_files_and_csv(router: CommandRouter):
    resp_files, _ = router.execute("files")
    assert "test.csv" in resp_files

    resp_csv, _ = router.execute("csv test.csv")
    assert "Dimensions: 1 rows x 2 columns" in resp_csv


def test_router_write_and_append(router: CommandRouter):
    resp_write, _ = router.execute("write todo.txt Buy groceries")
    assert "Success: Created 'todo.txt'" in resp_write

    resp_append, _ = router.execute("append todo.txt Call Alice")
    assert "Success: Appended to 'todo.txt'" in resp_append

    resp_read, _ = router.execute("read todo.txt")
    assert "Buy groceries" in resp_read
    assert "Call Alice" in resp_read


def test_router_excel(router: CommandRouter):
    import pandas as pd
    excel_path = router.config.workspace_dir / "demo.xlsx"
    pd.DataFrame({"X": [1], "Y": [2]}).to_excel(excel_path, engine="openpyxl", index=False)

    resp_excel, _ = router.execute("excel demo.xlsx")
    assert "Dimensions: 1 rows x 2 columns" in resp_excel


def test_router_conversational_fallback(router: CommandRouter):
    queries = [
        "What is the capital of France?",
        "Who created you?",
        "Can you write a poem for me?",
        "Hello there!",
    ]
    for q in queries:
        resp, should_exit = router.execute(q)
        assert "AURA is currently operating in local-only mode" in resp
        assert not should_exit


def test_router_unknown_command(router: CommandRouter):
    resp, should_exit = router.execute("xyz123random")
    assert "Unrecognized command: 'xyz123random'" in resp
    assert "Type 'help'" in resp
    assert not should_exit
