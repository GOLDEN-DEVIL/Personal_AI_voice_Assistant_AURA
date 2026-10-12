"""Tabular data tools: CSV inspection with Pandas."""

from __future__ import annotations

from pathlib import Path
from aura.safety import SecurityError, validate_workspace_path


def inspect_csv(workspace_dir: Path, filename: str, preview_rows: int = 5) -> str:
    """Safely inspect a CSV file using Pandas.

    Shows row count, columns, data types, and a concise top-N rows preview.
    Gracefully degrades if Pandas is unavailable.
    """
    clean_name = filename.strip()
    if not clean_name:
        return "Error: Please specify a CSV filename (e.g., 'csv sample.csv')."

    # Check for pandas
    try:
        import pandas as pd
    except ImportError:
        return (
            "CSV Inspection Unavailable:\n"
            "Pandas is not installed in the current environment.\n"
            "To enable CSV inspection, install it via:\n"
            "    pip install pandas\n"
        )

    try:
        file_path = validate_workspace_path(clean_name, workspace_dir)
    except SecurityError as err:
        return f"Security Error: {err}"

    if not file_path.exists():
        return f"Error: CSV file '{clean_name}' was not found in the workspace."

    if not file_path.is_file():
        return f"Error: '{clean_name}' is not a regular file."

    if file_path.suffix.lower() != ".csv":
        return f"Warning: '{clean_name}' does not have a .csv extension."

    try:
        # Read with pandas safely
        df = pd.read_csv(file_path)
        row_count, col_count = df.shape

        col_info = [f"  - {col} ({df[col].dtype})" for col in df.columns]

        # Convert preview to a clean string format
        preview_df = df.head(preview_rows)
        preview_table = preview_df.to_string(index=False)

        lines = [
            f"=== CSV Inspection: {file_path.relative_to(workspace_dir)} ===",
            f"Dimensions: {row_count} rows x {col_count} columns",
            f"Columns ({col_count}):",
            *col_info,
            "",
            f"Preview (First {min(preview_rows, row_count)} rows):",
            preview_table,
        ]
        return "\n".join(lines)
    except Exception as err:
        return f"CSV Processing Error: Failed to parse '{clean_name}': {err}"


def inspect_excel(
    workspace_dir: Path,
    filename: str,
    sheet_name: str | None = None,
    preview_rows: int = 5,
) -> str:
    """Safely inspect an Excel (.xlsx / .xls) spreadsheet.

    Lists all available worksheets, active sheet dimensions, and a concise top-N rows preview.
    Gracefully degrades if openpyxl or Pandas is unavailable.
    """
    clean_name = filename.strip()
    if not clean_name:
        return "Error: Please specify an Excel filename (e.g., 'excel workbook.xlsx' or 'excel data.xlsx Sheet1')."

    # Check for pandas and openpyxl
    try:
        import pandas as pd
        import openpyxl  # noqa: F401
    except ImportError as err:
        missing_pkg = "openpyxl" if "openpyxl" in str(err).lower() else "pandas"
        return (
            "Excel Inspection Unavailable:\n"
            f"The package '{missing_pkg}' is not installed.\n"
            "To enable Excel inspection, install it via:\n"
            "    pip install openpyxl\n"
            "or: pip install .[excel]"
        )

    try:
        file_path = validate_workspace_path(clean_name, workspace_dir)
    except SecurityError as err:
        return f"Security Error: {err}"

    if not file_path.exists():
        return f"Error: Excel file '{clean_name}' was not found in the workspace."

    if not file_path.is_file():
        return f"Error: '{clean_name}' is not a regular file."

    if file_path.suffix.lower() not in (".xlsx", ".xls"):
        return f"Warning: '{clean_name}' does not have an .xlsx or .xls extension."

    try:
        excel_file = pd.ExcelFile(file_path, engine="openpyxl")
        all_sheets = excel_file.sheet_names

        target_sheet = sheet_name.strip() if sheet_name else all_sheets[0]
        if target_sheet not in all_sheets:
            return (
                f"Error: Sheet '{target_sheet}' not found in '{clean_name}'.\n"
                f"Available sheets: {', '.join(all_sheets)}"
            )

        df = excel_file.parse(sheet_name=target_sheet)
        row_count, col_count = df.shape

        col_info = [f"  - {col} ({df[col].dtype})" for col in df.columns]
        preview_df = df.head(preview_rows)
        preview_table = preview_df.to_string(index=False)

        lines = [
            f"=== Excel Inspection: {file_path.relative_to(workspace_dir)} [Sheet: '{target_sheet}'] ===",
            f"Available Sheets ({len(all_sheets)}): {', '.join(all_sheets)}",
            f"Dimensions: {row_count} rows x {col_count} columns",
            f"Columns ({col_count}):",
            *col_info,
            "",
            f"Preview (First {min(preview_rows, row_count)} rows):",
            preview_table,
        ]
        return "\n".join(lines)
    except Exception as err:
        return f"Excel Processing Error: Failed to parse '{clean_name}': {err}"
