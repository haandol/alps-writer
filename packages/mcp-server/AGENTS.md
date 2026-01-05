# ALPS Writer MCP Server Package Guide

## Overview

ALPS 템플릿 도구를 제공하는 MCP (Model Context Protocol) 서버입니다.
Claude Desktop, Cursor 등 MCP 호환 클라이언트에서 사용할 수 있습니다.

## Directory Structure

```
packages/mcp-server/
├── src/
│   └── alps_mcp_server/
│       ├── __init__.py
│       ├── server.py       # MCP 서버 구현
│       └── templates/
│           ├── overview.md
│           └── chapters/   # 섹션별 템플릿
│               ├── 01-overview.md
│               ├── 02-mvp-goals.md
│               ├── 03-demo-scenario.md
│               ├── 04-architecture.md
│               ├── 05-design-spec.md
│               ├── 06-requirements.md
│               ├── 07-feature-spec.md
│               ├── 08-mvp-metrics.md
│               └── 09-out-of-scope.md
└── tests/
```

## Technology Stack

- **Protocol**: Model Context Protocol (MCP)
- **Language**: Python 3.13+
- **Package Manager**: uv

## Development Commands

```bash
# 의존성 설치
uv sync

# 서버 실행
uv run alps-mcp-server

# 테스트 실행
uv run pytest
```

## Available Tools

### Template Tools

| Tool | Description |
|------|-------------|
| `get_alps_overview` | ALPS 템플릿 개요 조회 |
| `list_alps_sections` | 모든 섹션 목록 조회 |
| `get_alps_section` | 특정 섹션 조회 (1-9) |
| `get_alps_full_template` | 전체 템플릿 조회 |
| `get_alps_section_guide` | 섹션별 대화 가이드 조회 |

### Document Management Tools

| Tool | Description |
|------|-------------|
| `init_alps_document` | 새 ALPS 문서 생성 |
| `load_alps_document` | 기존 문서 로드 |
| `save_alps_section` | 섹션 내용 저장 |
| `read_alps_section` | 섹션 내용 읽기 |
| `get_alps_document_status` | 문서 상태 조회 |
| `export_alps_markdown` | 마크다운 내보내기 |

## MCP Client Configuration

```json
{
  "mcpServers": {
    "alps-writer": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/alps-writer/packages/mcp-server",
        "run",
        "alps-mcp-server"
      ]
    }
  }
}
```

## Agent-specific Instructions

### Safe to Modify

- `templates/` - 템플릿 내용 수정
- 새로운 도구 추가

### Approach with Caution

- `server.py` - MCP 서버 핵심 로직
- 기존 도구 시그니처 변경
