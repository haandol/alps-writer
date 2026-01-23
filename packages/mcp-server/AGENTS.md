# ALPS Writer MCP Server Package Guide

## Overview

ALPS 템플릿 도구를 제공하는 MCP (Model Context Protocol) 서버입니다.
Claude Desktop, Cursor 등 MCP 호환 클라이언트에서 사용할 수 있습니다.

## Directory Structure

```
packages/mcp-server/
├── src/alps_mcp_server/
│   ├── server.py              # MCP 서버 진입점 + 도구 등록
│   ├── di/
│   │   └── container.py       # 의존성 주입 컨테이너
│   ├── tools/
│   │   ├── templates/         # 템플릿 도구
│   │   │   ├── controller.py  # MCP 인터페이스
│   │   │   └── service.py     # 비즈니스 로직
│   │   └── documents/         # 문서 관리 도구
│   │       ├── controller.py
│   │       └── service.py
│   ├── interfaces/
│   │   └── constants.py       # 상수 정의
│   ├── guides/                # 섹션별 가이드 (01.md ~ 09.md)
│   └── templates/
│       ├── overview.md
│       └── chapters/
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

## Architecture

Controller-Service 패턴을 사용합니다:

- **Controller**: MCP 도구 인터페이스 (docstring 포함)
- **Service**: 비즈니스 로직
- **DIContainer**: 의존성 주입을 통한 느슨한 결합

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

- `guides/` - 섹션 가이드 내용 수정
- `templates/` - 템플릿 내용 수정
- 새로운 도구 추가 (tools/ 하위에 새 모듈 생성)

### Approach with Caution

- `server.py` - 도구 등록 로직
- `di/container.py` - 의존성 주입 설정
- 기존 도구 시그니처 변경
