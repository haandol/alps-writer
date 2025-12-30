"""ALPS Writer MCP Server - Provides ALPS template tools for spec writing."""

import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP

TEMPLATES_DIR = Path(__file__).parent / "templates"
CHAPTERS_DIR = TEMPLATES_DIR / "chapters"

# Current working document path
WORKING_DOC: Path | None = None

mcp = FastMCP(
    "alps-writer",
    instructions="""You are an intelligent product owner helping users create ALPS documents.

<WORKFLOW>
1. init_alps_document() or load_alps_document()
2. get_alps_overview() - MUST call first to get conversation guide
3. For each section 1-9:
   a. get_alps_section_guide(N)
   b. get_alps_section(N)
   c. Follow conversation guide from overview
   d. save_alps_section(N, content) after user confirmation
5. export_alps_markdown() for final output
</WORKFLOW>

<RULES>
- MUST call get_alps_overview() first to get detailed conversation guide
- NEVER generate multiple sections at once
- NEVER proceed without user confirmation
</RULES>"""
)

SECTION_REFERENCES = {
    3: [2],      # Demo Scenario → MVP Goals
    5: [6],      # Design Spec → Requirements Summary
    7: [6],      # Feature Spec → Requirements Summary
    8: [2, 6],   # MVP Metrics → MVP Goals, Requirements (NFRs)
}

SECTION_GUIDES = {
    1: """<section_guide number="1" title="Overview">
<purpose>제품 비전, 타겟 사용자, 핵심 문제, 솔루션 전략, 성공 기준, 차별점 정의</purpose>

<questions>
1. 프로젝트의 주요 목적은 무엇인가요?
2. 공식 프로젝트 이름은 무엇인가요?
3. 타겟 사용자는 누구인가요?
4. 해결하려는 핵심 문제는 무엇인가요?
5. 솔루션 전략과 핵심 차별점은?
</questions>

<completion>모든 항목 작성 후 전체 섹션 출력, 사용자 확인 받기</completion>
</section_guide>""",

    2: """<section_guide number="2" title="MVP Goals and Key Metrics">
<purpose>MVP 가설을 검증할 2-5개의 측정 가능한 목표 정의</purpose>

<questions>
1. MVP로 검증하려는 핵심 가설은 무엇인가요?
2. 이를 검증할 측정 가능한 목표 2-5개를 정의해주세요
3. 각 목표의 baseline(현재)과 target(목표) 값은?
</questions>

<completion>정량적 지표 포함된 목표 작성 후 확인</completion>
</section_guide>""",

    3: """<section_guide number="3" title="Demo Scenario" references="2">
<purpose>핵심 가설을 검증할 수 있는 데모 시나리오 작성</purpose>

<required_review>
📋 MUST review Section 2 (MVP Goals) before writing this section.
Call read_alps_section(2) and summarize key goals before proceeding.
</required_review>

<questions>
1. Section 2의 목표를 어떻게 시연할 수 있을까요?
2. 데모의 시작점과 끝점은?
3. 핵심 사용자 여정은?
</questions>

<completion required="true">Section 2와 정렬된 시나리오 작성 후 반드시 확인 필요</completion>
</section_guide>""",

    4: """<section_guide number="4" title="High-Level Architecture">
<purpose>C4 모델의 Context, Container 다이어그램으로 시스템 아키텍처 설명</purpose>

<questions>
1. 시스템의 주요 컴포넌트는 무엇인가요?
2. 외부 시스템/서비스 연동은?
3. 기술 스택 선택 이유는?
</questions>

<completion>Context/Container 다이어그램 설명 포함</completion>
</section_guide>""",

    5: """<section_guide number="5" title="Design Specification" references="6">
<purpose>UX, 페이지 플로우, 주요 화면, 사용자 여정 상세화</purpose>

<required_review>
📋 MUST review Section 6 (Requirements Summary) before writing this section.
Call read_alps_section(6) and list Feature IDs (F1, F2...) to use in Key Pages.
</required_review>

<questions>
1. 주요 화면(페이지)은 몇 개인가요?
2. 각 화면의 핵심 기능은? (Section 6의 Feature ID 사용)
3. 화면 간 네비게이션 흐름은?
</questions>

<completion>주요 화면과 플로우 정의 (Feature ID 매핑 포함)</completion>
</section_guide>""",

    6: """<section_guide number="6" title="Requirements Summary">
<purpose>기능/비기능 요구사항 열거, 우선순위 지정</purpose>

<questions>
1. 핵심 기능 요구사항을 나열해주세요
2. 각 요구사항의 우선순위는? (Must-Have / Should-Have / Nice-to-Have)
3. 비기능 요구사항은? (최대 3개)
</questions>

<important>각 기능 요구사항에 고유 ID 부여 (F1, F2, ...)</important>
<completion required="true">모든 요구사항 ID 부여 후 반드시 확인 필요</completion>
</section_guide>""",

    7: """<section_guide number="7" title="Feature-Level Specification" references="6">
<purpose>Section 6의 각 요구사항에 대한 상세 사용자 스토리 작성</purpose>

<required_review>
📋 MUST review Section 6 (Requirements Summary) before writing this section.
Call read_alps_section(6) and confirm all Feature IDs (F1, F2...) to map 1:1.
</required_review>

<questions repeat="each_feature">
1. 사용자 스토리: "As a [역할], I want to [행동] so that [이점]"
2. 기능 범위와 엣지 케이스는?
3. 에러 처리 방법은?
4. 인수 기준(Acceptance Criteria)은?
</questions>

<important>
- Section 6의 요구사항 ID와 1:1 매핑 필수
- 각 7.x 서브섹션마다 개별 확인 필요
</important>
<completion>모든 F1, F2... 에 대응하는 7.1, 7.2... 작성</completion>
</section_guide>""",

    8: """<section_guide number="8" title="MVP Metrics" references="2,6">
<purpose>데이터 수집/분석 방법, 성공 임계값 정의</purpose>

<required_review>
📋 MUST review referenced sections before writing:
- Section 2 (MVP Goals): Call read_alps_section(2) for KPIs to measure
- Section 6.2 (Non-Functional Requirements): Call read_alps_section(6) for NFRs to validate
</required_review>

<questions>
1. Section 2의 각 목표를 어떻게 측정할 건가요?
2. 데이터 수집 방법은?
3. 성공/실패 판단 기준은?
</questions>

<completion>각 KPI별 측정 방법과 임계값 정의</completion>
</section_guide>""",

    9: """<section_guide number="9" title="Out of Scope">
<purpose>향후 반복에서 다룰 기능, 기술 부채 로드맵</purpose>

<questions>
1. MVP에서 제외된 기능은?
2. 향후 개선 계획은?
3. 알려진 기술 부채는?
</questions>

<completion>제외 항목과 향후 로드맵 정리</completion>
</section_guide>""",
}


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _list_chapters() -> list[dict]:
    """List all chapter files with their section numbers."""
    chapters = []
    for f in sorted(CHAPTERS_DIR.glob("*.md")):
        num = f.stem.split("-")[0]
        chapters.append({"section": int(num), "filename": f.name})
    return chapters


