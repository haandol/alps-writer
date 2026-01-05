# ALPS Writer Infra Package Guide

## Overview

AWS CDK 기반 인프라 코드로, ALPS Writer 애플리케이션을 AWS에 배포합니다.

## Directory Structure

```
packages/infra/
├── bin/
│   └── infra.ts        # CDK 앱 진입점
├── lib/
│   ├── stacks/         # CDK 스택 정의
│   │   ├── vpc-stack.ts
│   │   ├── auth-stack.ts
│   │   ├── common-app-stack.ts
│   │   └── alps-app-stack.ts
│   └── constructs/     # 재사용 가능한 구성 요소
│       ├── alps-chainlit-app.ts
│       └── reverse-proxy.ts
└── config/             # 환경 설정
    └── dev.toml
```

## Technology Stack

- **IaC**: AWS CDK 2.233.0
- **Language**: TypeScript 5.9+
- **Package Manager**: yarn

## AWS Services

- **VPC**: 네트워크 인프라
- **Cognito**: 사용자 인증
- **ECS Fargate**: 컨테이너 기반 애플리케이션 실행
- **ALB**: 로드 밸런서
- **CloudFront**: CDN

## Development Commands

```bash
# 의존성 설치
yarn install

# CDK 부트스트랩
npx cdk bootstrap

# 스택 배포
npx cdk deploy "*" --require-approval never

# 특정 스택만 배포
npx cdk deploy AlpsAppStack
```

## Configuration

`.toml` 파일로 환경 설정:

```toml
[vpc]
vpcId = "vpc-xxx"  # 기존 VPC 사용 시

[external.web]
tavilyApiKey = "tvly-xxx"
```

## Stacks

### VpcStack

- VPC 생성 또는 기존 VPC 참조
- 서브넷, 라우팅 테이블 구성

### AuthStack

- Cognito User Pool 생성
- MFA 설정
- OAuth 클라이언트 구성

### CommonAppStack

- 공통 리소스 (보안 그룹 등)

### AlpsAppStack

- ECS Fargate 서비스
- ALB 구성
- CloudFront 배포

## Agent-specific Instructions

### Safe to Modify

- `config/` - 환경 설정 파일
- 태그, 이름 등 메타데이터

### Approach with Caution

- `lib/stacks/` - 스택 정의
- `lib/constructs/` - 구성 요소
- IAM 권한 설정
- 네트워크 구성
