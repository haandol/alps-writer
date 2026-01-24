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
        # 새 형식: <section id="N" title="...">
        pattern = r'<section id="(\d+)" title="[^"]*">\s*(.*?)</section>'
        for match in re.finditer(pattern, content, re.DOTALL):
            sections[int(match.group(1))] = match.group(2).strip()
        # 구 형식 호환: <section id="N">\n## Section N. Title
        if not sections:
            pattern = r'<section id="(\d+)">\s*## Section \d+\.[^\n]*\n+(.*?)</section>'
            for match in re.finditer(pattern, content, re.DOTALL):
                sections[int(match.group(1))] = match.group(2).strip()
        return sections

    def _parse_subsections(self, section_content: str, section_id: int) -> dict[str, str]:
        """Parse subsections from section content. Returns {subsection_id: content}."""
        subsections = {}
        pattern = rf'<subsection id="{section_id}\.([^"]+)" title="([^"]*)">\s*(.*?)</subsection>'
        for match in re.finditer(pattern, section_content, re.DOTALL):
            sub_id = f"{section_id}.{match.group(1)}"
            subsections[sub_id] = {"title": match.group(2), "content": match.group(3).strip()}
        return subsections

    def _build_subsection(self, sub_id: str, title: str, content: str) -> str:
        return f'<subsection id="{sub_id}" title="{title}">\n{content}\n</subsection>'

    def _build_section(self, section_id: int, content: str) -> str:
        return f'<section id="{section_id}" title="{SECTION_TITLES[section_id]}">\n{content}\n</section>'

    def _build_document(self, project_name: str, sections: dict[int, str]) -> str:
        lines = [f'<alps-document project="{project_name}">']
        for num in range(1, 10):
            content = sections.get(num, "<!-- Not started -->")
            lines.append(self._build_section(num, content))
        lines.append("</alps-document>")
        return "\n\n".join(lines)

    def _extract_project_name(self, content: str) -> str:
        # 새 형식
        match = re.search(r'<alps-document project="([^"]+)">', content)
        if match:
            return match.group(1)
        # 구 형식 호환
        match = re.match(r"# (.+?) ALPS", content)
        return match.group(1) if match else "Untitled"

    def init_document(self, project_name: str, output_path: str) -> str:
        filepath = Path(output_path).expanduser()
        if not filepath.suffix:
            filepath = filepath.with_suffix(".alps.xml")
        
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
        status = self.get_status()
        return f"""{status}

---
⚠️ CONVERSATION MODE REQUIRED:
1. Call get_alps_section_guide(N) before working on any section
2. Ask 1-2 focused questions at a time - DO NOT auto-generate content
3. Wait for user response before proceeding
4. Get explicit "yes" confirmation before calling save_alps_section()
NEVER auto-fill sections without user Q&A, even if content already exists."""

    def save_section(self, section: int, subsection_id: str, title: str, content: str) -> str:
        """Save content to a subsection."""
        if self._working_doc is None:
            return "No document loaded. Call init_alps_document() or load_alps_document() first."
        if section not in SECTION_TITLES:
            return f"Invalid section number: {section}. Must be 1-9."
        
        doc_content = self._working_doc.read_text(encoding="utf-8")
        project_name = self._extract_project_name(doc_content)
        sections = self._parse_sections(doc_content)
        
        sub_id = f"{section}.{subsection_id}"
        existing = self._parse_subsections(sections.get(section, ""), section)
        existing[sub_id] = {"title": title, "content": content}
        
        parts = [self._build_subsection(k, v["title"], v["content"]) 
                 for k, v in sorted(existing.items())]
        sections[section] = "\n".join(parts)
        
        self._working_doc.write_text(self._build_document(project_name, sections), encoding="utf-8")
        return f"Saved {sub_id}. {title}"

    def read_section(self, section: int, subsection_id: str | None = None) -> str:
        if self._working_doc is None:
            return "No document loaded. Call init_alps_document() or load_alps_document() first."
        if section not in SECTION_TITLES:
            return f"Section {section} not found."
        sections = self._parse_sections(self._working_doc.read_text(encoding="utf-8"))
        content = sections.get(section, "")
        
        if subsection_id is not None:
            sub_id = f"{section}.{subsection_id}"
            subs = self._parse_subsections(content, section)
            if sub_id in subs:
                return f"## {sub_id}. {subs[sub_id]['title']}\n\n{subs[sub_id]['content']}"
            return f"Subsection {sub_id} not found."
        
        if not content or "<!-- Not started -->" in content:
            content = "*Not yet written*"
        return f"## Section {section}. {SECTION_TITLES[section]}\n\n{content}"

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

    def _content_to_markdown(self, content: str, section: int) -> str:
        """Convert section content (with subsection tags) to clean markdown."""
        subs = self._parse_subsections(content, section)
        if not subs:
            return content
        lines = []
        for sub_id, data in sorted(subs.items()):
            lines.append(f"### {sub_id}. {data['title']}\n\n{data['content']}")
        return "\n\n".join(lines)

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
                md_content = "*Not yet written*"
            else:
                md_content = self._content_to_markdown(content, num)
            lines.append(f"## Section {num}. {SECTION_TITLES[num]}\n\n{md_content}\n\n---\n")
        
        result = "\n".join(lines)
        if output_path:
            out = Path(output_path).expanduser()
            out.write_text(result, encoding="utf-8")
            return f"Exported to {out}"
        return result
