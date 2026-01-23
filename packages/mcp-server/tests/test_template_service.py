"""Tests for TemplateService."""

import pytest
from alps_mcp_server.tools.templates.service import TemplateService


@pytest.fixture
def service():
    return TemplateService()


def test_get_overview(service):
    result = service.get_overview()
    assert "ALPS" in result
    assert len(result) > 100


def test_list_sections(service):
    result = service.list_sections()
    assert len(result) == 9
    assert result[0]["section"] == 1


def test_get_section(service):
    result = service.get_section(1)
    assert "Overview" in result


def test_get_section_not_found(service):
    result = service.get_section(99)
    assert "not found" in result


def test_get_section_guide(service):
    result = service.get_section_guide(1)
    assert "section_guide" in result
    assert "Overview" in result


def test_get_section_guide_with_refs(service):
    result = service.get_section_guide(3)
    assert "REQUIRED" in result
    assert "Section 2" in result
