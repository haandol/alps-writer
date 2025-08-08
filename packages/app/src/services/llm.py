import asyncio
from typing import List, AsyncGenerator, Optional

import boto3
from strands.models.bedrock import BedrockModel
from strands.models.anthropic import AnthropicModel
from strands.types.content import Message

from src.config import config
from src.constant import MAX_TOKENS, TEMPERATURE, LLMBackend
from src.utils.logger import logger


class LLMService:
    def __init__(self, llm_backend: LLMBackend, model_id: str):
        self.llm_backend = llm_backend
        self.model_id = model_id
        self.model: Optional[BedrockModel | AnthropicModel] = None

        if self.llm_backend == LLMBackend.AWS:
            AWS_PROFILE = config.aws_profile
            logger.info("AWS profile configuration", profile_name=AWS_PROFILE)
            # Configure Bedrock model
            session = boto3.Session(profile_name=AWS_PROFILE)
            self.model = BedrockModel(
                boto_session=session,
                model_id=self.model_id,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                cache_prompt="default",
                cache_tools="default",
            )
        elif self.llm_backend == LLMBackend.ANTHROPIC:
            # Configure Anthropic model
            self.model = AnthropicModel(
                model_id=self.model_id,
                params={"temperature": TEMPERATURE},
                max_tokens=MAX_TOKENS,
            )
        else:
            raise ValueError(f"Unsupported LLM backend: {self.llm_backend}")

    async def stream_llm_response(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream model responses using Strands Agents model providers.

        Args:
            messages: List of strands Message dicts
            system_prompt: Optional system prompt string

        Yields:
            Text chunks as they stream from the provider
        """
        usage = None
        async for event in self.model.stream(
            messages=messages,
            system_prompt=system_prompt,
        ):
            # Text deltas
            delta = event.get("contentBlockDelta") if isinstance(event, dict) else None
            if delta:
                d = delta.get("delta", {})
                text = d.get("text") if isinstance(d, dict) else None
                if text:
                    yield text
            # Usage/metadata capture
            metadata = event.get("metadata") if isinstance(event, dict) else None
            if metadata:
                usage = metadata.get("usage", usage)
            await asyncio.sleep(0)
        if usage:
            logger.info("Usage metadata", usage=usage)
