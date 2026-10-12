"""Unit tests for document inspection (text and PDF)."""

from pathlib import Path
import pytest

from aura.tools.documents import inspect_pdf, read_text_file


@pytest.fixture
def temp_docs_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "data"
    ws.mkdir()
    (ws / "sample.txt").write_text("Hello AURA document reader!", encoding="utf-8")
    return ws


def test_read_text_file(temp_docs_workspace: Path):
    result = read_text_file(temp_docs_workspace, "sample.txt")
    assert "Hello AURA document reader!" in result


def test_read_text_file_not_found(temp_docs_workspace: Path):
    result = read_text_file(temp_docs_workspace, "missing.txt")
    assert "does not exist in workspace" in result


def test_inspect_pdf_with_real_pdf(temp_docs_workspace: Path):
    try:
        import pymupdf as fitz
    except ImportError:
        pytest.skip("PyMuPDF not installed")

    # Generate a small in-memory PDF for testing
    pdf_path = temp_docs_workspace / "test_doc.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Project AURA Automated PDF Verification Test")
    doc.set_metadata({"title": "Test Title", "author": "AURA Bot"})
    doc.save(pdf_path)
    doc.close()

    result = inspect_pdf(temp_docs_workspace, "test_doc.pdf")
    assert "Pages  : 1" in result
    assert "Test Title" in result
    assert "Project AURA Automated PDF Verification Test" in result


def test_inspect_pdf_traversal_blocked(temp_docs_workspace: Path):
    result = inspect_pdf(temp_docs_workspace, "../../outside.pdf")
    assert "Security Error" in result


def test_write_text_file_new_and_overwrite_protection(temp_docs_workspace: Path):
    from aura.tools.documents import write_text_file

    # Create new file
    res = write_text_file(temp_docs_workspace, "new_note.txt", "Initial notes content.")
    assert "Success: Created 'new_note.txt'" in res
    assert (temp_docs_workspace / "new_note.txt").read_text(encoding="utf-8") == "Initial notes content."

    # Overwrite protection check (should warn and refuse without overwrite flag)
    res_refusal = write_text_file(temp_docs_workspace, "new_note.txt", "Different content.")
    assert "Safety Warning: File 'new_note.txt' already exists" in res_refusal
    assert (temp_docs_workspace / "new_note.txt").read_text(encoding="utf-8") == "Initial notes content."

    # Explicit overwrite
    res_overwrite = write_text_file(temp_docs_workspace, "new_note.txt", "Overwritten content.", overwrite=True)
    assert "Success: Created 'new_note.txt'" in res_overwrite
    assert (temp_docs_workspace / "new_note.txt").read_text(encoding="utf-8") == "Overwritten content."


def test_write_text_file_append(temp_docs_workspace: Path):
    from aura.tools.documents import write_text_file

    write_text_file(temp_docs_workspace, "log.txt", "Line 1")
    write_text_file(temp_docs_workspace, "log.txt", "Line 2", append=True)

    content = (temp_docs_workspace / "log.txt").read_text(encoding="utf-8")
    assert "Line 1" in content
    assert "Line 2" in content


def test_write_text_file_security_checks(temp_docs_workspace: Path):
    from aura.tools.documents import write_text_file

    # Executable / script extension blocked
    res_exe = write_text_file(temp_docs_workspace, "script.py", "print('malicious')")
    assert "Security Error: Creating files with extension '.py' is forbidden" in res_exe

    res_bat = write_text_file(temp_docs_workspace, "run.bat", "calc.exe")
    assert "Security Error: Creating files with extension '.bat' is forbidden" in res_bat

    # Traversal blocked
    res_traversal = write_text_file(temp_docs_workspace, "../escape.txt", "escape")
    assert "Security Error" in res_traversal
