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


def write_text_file(
    workspace_dir: Path,
    filename: str,
    content: str,
    append: bool = False,
    overwrite: bool = False,
) -> str:
    """Safely create or append to a text-based document in the workspace.

    Safety guards:
    - Confined strictly to the workspace boundary.
    - Only permits text file extensions (.txt, .md, .log, .csv).
    - Protects existing files from accidental destruction unless explicit confirmation or append is requested.
    """
    clean_name = filename.strip()
    if not clean_name:
        return "Error: Please specify a filename (e.g., 'write notes.txt Meeting notes here')."

    # Restrict to safe non-executable text formats
    allowed_extensions = {".txt", ".md", ".log", ".csv", ".json"}
    target_ext = Path(clean_name).suffix.lower()
    if target_ext not in allowed_extensions:
        return (
            f"Security Error: Creating files with extension '{target_ext}' is forbidden.\n"
            f"Allowed extensions: {', '.join(sorted(allowed_extensions))}"
        )

    try:
        file_path = validate_workspace_path(clean_name, workspace_dir)
    except SecurityError as err:
        return f"Security Error: {err}"

    rel_path = file_path.relative_to(workspace_dir)

    # Accidental overwrite protection
    if file_path.exists() and not append and not overwrite:
        return (
            f"Safety Warning: File '{rel_path}' already exists.\n"
            f"To append new content, use: 'append {clean_name} <content>'\n"
            f"To overwrite the file, use: 'write {clean_name} --overwrite <content>'"
        )

    try:
        # Create parent directories if subfolder requested within workspace
        file_path.parent.mkdir(parents=True, exist_ok=True)

        mode = "a" if append else "w"
        write_content = f"\n{content}" if append and file_path.exists() else content

        with file_path.open(mode, encoding="utf-8") as f:
            f.write(write_content)

        action_str = "Appended to" if append else "Created"
        return f"Success: {action_str} '{rel_path}' ({len(content)} characters written)."
    except Exception as err:
        return f"Write Error: Could not write to '{clean_name}': {err}"


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
