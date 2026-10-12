"""Unit tests for workspace-bounded file operations and safety."""

import pytest
from pathlib import Path

from aura.safety import SecurityError, validate_workspace_path
from aura.tools.documents import read_text_file
from aura.tools.files import list_workspace_files, search_workspace_files


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Create a temporary sandbox workspace directory with dummy files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Subdirectory
    sub = data_dir / "reports"
    sub.mkdir()

    # Files
    (data_dir / "notes.txt").write_text("Meeting notes content", encoding="utf-8")
    (data_dir / "data.csv").write_text("a,b\n1,2", encoding="utf-8")
    (sub / "summary.txt").write_text("Monthly summary report", encoding="utf-8")

    return data_dir


def test_validate_workspace_path_within_bounds(temp_workspace: Path):
    path = validate_workspace_path("notes.txt", temp_workspace)
    assert path == (temp_workspace / "notes.txt").resolve()

    sub_path = validate_workspace_path("reports/summary.txt", temp_workspace)
    assert sub_path == (temp_workspace / "reports" / "summary.txt").resolve()


def test_validate_workspace_path_rejects_traversal(temp_workspace: Path):
    with pytest.raises(SecurityError):
        validate_workspace_path("../outside.txt", temp_workspace)

    with pytest.raises(SecurityError):
        validate_workspace_path("../../", temp_workspace)


def test_list_workspace_files(temp_workspace: Path):
    output = list_workspace_files(temp_workspace)
    assert "Contents of '.'" in output
    assert "notes.txt" in output
    assert "data.csv" in output
    assert "reports/" in output


def test_list_workspace_files_traversal_blocked(temp_workspace: Path):
    output = list_workspace_files(temp_workspace, "../")
    assert "Security Error" in output


def test_search_workspace_files(temp_workspace: Path):
    res = search_workspace_files(temp_workspace, "*.txt")
    assert "Found 2 match(es)" in res
    assert "notes.txt" in res
    assert "summary.txt" in res


def test_search_workspace_files_type_filters(temp_workspace: Path):
    res_files = search_workspace_files(temp_workspace, "reports --files")
    assert "No matching items found" in res_files

    res_dirs = search_workspace_files(temp_workspace, "reports --dirs")
    assert "Found 1 match(es)" in res_dirs
    assert "[DIR]  reports" in res_dirs


def test_search_workspace_files_traversal_blocked(temp_workspace: Path):
    res = search_workspace_files(temp_workspace, "../evil")
    assert "Security Error" in res


def test_read_text_file(temp_workspace: Path):
    content = read_text_file(temp_workspace, "notes.txt")
    assert "Meeting notes content" in content


def test_read_text_file_traversal_blocked(temp_workspace: Path):
    res = read_text_file(temp_workspace, "../secret.txt")
    assert "Security Error" in res