@mcp.tool()
def get_alps_overview() -> str:
    """Get the ALPS template overview with all section descriptions.
    
    IMPORTANT: After calling this, you MUST call get_alps_section_guide(1) 
    to start the interactive Q&A process. Never auto-generate sections.
    """
    content = _read_file(TEMPLATES_DIR / "overview.md")
    return content + """

---
## Next Step

**REQUIRED**: Call `get_alps_section_guide(1)` to begin interactive writing.
Do NOT write any section without going through the guide's Q&A process first."""


@mcp.tool()
def list_alps_sections() -> list[dict]:
    """List all available ALPS template sections.
    
    Returns:
        List of sections with section number and filename.
    """
    return _list_chapters()


@mcp.tool()
def get_alps_section(section: int) -> str:
    """Get a specific ALPS template section by number.
    
    Args:
        section: Section number (1-9)
    
    Returns:
        The section template content.
    """
    for f in CHAPTERS_DIR.glob(f"{section:02d}-*.md"):
        return _read_file(f)
    return f"Section {section} not found."


@mcp.tool()
def get_alps_full_template() -> str:
    """Get the complete ALPS template with all sections combined."""
    parts = [_read_file(TEMPLATES_DIR / "overview.md"), "\n---\n"]
    for f in sorted(CHAPTERS_DIR.glob("*.md")):
        parts.append(_read_file(f))
        parts.append("\n---\n")
    return "\n".join(parts)


@mcp.tool()
def get_alps_section_guide(section: int) -> str:
    """Get conversation guide for writing a specific ALPS section.
    
    Use this before starting each section to guide the interactive conversation.
    Returns questions to ask, completion criteria, and important notes.
    For sections with dependencies, includes required review instructions.
    
    Args:
        section: Section number (1-9)
    
    Returns:
        Conversation guide with questions and completion criteria.
    """
    guide = SECTION_GUIDES.get(section)
    if not guide:
        return f"Section {section} not found."
    
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


# ============ File-based Document Management Tools ============

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


