import os
from typing import Optional
from dataclasses import dataclass

import structlog
from dotenv import load_dotenv
load_dotenv()  # noqa: E402

from src.constant import LLMBackend

logger = structlog.get_logger('config')

# Set environment variables
# disable oauth only for the local test
DISABLE_OAUTH = os.getenv("DISABLE_OAUTH", "false").lower() == "true"
logger.info("OAuth configuration", disable_oauth=DISABLE_OAUTH)
HISTORY_TABLE_NAME = os.getenv("HISTORY_TABLE_NAME", "")
logger.info("HISTORY_TABLE_NAME configuration", table_name=HISTORY_TABLE_NAME)
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", None)
logger.info("AWS region configuration", region=AWS_DEFAULT_REGION)

# AWS
AWS_PROFILE = os.getenv("AWS_PROFILE", None)
logger.info("AWS profile configuration", profile=AWS_PROFILE)
AWS_BEDROCK_MODEL_ID = os.getenv("AWS_BEDROCK_MODEL_ID", None)
logger.info("AWS Bedrock model configuration", model_id=AWS_BEDROCK_MODEL_ID)

# Anthropic
ANTHROPIC_MODEL_ID = os.getenv("ANTHROPIC_MODEL_ID", None)
logger.info("Anthropic model configuration", model_id=ANTHROPIC_MODEL_ID)

# default is AWS, only use Anthropic if ANTHROPIC_MODEL_ID is set
MODEL_ID = ANTHROPIC_MODEL_ID or AWS_BEDROCK_MODEL_ID
assert MODEL_ID, "MODEL_ID must be set"
LLM_BACKEND = LLMBackend.ANTHROPIC if ANTHROPIC_MODEL_ID else LLMBackend.AWS
logger.info("LLM backend configuration", backend=LLM_BACKEND)

# Tavily
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", None)
logger.info("Tavily API key configuration", api_key=TAVILY_API_KEY)
TAVILY_MAX_RESULTS = os.getenv("TAVILY_MAX_RESULTS", 5)
logger.info("Tavily max results configuration", max_results=TAVILY_MAX_RESULTS)

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
logger.info("Environment configuration", environment=ENVIRONMENT)


@dataclass
class Config:
    disable_oauth: bool
    history_table_name: Optional[str]
    aws_default_region: Optional[str]
    aws_profile: Optional[str]
    aws_bedrock_model_id: Optional[str]
    anthropic_model_id: Optional[str]
    model_id: str
    llm_backend: LLMBackend
    tavily_api_key: Optional[str]
    tavily_max_results: int
    environment: str


config = Config(
    disable_oauth=DISABLE_OAUTH,
    history_table_name=HISTORY_TABLE_NAME,
    aws_default_region=AWS_DEFAULT_REGION,
    aws_profile=AWS_PROFILE,
    aws_bedrock_model_id=AWS_BEDROCK_MODEL_ID,
    anthropic_model_id=ANTHROPIC_MODEL_ID,
    model_id=MODEL_ID,
    llm_backend=LLM_BACKEND,
    tavily_api_key=TAVILY_API_KEY,
    tavily_max_results=TAVILY_MAX_RESULTS,
    environment=ENVIRONMENT,
)
