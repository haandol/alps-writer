import os
import asyncio
from typing import List, AsyncGenerator

from langchain_aws import ChatBedrockConverse
from langchain.schema import BaseMessage

from src.constant import MAX_TOKENS, TEMPERATURE
from src.utils.logger import logger


class LLMService:
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.llm = ChatBedrockConverse(
            model_id=self.model_id,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            region_name=os.getenv("AWS_REGION"),
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
                    yield content.get("text", "")
            await asyncio.sleep(0)
        logger.info("Usage metadata",
                    usage_metadata=full_response.usage_metadata)