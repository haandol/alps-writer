# Interactive ALPS Writer (Agentic Lean Prototyping Spec Writer)

An AI-powered tool that generates technical/functional specification documents through interactive conversations. It helps developers, product managers, and planners create MVP technical specs more efficiently.

## Requirements

1. Python 3.13 or higher

### Choose ONE of the following LLM providers:

#### For AWS Bedrock Users

1. Configured AWSCLI
2. Enabled AWS Bedrock for `Anthropic Claude 3.7 Sonnet V1`

#### For Anthropic Direct API Users

1. Anthropic API Key for `Claude 3.7 Sonnet`

## Installation

1. Clone the repository:

```bash
git clone git@github.com:haandol/alps-writer.git
cd alps-writer
```

> Tip: If you're using VS Code or equivalent IDEs that support Dev Containers, you can utilize this feature.

2. Install UV:

```bash
pip install uv
```

3. Install required packages:

```bash
uv sync
```

4. Set up environment variables:

```bash
cp env/local.env .env
```

5. Configure your LLM provider in the `.env` file:

#### For AWS Bedrock users:
```env
AWS_DEFAULT_REGION="us-west-2"
AWS_PROFILE_NAME="default"
AWS_BEDROCK_MODEL_ID="us.anthropic.claude-3-7-sonnet-20250219-v1:0"

# Comment out or remove these lines
# ANTHROPIC_MODEL_ID=""
# ANTHROPIC_API_KEY=""
```

#### For Anthropic Direct API users:
```env
# Comment out or remove these lines
# AWS_DEFAULT_REGION=""
# AWS_PROFILE_NAME=""
# AWS_BEDROCK_MODEL_ID=""

ANTHROPIC_MODEL_ID="claude-3-7-sonnet-20250219"
ANTHROPIC_API_KEY="your-anthropic-api-key"
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
