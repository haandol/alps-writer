"""Document service - business logic for ALPS document management."""

import re
from pathlib import Path

from alps_mcp_server.interfaces.constants import SECTION_TITLES


class DocumentService:
    def __init__(self):
        self._working_doc: Path | None = None

    @property
    def working_doc(self) -> Path | None:
        return self._working_doc

    def _parse_sections(self, content: str) -> dict[int, str]:
        sections = {}
        pattern = r'<section id="(\d+)">\s*## Section \d+\.[^\n]*\n+(.*?)</section>'
        for match in re.finditer(pattern, content, re.DOTALL):
            sections[int(match.group(1))] = match.group(2).strip()
        return sections

    def _parse_subsections(self, content: str) -> dict[int, str]:
        subsections = {}
        pattern = r'<subsection id="7\.(\d+)">\s*(.*?)</subsection>'
        for match in re.finditer(pattern, content, re.DOTALL):
            subsections[int(match.group(1))] = match.group(2).strip()
        return subsections

    def _build_section7(self, subsections: dict[int, str]) -> str:
        return "\n\n".join(
            f'<subsection id="7.{num}">\n{subsections[num]}\n</subsection>'
            for num in sorted(subsections.keys())
        )

    def _build_document(self, project_name: str, sections: dict[int, str]) -> str:
        lines = [f"# {project_name} ALPS\n"]
        for num in range(1, 10):
            content = sections.get(num, "<!-- Not started -->")
            lines.append(f'<section id="{num}">\n## Section {num}. {SECTION_TITLES[num]}\n\n{content}\n</section>\n')
        return "\n".join(lines)

    def _extract_project_name(self, content: str) -> str:
        match = re.match(r"# (.+?) ALPS", content)
        return match.group(1) if match else "Untitled"

    def init_document(self, project_name: str, output_path: str) -> str:
        filepath = Path(output_path).expanduser()
        if not filepath.suffix:
            filepath = filepath.with_suffix(".alps.md")
        
        if filepath.exists():
            self._working_doc = filepath
            return f"Document already exists at {filepath}. Use load_alps_document() to resume."
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(self._build_document(project_name, {}), encoding="utf-8")
        self._working_doc = filepath
        return f"Created ALPS document at {filepath}"

    def load_document(self, doc_path: str) -> str:
        filepath = Path(doc_path).expanduser()
        if not filepath.exists():
            return f"Document not found at {filepath}"
        self._working_doc = filepath
        return self.get_status()

    def save_section(self, section: int, content: str, subsection: int | None = None) -> str:
        if self._working_doc is None:
            return "No document loaded. Call init_alps_document() or load_alps_document() first."
        if section not in SECTION_TITLES:
            return f"Invalid section number: {section}. Must be 1-9."
        
        doc_content = self._working_doc.read_text(encoding="utf-8")
        project_name = self._extract_project_name(doc_content)
        sections = self._parse_sections(doc_content)
        
        if section == 7 and subsection is None:
            return "ERROR: Section 7 requires subsection parameter. Use save_alps_section(7, content, subsection=N) where N is the feature number (1, 2, 3...)."
        
        if section == 7 and subsection is not None:
            subsections = self._parse_subsections(sections.get(7, ""))
            subsections[subsection] = content
            sections[7] = self._build_section7(subsections)
            msg = f"Saved subsection 7.{subsection} to {self._working_doc}"
        else:
            sections[section] = content
            msg = f"Saved section {section} to {self._working_doc}"
        
        self._working_doc.write_text(self._build_document(project_name, sections), encoding="utf-8")
        return msg

    def read_section(self, section: int) -> str:
        if self._working_doc is None:
            return "No document loaded. Call init_alps_document() or load_alps_document() first."
        sections = self._parse_sections(self._working_doc.read_text(encoding="utf-8"))
        return sections.get(section, f"Section {section} not found.")

    def get_status(self) -> str:
        if self._working_doc is None:
            return "No document loaded. Call init_alps_document() or load_alps_document() first."
        
        doc_content = self._working_doc.read_text(encoding="utf-8")
        project_name = self._extract_project_name(doc_content)
        sections = self._parse_sections(doc_content)
        
        lines = [f"ALPS Document: {project_name}", f"Location: {self._working_doc}", ""]
        for num, title in SECTION_TITLES.items():
            content = sections.get(num, "")
            if not content or "<!-- Not started -->" in content:
                status = "⬜ Not started"
            elif len(content.strip()) > 50:
                status = "✅ Written"
            else:
                status = "🟡 In progress"
            lines.append(f"Section {num} ({title}): {status}")
        return "\n".join(lines)

    def export_markdown(self, output_path: str | None = None) -> str:
        if self._working_doc is None:
            return "No document loaded. Call init_alps_document() or load_alps_document() first."
        
        doc_content = self._working_doc.read_text(encoding="utf-8")
        project_name = self._extract_project_name(doc_content)
        sections = self._parse_sections(doc_content)
        
        lines = [f"# {project_name} ALPS\n"]
        for num in range(1, 10):
            content = sections.get(num, "")
            if not content or "<!-- Not started -->" in content:
                content = "*Not yet written*"
            lines.append(f"## Section {num}. {SECTION_TITLES[num]}\n\n{content}\n\n---\n")
        
        result = "\n".join(lines)
        if output_path:
            out = Path(output_path).expanduser()
            out.write_text(result, encoding="utf-8")
            return f"Exported to {out}"
        return result
