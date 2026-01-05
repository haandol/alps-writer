# ALPS Writer App Package Guide

## Overview

Chainlit 기반 AI 대화형 기술 명세서 작성 애플리케이션입니다.

## Directory Structure

```
packages/app/
├── app.py              # 메인 애플리케이션 진입점
├── src/
│   ├── config.py       # 환경 설정
│   ├── constant.py     # 상수 정의
│   ├── handlers/       # 이벤트 핸들러
│   │   ├── file_handler.py
│   │   ├── image_file_handler.py
│   │   ├── save_handler.py
│   │   └── search_handler.py
│   ├── prompts/        # LLM 프롬프트 정의
│   │   ├── cowriter.py
│   │   ├── section_printer.py
│   │   └── web_qa.py
│   ├── services/       # 비즈니스 로직
│   │   ├── alps_cowriter.py
│   │   ├── llm.py
│   │   ├── prompt_cache.py
│   │   ├── section_printer.py
│   │   └── web_search.py
│   └── utils/          # 유틸리티
│       ├── chainlit_patch.py
│       ├── context.py
│       ├── logger.py
│       ├── memory.py
│       ├── session.py
│       └── token_counter.py
├── templates/          # 문서 템플릿
├── specs/              # 스펙 문서
└── env/                # 환경 설정 파일
```

## Technology Stack

- **Framework**: Chainlit 2.6.6
- **Language**: Python 3.13+
- **LLM**: AWS Bedrock (Claude 3.7 Sonnet) / Anthropic API
- **Agent**: Strands Agents
- **Web Search**: Tavily API
- **Package Manager**: uv

## Development Commands

```bash
# 의존성 설치
uv sync

# 개발 서버 실행
uv run -- chainlit run app.py -w -h
```

## Environment Variables

```env
# AWS Bedrock 사용 시
AWS_DEFAULT_REGION="us-west-2"
AWS_PROFILE_NAME="default"
AWS_BEDROCK_MODEL_ID="us.anthropic.claude-3-7-sonnet-20250219-v1:0"

# Anthropic API 사용 시
ANTHROPIC_MODEL_ID="claude-3-7-sonnet-20250219"
ANTHROPIC_API_KEY="your-api-key"

# 웹 검색 (선택)
TAVILY_API_KEY="tvly-xxx"

# 인증 (선택)
DISABLE_OAUTH="true"
OAUTH_COGNITO_CLIENT_ID=""
OAUTH_COGNITO_CLIENT_SECRET=""
OAUTH_COGNITO_DOMAIN=""
```

## Key Components

### Handlers

- `file_handler.py` - 파일 업로드 처리
- `image_file_handler.py` - 이미지 파일 처리
- `save_handler.py` - 문서 저장 처리
- `search_handler.py` - 웹 검색 처리

### Services

- `alps_cowriter.py` - ALPS 문서 공동 작성 로직
- `llm.py` - LLM 클라이언트 초기화
- `prompt_cache.py` - 프롬프트 캐싱
- `section_printer.py` - 섹션 출력 서비스
- `web_search.py` - Tavily 웹 검색

### Prompts

- `cowriter.py` - 메인 코라이터 프롬프트
- `section_printer.py` - 섹션 출력 프롬프트
- `web_qa.py` - 웹 검색 QA 프롬프트

## Agent-specific Instructions

### Safe to Modify

- `src/prompts/` - 프롬프트 수정
- `src/utils/` - 유틸리티 함수
- `templates/` - 문서 템플릿

### Approach with Caution

- `app.py` - 메인 진입점
- `src/config.py` - 환경 설정
- `src/services/llm.py` - LLM 클라이언트
