"""Constants for ALPS MCP Server."""

from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
CHAPTERS_DIR = TEMPLATES_DIR / "chapters"
GUIDES_DIR = Path(__file__).parent.parent / "guides"

SECTION_TITLES = {
    1: "Overview",
    2: "MVP Goals and Key Metrics",
    3: "Demo Scenario",
    4: "High-Level Architecture",
    5: "Design Specification",
    6: "Requirements Summary",
    7: "Feature-Level Specification",
    8: "MVP Metrics",
    9: "Out of Scope",
}

SECTION_REFERENCES = {
    3: [2],      # Demo Scenario → MVP Goals
    5: [6],      # Design Spec → Requirements Summary
    7: [6],      # Feature Spec → Requirements Summary
    8: [2, 6],   # MVP Metrics → MVP Goals, Requirements (NFRs)
}
