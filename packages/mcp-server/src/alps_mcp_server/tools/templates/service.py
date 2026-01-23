"""Template service - business logic for ALPS templates."""

from alps_mcp_server.interfaces.constants import TEMPLATES_DIR, CHAPTERS_DIR, GUIDES_DIR, SECTION_TITLES, SECTION_REFERENCES


class TemplateService:
    def get_overview(self) -> str:
        return (TEMPLATES_DIR / "overview.md").read_text(encoding="utf-8")

    def list_sections(self) -> list[dict]:
        return [
            {"section": int(f.stem.split("-")[0]), "filename": f.name}
            for f in sorted(CHAPTERS_DIR.glob("*.md"))
        ]

    def get_section(self, section: int) -> str:
        for f in CHAPTERS_DIR.glob(f"{section:02d}-*.md"):
            return f.read_text(encoding="utf-8")
        return f"Section {section} not found."

    def get_full_template(self) -> str:
        parts = [self.get_overview(), "\n---\n"]
        for f in sorted(CHAPTERS_DIR.glob("*.md")):
            parts.append(f.read_text(encoding="utf-8"))
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
