"""Tests for ALPS document management tools."""

import pytest
from pathlib import Path

from alps_mcp_server import server


@pytest.fixture
def temp_doc(tmp_path):
    """Create a temporary document and clean up WORKING_DOC after test."""
    doc_path = tmp_path / "test.alps.md"
    yield doc_path
    server.WORKING_DOC = None


class TestParseAndBuild:
    def test_build_document_creates_all_sections(self):
        doc = server._build_document("TestProject", {})
        assert "# TestProject ALPS" in doc
        for i in range(1, 10):
            assert f'<section id="{i}">' in doc
            assert f"## Section {i}." in doc

    def test_build_document_with_content(self):
        doc = server._build_document("Test", {1: "Overview content here"})
        assert "Overview content here" in doc

    def test_parse_sections_extracts_content_without_header(self):
        doc = server._build_document("Test", {1: "My content", 2: "Second content"})
        sections = server._parse_sections(doc)
        assert sections[1] == "My content"
        assert sections[2] == "Second content"
        assert "## Section" not in sections[1]

    def test_round_trip_preserves_content(self):
        original = {1: "Content 1", 3: "Content 3", 9: "Content 9"}
        doc = server._build_document("Test", original)
        parsed = server._parse_sections(doc)
        for k, v in original.items():
            assert parsed[k] == v

    def test_extract_project_name(self):
        doc = server._build_document("MyAwesomeProject", {})
        assert server._extract_project_name(doc) == "MyAwesomeProject"


class TestInitDocument:
    def test_creates_new_document(self, temp_doc):
        result = server.init_alps_document("TestProject", str(temp_doc))
        assert "Created" in result
        assert temp_doc.exists()
        assert server.WORKING_DOC == temp_doc

    def test_adds_suffix_if_missing(self, tmp_path):
        doc_path = tmp_path / "test"
        server.init_alps_document("Test", str(doc_path))
        assert (tmp_path / "test.alps.md").exists()
        server.WORKING_DOC = None

    def test_existing_document_not_overwritten(self, temp_doc):
        temp_doc.write_text("existing content")
        result = server.init_alps_document("Test", str(temp_doc))
        assert "already exists" in result
        assert temp_doc.read_text() == "existing content"


class TestLoadDocument:
    def test_loads_existing_document(self, temp_doc):
        server.init_alps_document("Test", str(temp_doc))
        server.WORKING_DOC = None
        result = server.load_alps_document(str(temp_doc))
        assert "ALPS Document: Test" in result
        assert server.WORKING_DOC == temp_doc

    def test_returns_error_for_missing_file(self, tmp_path):
        result = server.load_alps_document(str(tmp_path / "nonexistent.md"))
        assert "not found" in result


class TestSaveAndReadSection:
    def test_save_and_read_section(self, temp_doc):
        server.init_alps_document("Test", str(temp_doc))
        server.save_alps_section(1, "New overview content")
        content = server.read_alps_section(1)
        assert content == "New overview content"

    def test_save_preserves_other_sections(self, temp_doc):
        server.init_alps_document("Test", str(temp_doc))
        server.save_alps_section(1, "Section 1 content")
        server.save_alps_section(2, "Section 2 content")
        assert server.read_alps_section(1) == "Section 1 content"
        assert server.read_alps_section(2) == "Section 2 content"

    def test_save_without_loaded_doc_returns_error(self):
        server.WORKING_DOC = None
        result = server.save_alps_section(1, "content")
        assert "No document loaded" in result

    def test_invalid_section_number(self, temp_doc):
        server.init_alps_document("Test", str(temp_doc))
        assert "Invalid section" in server.save_alps_section(10, "x")
        assert "not found" in server.read_alps_section(0)


class TestDocumentStatus:
    def test_status_shows_not_started(self, temp_doc):
        server.init_alps_document("Test", str(temp_doc))
        status = server.get_alps_document_status()
        assert "⬜ Not started" in status

    def test_status_shows_written_after_save(self, temp_doc):
        server.init_alps_document("Test", str(temp_doc))
        server.save_alps_section(1, "A" * 100)  # >50 chars
        status = server.get_alps_document_status()
        assert "Section 1 (Overview): ✅ Written" in status


class TestExportMarkdown:
    def test_export_removes_xml_tags(self, temp_doc):
        server.init_alps_document("Test", str(temp_doc))
        server.save_alps_section(1, "Overview content")
        result = server.export_alps_markdown()
        assert "<section" not in result
        assert "</section>" not in result
        assert "## Section 1. Overview" in result
        assert "Overview content" in result

    def test_export_to_file(self, temp_doc, tmp_path):
        server.init_alps_document("Test", str(temp_doc))
        out_path = tmp_path / "export.md"
        result = server.export_alps_markdown(str(out_path))
        assert "Exported" in result
        assert out_path.exists()

    def test_not_started_shows_placeholder(self, temp_doc):
        server.init_alps_document("Test", str(temp_doc))
        result = server.export_alps_markdown()
        assert "*Not yet written*" in result
