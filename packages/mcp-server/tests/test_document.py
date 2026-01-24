"""Tests for ALPS document management tools."""

import pytest
from pathlib import Path

from alps_mcp_server.tools.documents.service import DocumentService
from alps_mcp_server.tools.templates.service import TemplateService
from alps_mcp_server.interfaces.constants import SECTION_REFERENCES


@pytest.fixture
def doc_service():
    return DocumentService()


@pytest.fixture
def template_service():
    return TemplateService()


@pytest.fixture
def temp_doc(tmp_path, doc_service):
    """Create a temporary document."""
    doc_path = tmp_path / "test.alps.xml"
    doc_service.init_document("Test", str(doc_path))
    return doc_path


class TestParseAndBuild:
    def test_build_document_creates_all_sections(self, doc_service):
        doc = doc_service._build_document("TestProject", {})
        assert "# TestProject ALPS" in doc
        for i in range(1, 10):
            assert f'<section id="{i}">' in doc
            assert f"## Section {i}." in doc

    def test_build_document_with_content(self, doc_service):
        doc = doc_service._build_document("Test", {1: "Overview content here"})
        assert "Overview content here" in doc

    def test_parse_sections_extracts_content_without_header(self, doc_service):
        doc = doc_service._build_document("Test", {1: "My content", 2: "Second content"})
        sections = doc_service._parse_sections(doc)
        assert sections[1] == "My content"
        assert sections[2] == "Second content"
        assert "## Section" not in sections[1]

    def test_round_trip_preserves_content(self, doc_service):
        original = {1: "Content 1", 3: "Content 3", 9: "Content 9"}
        doc = doc_service._build_document("Test", original)
        parsed = doc_service._parse_sections(doc)
        for k, v in original.items():
            assert parsed[k] == v

    def test_extract_project_name(self, doc_service):
        doc = doc_service._build_document("MyAwesomeProject", {})
        assert doc_service._extract_project_name(doc) == "MyAwesomeProject"


class TestInitDocument:
    def test_creates_new_document(self, tmp_path, doc_service):
        doc_path = tmp_path / "test.alps.xml"
        result = doc_service.init_document("TestProject", str(doc_path))
        assert "Created" in result
        assert doc_path.exists()
        assert doc_service.working_doc == doc_path

    def test_adds_suffix_if_missing(self, tmp_path, doc_service):
        doc_path = tmp_path / "test"
        doc_service.init_document("Test", str(doc_path))
        assert (tmp_path / "test.alps.xml").exists()

    def test_existing_document_not_overwritten(self, tmp_path, doc_service):
        doc_path = tmp_path / "test.alps.xml"
        doc_path.write_text("existing content")
        result = doc_service.init_document("Test", str(doc_path))
        assert "already exists" in result
        assert doc_path.read_text() == "existing content"


class TestLoadDocument:
    def test_loads_existing_document(self, temp_doc, doc_service):
        new_service = DocumentService()
        result = new_service.load_document(str(temp_doc))
        assert "ALPS Document: Test" in result
        assert new_service.working_doc == temp_doc

    def test_returns_error_for_missing_file(self, tmp_path, doc_service):
        result = doc_service.load_document(str(tmp_path / "nonexistent.md"))
        assert "not found" in result


class TestSaveAndReadSection:
    def test_save_and_read_section(self, temp_doc, doc_service):
        doc_service.save_section(1, "New overview content")
        content = doc_service.read_section(1)
        assert "New overview content" in content
        assert "## Section 1. Overview" in content

    def test_save_preserves_other_sections(self, temp_doc, doc_service):
        doc_service.save_section(1, "Section 1 content")
        doc_service.save_section(2, "Section 2 content")
        assert "Section 1 content" in doc_service.read_section(1)
        assert "Section 2 content" in doc_service.read_section(2)

    def test_save_without_loaded_doc_returns_error(self):
        service = DocumentService()
        result = service.save_section(1, "content")
        assert "No document loaded" in result

    def test_invalid_section_number(self, temp_doc, doc_service):
        assert "Invalid section" in doc_service.save_section(10, "x")
        assert "not found" in doc_service.read_section(0)


class TestDocumentStatus:
    def test_status_shows_not_started(self, temp_doc, doc_service):
        status = doc_service.get_status()
        assert "⬜ Not started" in status

    def test_status_shows_written_after_save(self, temp_doc, doc_service):
        doc_service.save_section(1, "A" * 100)  # >50 chars
        status = doc_service.get_status()
        assert "Section 1 (Overview): ✅ Written" in status


class TestExportMarkdown:
    def test_export_removes_xml_tags(self, temp_doc, doc_service):
        doc_service.save_section(1, "Overview content")
        result = doc_service.export_markdown()
        assert "<section" not in result
        assert "</section>" not in result
        assert "## Section 1. Overview" in result
        assert "Overview content" in result

    def test_export_to_file(self, temp_doc, doc_service, tmp_path):
        out_path = tmp_path / "export.md"
        result = doc_service.export_markdown(str(out_path))
        assert "Exported" in result
        assert out_path.exists()

    def test_not_started_shows_placeholder(self, temp_doc, doc_service):
        result = doc_service.export_markdown()
        assert "*Not yet written*" in result


class TestInteractiveWorkflowGuide:
    def test_overview_contains_interactive_process_warning(self, template_service):
        result = template_service.get_overview()
        assert "NEVER auto-generate" in result

    def test_overview_mentions_reference_document_handling(self, template_service):
        result = template_service.get_overview()
        assert "PDF" in result or "reference" in result.lower()

    def test_overview_contains_section_reference_rules(self, template_service):
        result = template_service.get_overview()
        assert "Section Reference Rules" in result
        assert "MUST review" in result


class TestSectionReferences:
    def test_section_references_map_exists(self):
        assert SECTION_REFERENCES[3] == [2]
        assert SECTION_REFERENCES[5] == [6]
        assert SECTION_REFERENCES[7] == [6]
        assert SECTION_REFERENCES[8] == [2, 6]

    def test_sections_without_references(self):
        for section in [1, 2, 4, 6, 9]:
            assert section not in SECTION_REFERENCES

    def test_guide_with_references_includes_warning(self, template_service):
        for section in [3, 5, 7, 8]:
            guide = template_service.get_section_guide(section)
            assert "REQUIRED" in guide
            assert "read_alps_section" in guide

    def test_guide_without_references_no_warning(self, template_service):
        for section in [1, 2, 4, 6, 9]:
            guide = template_service.get_section_guide(section)
            assert "⚠️ REQUIRED: This section depends on" not in guide

    def test_section_3_references_section_2(self, template_service):
        guide = template_service.get_section_guide(3)
        assert "Section 2" in guide
        assert "MVP Goals" in guide

    def test_section_7_references_section_6(self, template_service):
        guide = template_service.get_section_guide(7)
        assert "Section 6" in guide
        assert "Requirements" in guide

    def test_section_8_references_multiple_sections(self, template_service):
        guide = template_service.get_section_guide(8)
        assert "Section 2" in guide
        assert "Section 6" in guide
