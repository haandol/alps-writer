# ALPS Writer (Agentic Lean Prototyping Specification Writer) ⛰️📝

This project is a demo of an LLM-based interactive technical/functional specification writing tool. It is a web application that helps developers, product managers, and planners create MVP technical specifications more efficiently.

![screenshot](/docs/screenshot.png)

## Project Goals

1. Support non-technical planners and business stakeholders to easily organize technical and business requirements when writing service/product planning documents, as if working with a developer for technical validation.
2. Present an optimal document format that can reflect technical requirements suitable for agent-driven development methodologies such as Cursor and Windsurf.

## Key Features

- AI-powered conversational interface (Amazon Bedrock 3.7 Sonnet)
- User authentication via AWS Cognito
- Web search functionality (Tavily API integration)
- Asynchronous collaboration through chat session sharing

## Prerequisites

1. Python 3.13 or higher
2. Node.js 20 or higher
3. Docker
4. AWS CLI configuration or Claude API Key

## Project Structure

```
alps-writer/
├── packages/
│   ├── app/          # Main application code
│   └── infra/        # AWS CDK infrastructure code
└── docs/             # Project documentation
```

## Getting Started

For detailed installation and setup instructions for each package, refer to the README.md in the respective directory:

You can run this project either locally on your machine:

- [Application Installation Guide](packages/app/README.md)

Or deploy it to your personal AWS account:

- [Infrastructure Installation Guide](packages/infra/README.md)

## Next Steps

The following features are planned for production-ready release:

- [x] Apply RAG and chat-history-memory features to reduce token usage
- [x] Enable Prompt Caching for reducing token usage
- [ ] TaskManager feature that reduce blast radius during develop using Agentic IDEs
- [ ] Add Save command for upload completed document to S3 with one click
- [ ] Migrate from Chainlit to custom solution that supports concurrent user sessions per each conversation
- [ ] Build document management system for specification generation and versioning

## License

Apache License 2.0
