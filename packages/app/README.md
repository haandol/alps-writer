# Interactive ALPS Writer (Agentic Lean Prototyping Spec Writer)

An AI-powered tool that generates technical/functional specification documents through interactive conversations. It helps developers, product managers, and planners create MVP technical specs more efficiently.

## Requirements

1. Python 3.13 or higher
2. Configured AWSCLI
3. Enabled AWS Bedrock for `Anthropic Claude 3.5 Sonnet V2` and `Amazon Titan Embeddings Text V2`

## Installation

1. Clone the repository:

```bash
git clone git@github.com:haandol/alps-writer.git
cd alps-writer
```

> Tip: If you're using VS Code or equivalent IDEs that support Dev Containers, you can utilize this feature.

1. Install UV:

```bash
pip install uv
```

1. Install required packages:

```bash
uv sync
```

1. Set up environment variables:

```bash
cp env/dev.env .env
```

1. Open the `.env` file and edit your AWS profile and region:

```env
AWS_DEFAULT_REGION="us-west-2"
AWS_PROFILE_NAME="default"
```

### **Optional** Enable Authentication on Local Machine

Chainlit supports Cognito authentication, which allows you to maintain chat history and resume conversations even after session termination. To enable this feature, follow these instructions:

1. Read [README.md](../infra/README.md) and provision the infrastructure on AWS

2. Open `.env` and complete the following sections. All values can be found in your AWS Web Console:
```env
DISABLE_OAUTH="false" # set this false
OAUTH_COGNITO_CLIENT_ID="YOUR_COGNITO_CLIENT_ID"
OAUTH_COGNITO_CLIENT_SECRET="YOUR_COGNITO_CLIENT_SECRET"
OAUTH_COGNITO_DOMAIN="YOUR_COGNITO_DOMAIN"
```

### **Optional** TavilyAPI

To enable the search feature:

1. Open the `.env` file and enter your [Tavily](https://tavily.com) API Key:

```env
TAVILY_API_KEY="tvly-1234567890"
```

## Running the Application

1. Run the application with the following command:

```bash
uv run -- chainlit run app.py -w -h
```

## License

Apache License 2.0
