"""Unit tests for CSV tabular inspection."""

from pathlib import Path
import pytest

from aura.tools.tabular import inspect_csv


@pytest.fixture
def temp_csv_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "data"
    ws.mkdir()
    sample = ws / "test.csv"
    sample.write_text(
        "id,product,price,stock\n"
        "1,Widget,19.99,100\n"
        "2,Gadget,49.99,25\n"
        "3,Doohickey,5.99,500\n"
        "4,Thingamajig,12.50,80\n"
        "5,Whatchamacallit,99.00,10\n"
        "6,Gizmo,34.00,45\n",
        encoding="utf-8",
    )
    return ws


def test_inspect_csv_success(temp_csv_workspace: Path):
    result = inspect_csv(temp_csv_workspace, "test.csv", preview_rows=3)
    assert "Dimensions: 6 rows x 4 columns" in result
    assert "product" in result
    assert "price" in result
    assert "Widget" in result
    assert "Gadget" in result
    assert "Preview (First 3 rows):" in result


def test_inspect_csv_traversal_blocked(temp_csv_workspace: Path):
    result = inspect_csv(temp_csv_workspace, "../../passwords.csv")
    assert "Security Error" in result


def test_inspect_csv_not_found(temp_csv_workspace: Path):
    result = inspect_csv(temp_csv_workspace, "nonexistent.csv")
    assert "was not found" in result
