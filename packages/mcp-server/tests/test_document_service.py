"""Tests for DocumentService."""

import pytest
from pathlib import Path
from alps_mcp_server.tools.documents.service import DocumentService


@pytest.fixture
def service():
    return DocumentService()


@pytest.fixture
def temp_doc(tmp_path, service):
    doc_path = tmp_path / "test.alps.xml"
    service.init_document("TestProject", str(doc_path))
    return doc_path


def test_init_document(tmp_path, service):
    doc_path = tmp_path / "new.alps.xml"
    result = service.init_document("MyProject", str(doc_path))
    assert "Created" in result
    assert doc_path.exists()


def test_init_document_already_exists(temp_doc, service):
    result = service.init_document("Another", str(temp_doc))
    assert "already exists" in result


def test_load_document(temp_doc, service):
    new_service = DocumentService()
    result = new_service.load_document(str(temp_doc))
    assert "TestProject" in result


def test_save_and_read_section(temp_doc, service):
    service.save_section(1, "Test content for section 1")
    result = service.read_section(1)
    assert "Test content" in result


def test_save_subsection(temp_doc, service):
    service.save_section(7, "Feature 1 content", subsection=1)
    service.save_section(7, "Feature 2 content", subsection=2)
    result = service.read_section(7)
    assert "Feature 1" in result
    assert "Feature 2" in result


def test_get_status(temp_doc, service):
    result = service.get_status()
    assert "TestProject" in result
    assert "Not started" in result


def test_export_markdown(temp_doc, service):
    service.save_section(1, "Overview content here")
    result = service.export_markdown()
    assert "# TestProject ALPS" in result
    assert "Overview content" in result
    assert "<section" not in result
