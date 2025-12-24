"""ALPS Writer MCP Server - Provides ALPS template tools for spec writing."""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

TEMPLATES_DIR = Path(__file__).parent / "templates"
CHAPTERS_DIR = TEMPLATES_DIR / "chapters"

mcp = FastMCP("alps-writer")

SECTION_GUIDES = {
    1: """## Section 1. Overview - 대화 가이드

**목적**: 제품 비전, 타겟 사용자, 핵심 문제, 솔루션 전략, 성공 기준, 차별점 정의

**질문 순서**:
1. 프로젝트의 주요 목적은 무엇인가요?
2. 공식 프로젝트 이름은 무엇인가요?
3. 타겟 사용자는 누구인가요?
4. 해결하려는 핵심 문제는 무엇인가요?
5. 솔루션 전략과 핵심 차별점은?

**완료 기준**: 모든 항목 작성 후 전체 섹션 출력, 사용자 확인 받기""",

    2: """## Section 2. MVP Goals and Key Metrics - 대화 가이드

**목적**: MVP 가설을 검증할 2-5개의 측정 가능한 목표 정의

**질문 순서**:
1. MVP로 검증하려는 핵심 가설은 무엇인가요?
2. 이를 검증할 측정 가능한 목표 2-5개를 정의해주세요
3. 각 목표의 baseline(현재)과 target(목표) 값은?

**완료 기준**: 정량적 지표 포함된 목표 작성 후 확인""",

    3: """## Section 3. Demo Scenario - 대화 가이드

**목적**: 핵심 가설을 검증할 수 있는 데모 시나리오 작성

**질문 순서**:
1. Section 2의 목표를 어떻게 시연할 수 있을까요?
2. 데모의 시작점과 끝점은?
3. 핵심 사용자 여정은?

**완료 기준**: Section 2와 정렬된 시나리오 작성 후 **반드시 확인 필요**""",

    4: """## Section 4. High-Level Architecture - 대화 가이드

**목적**: C4 모델의 Context, Container 다이어그램으로 시스템 아키텍처 설명

**질문 순서**:
1. 시스템의 주요 컴포넌트는 무엇인가요?
2. 외부 시스템/서비스 연동은?
3. 기술 스택 선택 이유는?

**완료 기준**: Context/Container 다이어그램 설명 포함""",

    5: """## Section 5. Design Specification - 대화 가이드

**목적**: UX, 페이지 플로우, 주요 화면, 사용자 여정 상세화

**질문 순서**:
1. 주요 화면(페이지)은 몇 개인가요?
2. 각 화면의 핵심 기능은?
3. 화면 간 네비게이션 흐름은?

**완료 기준**: 주요 화면과 플로우 정의""",

    6: """## Section 6. Requirements Summary - 대화 가이드

**목적**: 기능/비기능 요구사항 열거, 우선순위 지정

**질문 순서**:
1. 핵심 기능 요구사항을 나열해주세요
2. 각 요구사항의 우선순위는? (Must-Have / Should-Have / Nice-to-Have)
3. 비기능 요구사항은? (최대 3개)

**중요**: 각 기능 요구사항에 고유 ID 부여 (F1, F2, ...)
**완료 기준**: 모든 요구사항 ID 부여 후 **반드시 확인 필요**""",

    7: """## Section 7. Feature-Level Specification - 대화 가이드

**목적**: Section 6의 각 요구사항에 대한 상세 사용자 스토리 작성

**질문 순서** (각 기능별 반복):
1. 사용자 스토리: "As a [역할], I want to [행동] so that [이점]"
2. 기능 범위와 엣지 케이스는?
3. 에러 처리 방법은?
4. 인수 기준(Acceptance Criteria)은?

**중요**: 
- Section 6의 요구사항 ID와 1:1 매핑 필수
- 각 7.x 서브섹션마다 **개별 확인 필요**

**완료 기준**: 모든 F1, F2... 에 대응하는 7.1, 7.2... 작성""",

    8: """## Section 8. MVP Metrics - 대화 가이드

**목적**: 데이터 수집/분석 방법, 성공 임계값 정의

**질문 순서**:
1. Section 2의 각 목표를 어떻게 측정할 건가요?
2. 데이터 수집 방법은?
3. 성공/실패 판단 기준은?

**완료 기준**: 각 KPI별 측정 방법과 임계값 정의""",

    9: """## Section 9. Out of Scope - 대화 가이드

**목적**: 향후 반복에서 다룰 기능, 기술 부채 로드맵

**질문 순서**:
1. MVP에서 제외된 기능은?
2. 향후 개선 계획은?
3. 알려진 기술 부채는?

**완료 기준**: 제외 항목과 향후 로드맵 정리""",
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
    """Get the ALPS template overview with all section descriptions."""
    return _read_file(TEMPLATES_DIR / "overview.md")


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
    
    Args:
        section: Section number (1-9)
    
    Returns:
        Conversation guide with questions and completion criteria.
    """
    return SECTION_GUIDES.get(section, f"Section {section} not found.")


def main():
    mcp.run()


if __name__ == "__main__":
    main()
