"""Template service - business logic for ALPS templates."""

import xml.etree.ElementTree as ET
from alps_mcp_server.interfaces.constants import TEMPLATES_DIR, CHAPTERS_DIR, GUIDES_DIR, SECTION_TITLES, SECTION_REFERENCES


class TemplateService:
    def _xml_to_markdown(self, content: str, include_examples: bool = True) -> str:
        """Convert XML format to clean markdown."""
        root = ET.fromstring(content)
        lines = []
        self._render_element(root, lines, 2, include_examples)
        return "\n".join(lines).strip()

    def _render_element(self, el: ET.Element, lines: list, level: int, include_examples: bool):
        """Recursively render XML element to markdown."""
        if el.tag == "example":
            if include_examples:
                lines.append(f"\n**Example:**\n{(el.text or '').strip()}\n")
            return
        if el.tag == "description":
            lines.append(f"\n{(el.text or '').strip()}\n")
            return
        if el.tag == "header":
            lines.append(f"\n> {(el.text or '').strip()}\n")
            return

        # section, subsection, template
        if el.tag in ("section", "subsection", "template"):
            title = el.get("title", "")
            id_ = el.get("id", "")
            if title:
                lines.append(f"{'#' * level} {id_} {title}\n" if id_ else f"{'#' * level} {title}\n")
            for child in el:
                self._render_element(child, lines, level + 1, include_examples)

    def get_overview(self) -> str:
        return (TEMPLATES_DIR / "overview.md").read_text(encoding="utf-8")

    def list_sections(self) -> list[dict]:
        return [
            {"section": int(f.stem.split("-")[0]), "filename": f.name}
            for f in sorted(CHAPTERS_DIR.glob("*.xml"))
        ]

    def get_section(self, section: int, include_examples: bool = True) -> str:
        for f in CHAPTERS_DIR.glob(f"{section:02d}-*.xml"):
            return self._xml_to_markdown(f.read_text(encoding="utf-8"), include_examples)
        return f"Section {section} not found."

    def get_full_template(self, include_examples: bool = True) -> str:
        parts = [self.get_overview(), "\n---\n"]
        for f in sorted(CHAPTERS_DIR.glob("*.xml")):
            parts.append(self._xml_to_markdown(f.read_text(encoding="utf-8"), include_examples))
            parts.append("\n---\n")
        return "\n".join(parts)

    def get_section_guide(self, section: int) -> str:
        guide_file = GUIDES_DIR / f"{section:02d}.md"
        if not guide_file.exists():
            return f"Section {section} not found."
        
        guide = guide_file.read_text(encoding="utf-8")
        refs = SECTION_REFERENCES.get(section)
        if refs:
            ref_names = [f"Section {r} ({SECTION_TITLES[r]})" for r in refs]
            warning = f"""⚠️ REQUIRED: This section depends on {', '.join(ref_names)}.
Before proceeding, you MUST:
1. Call read_alps_section({refs[0]}) to review referenced content
2. Summarize key points from referenced section(s) in your response
3. If referenced sections are incomplete, warn the user first

"""
            return warning + guide
        return guide
