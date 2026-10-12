"""Document inspection tools: text files and PDFs."""

from __future__ import annotations

from pathlib import Path
from aura.safety import SecurityError, sanitize_output, validate_workspace_path


def read_text_file(workspace_dir: Path, filename: str, max_chars: int = 2000) -> str:
    """Safely read and preview a text-based document from the workspace."""
    clean_name = filename.strip()
    if not clean_name:
        return "Error: Please specify a filename to read (e.g., 'read notes.txt')."

    try:
        file_path = validate_workspace_path(clean_name, workspace_dir)
    except SecurityError as err:
        return f"Security Error: {err}"

    if not file_path.exists():
        return f"Error: File '{clean_name}' does not exist in workspace."

    if not file_path.is_file():
        return f"Error: '{clean_name}' is a directory, not a file. Use 'files {clean_name}' to list its contents."

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as err:
        return f"File Read Error: Could not read '{clean_name}': {err}"

    total_chars = len(content)
    preview = sanitize_output(content, max_chars=max_chars)
    rel_path = file_path.relative_to(workspace_dir)

    header = f"=== File: {rel_path} ({total_chars} characters) ==="
    return f"{header}\n{preview}"


def inspect_pdf(workspace_dir: Path, filename: str, max_chars: int = 2000) -> str:
    """Inspect and extract text from a PDF inside the workspace.

    Degrades gracefully if PyMuPDF (fitz) is not installed.
    """
    clean_name = filename.strip()
    if not clean_name:
        return "Error: Please specify a PDF filename (e.g., 'pdf document.pdf')."

    # Verify optional dependency (supports modern pymupdf and legacy fitz)
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            return (
                "PDF Inspection Unavailable:\n"
                "The optional dependency 'pymupdf' is not installed.\n"
                "To enable PDF reading, install it via:\n"
                "    pip install pymupdf\n"
                "or: pip install .[pdf]"
            )

    try:
        file_path = validate_workspace_path(clean_name, workspace_dir)
    except SecurityError as err:
        return f"Security Error: {err}"

    if not file_path.exists():
        return f"Error: File '{clean_name}' was not found in the workspace."

    if not file_path.is_file():
        return f"Error: '{clean_name}' is not a regular file."

    if file_path.suffix.lower() != ".pdf":
        return f"Warning: '{clean_name}' does not have a .pdf extension."

    try:
        doc = fitz.open(file_path)
        page_count = len(doc)
        metadata = doc.metadata or {}

        title = metadata.get("title") or "Unknown"
        author = metadata.get("author") or "Unknown"

        extracted_text_parts = []
        for i in range(min(page_count, 3)):  # Sample up to first 3 pages
            page = doc[i]
            text = page.get_text()
            if text.strip():
                extracted_text_parts.append(f"--- Page {i + 1} ---\n{text.strip()}")

        combined_text = "\n\n".join(extracted_text_parts) if extracted_text_parts else "[No readable text found]"
        safe_preview = sanitize_output(combined_text, max_chars=max_chars)

        doc.close()

        summary_lines = [
            f"=== PDF Document: {file_path.relative_to(workspace_dir)} ===",
            f"Pages  : {page_count}",
            f"Title  : {title}",
            f"Author : {author}",
            "",
            "Extracted Text Preview:",
            safe_preview,
        ]
        return "\n".join(summary_lines)
    except Exception as err:
        return f"PDF Processing Error: Could not read '{clean_name}': {err}"
