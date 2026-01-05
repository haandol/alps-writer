# ALPS Writer Project Guide

This file acts as a living wiki for the repository.
Use it to quickly understand the project layout, common tasks and key documentation.

## Overview

ALPS Writer (Agentic Lean Prototyping Specification Writer)는 LLM 기반 대화형 기술/기능 명세서 작성 도구입니다.
개발자, PM, 기획자가 MVP 기술 명세서를 효율적으로 작성할 수 있도록 지원합니다.

## Repository Structure

### Core Packages

- **`packages/app`** – Chainlit 기반 메인 애플리케이션
  - AI 기반 대화형 인터페이스 (Amazon Bedrock Claude 3.7 Sonnet)
  - AWS Cognito 사용자 인증
  - Tavily API 웹 검색 기능
  - 채팅 세션 공유를 통한 비동기 협업
  - Technology: Python 3.13+, Chainlit, Strands Agents, uv

- **`packages/infra`** – AWS CDK 인프라 코드
  - VPC, Cognito 인증 서비스
  - ECS Fargate 기반 애플리케이션 배포
  - CloudFront CDN 구성
  - Technology: TypeScript, AWS CDK 2.233.0

- **`packages/mcp-server`** – ALPS 템플릿 도구용 MCP 서버
  - ALPS 템플릿 섹션 조회 도구
  - 문서 관리 도구 (생성, 저장, 내보내기)
  - Claude Desktop, Cursor 등 MCP 호환 클라이언트 지원
  - Technology: Python 3.13+, MCP SDK, uv

### Documentation

- `docs/architecture.drawio.png` – 시스템 아키텍처 다이어그램
- `docs/screenshot.png` – 애플리케이션 스크린샷

## Development Commands

### Application

```bash
cd packages/app
uv sync
uv run -- chainlit run app.py -w -h
```

### Infrastructure

```bash
cd packages/infra
yarn install
npx cdk deploy "*" --require-approval never
```

### MCP Server

```bash
cd packages/mcp-server
uv sync
uv run alps-mcp-server
```

## Technology Stack

### Application

- **Framework**: Chainlit 2.6.6
- **Language**: Python 3.13+
- **LLM**: AWS Bedrock (Claude 3.7 Sonnet) / Anthropic API
- **Agent Framework**: Strands Agents
- **Web Search**: Tavily API
- **Authentication**: AWS Cognito
- **Package Manager**: uv

### Infrastructure

- **IaC**: AWS CDK 2.233.0 with TypeScript
- **Services**: VPC, ECS Fargate, Cognito, CloudFront, ALB
- **Package Manager**: yarn

### MCP Server

- **Protocol**: Model Context Protocol (MCP)
- **Language**: Python 3.13+
- **Package Manager**: uv

## Code Style & Conventions

### Python (app, mcp-server)

- Python 3.13+ 필수
- uv 패키지 매니저 사용
- Ruff 린터/포매터 사용
- structlog 기반 로깅

### TypeScript (infra)

- TypeScript 5.9+
- AWS CDK 베스트 프랙티스 준수
- TOML 기반 환경 설정

## Agent-specific Instructions

### Safe to Modify

- 프롬프트 파일 (`packages/app/src/prompts/`)
- 유틸리티 함수 (`packages/app/src/utils/`)
- MCP 서버 템플릿 (`packages/mcp-server/src/alps_mcp_server/templates/`)
- 문서 및 README 파일

### Approach with Caution

- CDK 스택 정의 (`packages/infra/lib/stacks/`)
- 인증 관련 코드
- 환경 변수 참조
- 메인 애플리케이션 진입점 (`packages/app/app.py`)

### Key Patterns to Follow

- 기존 코드 구조 및 패턴 준수
- 적절한 에러 핸들링 및 로깅 추가
- 보안 베스트 프랙티스 준수
- 환경 변수로 민감 정보 관리

## Security Considerations

- 환경 변수로 민감 설정 관리
- AWS Cognito 기반 인증
- 코드베이스에 시크릿 하드코딩 금지
- 적절한 IAM 권한 설정

## Further Reading

- 패키지별 AGENTS.md 파일 참조
- 각 패키지의 README.md 파일 참조