def _parse_sections(content: str) -> dict[int, str]:
    """Parse XML-tagged sections from document content.
    
    Returns section content WITHOUT the header (## Section N. Title).
    """
    sections = {}
    pattern = r'<section id="(\d+)">\s*## Section \d+\.[^\n]*\n+(.*?)</section>'
    for match in re.finditer(pattern, content, re.DOTALL):
        sections[int(match.group(1))] = match.group(2).strip()
    return sections


def _build_document(project_name: str, sections: dict[int, str]) -> str:
    """Build full document with XML section tags."""
    lines = [f"# {project_name} ALPS\n"]
    for num in range(1, 10):
        content = sections.get(num, "<!-- Not started -->")
        lines.append(f'<section id="{num}">\n## Section {num}. {SECTION_TITLES[num]}\n\n{content}\n</section>\n')
    return "\n".join(lines)


def _extract_project_name(content: str) -> str:
    """Extract project name from document header."""
    match = re.match(r"# (.+?) ALPS", content)
    return match.group(1) if match else "Untitled"


@mcp.tool()
def init_alps_document(project_name: str, output_path: str) -> str:
    """Initialize a new ALPS document file.
    
    Args:
        project_name: Name of the project
        output_path: File path for the document (e.g., ~/Documents/my-project.alps.md)
    
    Returns:
        Confirmation with file path.
    """
    global WORKING_DOC
    
    filepath = Path(output_path).expanduser()
    if not filepath.suffix:
        filepath = filepath.with_suffix(".alps.md")
    
    if filepath.exists():
        WORKING_DOC = filepath
        return f"Document already exists at {filepath}. Use load_alps_document() to resume."
    
    filepath.parent.mkdir(parents=True, exist_ok=True)
    content = _build_document(project_name, {})
    filepath.write_text(content, encoding="utf-8")
    
    WORKING_DOC = filepath
    return f"Created ALPS document at {filepath}"


@mcp.tool()
def load_alps_document(doc_path: str) -> str:
    """Load an existing ALPS document to resume editing.
    
    Args:
        doc_path: Path to the .alps.md file
    
    Returns:
        Document status summary.
    """
    global WORKING_DOC
    
    filepath = Path(doc_path).expanduser()
    if not filepath.exists():
        return f"Document not found at {filepath}"
    
    WORKING_DOC = filepath
    return get_alps_document_status()


@mcp.tool()
def save_alps_section(section: int, content: str) -> str:
    """Save content to a specific section in the ALPS document.
    
    Args:
        section: Section number (1-9)
        content: Markdown content for the section (without header)
    
    Returns:
        Confirmation message.
    """
    if WORKING_DOC is None:
        return "No document loaded. Call init_alps_document() or load_alps_document() first."
    
    if section not in SECTION_TITLES:
        return f"Invalid section number: {section}. Must be 1-9."
    
    doc_content = WORKING_DOC.read_text(encoding="utf-8")
    project_name = _extract_project_name(doc_content)
    sections = _parse_sections(doc_content)
    sections[section] = content
    
    WORKING_DOC.write_text(_build_document(project_name, sections), encoding="utf-8")
    return f"Saved section {section} to {WORKING_DOC}"


@mcp.tool()
def read_alps_section(section: int) -> str:
    """Read the current content of a specific section.
    
    Args:
        section: Section number (1-9)
    
    Returns:
        Current content of the section.
    """
    if WORKING_DOC is None:
        return "No document loaded. Call init_alps_document() or load_alps_document() first."
    
    sections = _parse_sections(WORKING_DOC.read_text(encoding="utf-8"))
    return sections.get(section, f"Section {section} not found.")


@mcp.tool()
def get_alps_document_status() -> str:
    """Get the status of all sections in the current document.
    
    Returns:
        Status summary showing which sections are completed/in-progress/not-started.
    """
    if WORKING_DOC is None:
        return "No document loaded. Call init_alps_document() or load_alps_document() first."
    
    doc_content = WORKING_DOC.read_text(encoding="utf-8")
    project_name = _extract_project_name(doc_content)
    sections = _parse_sections(doc_content)
    
    lines = [f"ALPS Document: {project_name}", f"Location: {WORKING_DOC}", ""]
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


@mcp.tool()
def export_alps_markdown(output_path: str | None = None) -> str:
    """Export the ALPS document as clean markdown (without XML tags).
    
    Args:
        output_path: Optional output file path. If not provided, returns the content.
    
    Returns:
        Clean markdown content or confirmation message.
    """
    if WORKING_DOC is None:
        return "No document loaded. Call init_alps_document() or load_alps_document() first."
    
    doc_content = WORKING_DOC.read_text(encoding="utf-8")
    project_name = _extract_project_name(doc_content)
    sections = _parse_sections(doc_content)
    
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


def main():
    mcp.run()


if __name__ == "__main__":
    main()
