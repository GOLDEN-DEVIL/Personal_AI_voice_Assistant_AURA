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


def test_inspect_excel_success(tmp_path: Path):
    import pandas as pd
    from aura.tools.tabular import inspect_excel

    ws = tmp_path / "data"
    ws.mkdir()
    excel_path = ws / "sheet_test.xlsx"

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        pd.DataFrame({"Item": ["A", "B"], "Cost": [10, 20]}).to_excel(writer, sheet_name="Alpha", index=False)
        pd.DataFrame({"User": ["X", "Y"], "Score": [99, 88]}).to_excel(writer, sheet_name="Beta", index=False)

    # Test default first sheet (Alpha)
    res_default = inspect_excel(ws, "sheet_test.xlsx")
    assert "Sheet: 'Alpha'" in res_default
    assert "Available Sheets (2): Alpha, Beta" in res_default
    assert "Item" in res_default

    # Test named sheet (Beta)
    res_named = inspect_excel(ws, "sheet_test.xlsx", sheet_name="Beta")
    assert "Sheet: 'Beta'" in res_named
    assert "User" in res_named
    assert "Score" in res_named

    # Test nonexistent sheet error
    res_missing_sheet = inspect_excel(ws, "sheet_test.xlsx", sheet_name="Gamma")
    assert "Sheet 'Gamma' not found" in res_missing_sheet

    # Test traversal blocked
    res_traversal = inspect_excel(ws, "../../evil.xlsx")
    assert "Security Error" in res_traversal
