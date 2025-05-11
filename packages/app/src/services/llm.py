import os
import asyncio
from typing import List, AsyncGenerator

from langchain_aws import ChatBedrockConverse
from langchain_anthropic import ChatAnthropic
from langchain.schema import BaseMessage

from src.constant import MAX_TOKENS, TEMPERATURE, LLMBackend
from src.utils.logger import logger


class LLMService:
    def __init__(self, llm_backend: LLMBackend, model_id: str):
        self.llm_backend = llm_backend
        self.model_id = model_id

        if self.llm_backend == LLMBackend.AWS:
            AWS_PROFILE = os.getenv("AWS_PROFILE", None)
            logger.info("AWS profile configuration", profile_name=AWS_PROFILE)
            self.llm = ChatBedrockConverse(
                model=self.model_id,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                credentials_profile_name=AWS_PROFILE,
            )
        elif self.llm_backend == LLMBackend.ANTHROPIC:
            self.llm = ChatAnthropic(
                model=self.model_id,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )

    async def stream_llm_response(
        self,
        messages: List[BaseMessage],
    ) -> AsyncGenerator[str, None]:
        """
        Streams LLM response for the given messages.

        Args:
            messages (List[BaseMessage]): List of messages including system message and user message

        Returns:
            AsyncGenerator[str, None]: Generated text stream
        """
        full_response = None
        first_chunk = True
        async for chunk in self.llm.astream(messages):
            if first_chunk:
                full_response = chunk
                first_chunk = False
            else:
                full_response += chunk
                for content in chunk.content:
                    if isinstance(content, dict):
                        yield content.get("text", "")
                    else:
                        yield content
            await asyncio.sleep(0)
        logger.info("Usage metadata", usage_metadata=full_response.usage_metadata)
