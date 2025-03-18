import os
import asyncio
import logging
from typing import AsyncGenerator, List

from langchain_aws import ChatBedrockConverse
from langchain.schema import HumanMessage, AIMessage, SystemMessage, BaseMessage

from src.prompts.alps import SYSTEM_PROMPT as ALPS_SYSTEM_PROMPT
from src.prompts.web_qa import SYSTEM_PROMPT as WEB_QA_SYSTEM_PROMPT
from src.utils.context import load_alps_context

logger = logging.getLogger(__name__)


class LLMCowriterService:
    def __init__(self, model_id: str = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"):
        self.llm = ChatBedrockConverse(
            model_id=model_id,
            temperature=0.33,
            max_tokens=8192,
            region_name=os.getenv("AWS_REGION"),
        )
        self.alps_context = load_alps_context()
        self.alps_system_prompt = f"{ALPS_SYSTEM_PROMPT}\n\n<template>{self.alps_context}</template>\n\nPlease answer in user's language, if you don't know the language, answer in English."
        self.web_qa_system_prompt = WEB_QA_SYSTEM_PROMPT

    def _create_messages(self, message_history: List[dict]) -> List[BaseMessage]:
        """Create a list of LLM messages from the message history."""
        messages = [SystemMessage(content=self.alps_system_prompt)]

        if message_history:
            # 빈 content를 가진 메시지 필터링
            filtered_history = [
                msg for msg in message_history if msg.get("content")]

            for msg in filtered_history:
                content = msg["content"]
                # Process messages containing images
                if "image" in msg:
                    image_context = msg["image"]
                    image_content = {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image_context["mime"],
                            "data": image_context["base64"],
                        },
                    }
                    if msg["role"] == "user":
                        messages.append(
                            HumanMessage(
                                content=[
                                    {"type": "text", "text": content},
                                    image_content,
                                ]
                            )
                        )
                    else:
                        messages.append(
                            AIMessage(
                                content=[
                                    {"type": "text", "text": content},
                                    image_content,
                                ]
                            )
                        )
                else:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=content))
                    else:
                        messages.append(AIMessage(content=content))

        return messages

    def _create_answer_question_messages(
        self, query: str, web_result: str
    ) -> List[BaseMessage]:
        """Create messages for answering a question."""
        messages = [SystemMessage(content=self.web_qa_system_prompt)]
        messages.append(
            HumanMessage(
                content=f"<query>{query}</query>\n\n<web_result>{
                    web_result
                }</web_result>"
            )
        )
        return messages

    async def answer_question_stream(
        self, query: str, web_result: str
    ) -> AsyncGenerator[str, None]:
        """Process a question based on web search results in a streaming manner."""
        try:
            messages = self._create_answer_question_messages(query, web_result)

            async for chunk in self.llm.astream(messages):
                for content in chunk.content:
                    yield content.get("text", "")
                await asyncio.sleep(0)

        except Exception as e:
            logger.error(f"Error streaming from Bedrock: {e}")
            yield f"죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다: {str(e)}"

    async def cowrite_alps_template_stream(
        self, message_history: List[dict]
    ) -> AsyncGenerator[str, None]:
        """Generate ALPS template interactively in a streaming manner."""
        try:
            messages = self._create_messages(message_history)
            async for chunk in self.llm.astream(messages):
                for content in chunk.content:
                    yield content.get("text", "")
                await asyncio.sleep(0)
        except Exception as e:
            logger.error(f"Error streaming from Bedrock: {e}")
            yield f"죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다: {str(e)}"
