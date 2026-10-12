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
