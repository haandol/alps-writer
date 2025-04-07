import os
import asyncio
import traceback
from typing import AsyncGenerator, List, Optional

from langchain_aws import ChatBedrockConverse
from langchain.schema import BaseMessage, HumanMessage, SystemMessage

from src.constant import TEMPERATURE, MAX_TOKENS
from src.prompts.alps import SYSTEM_PROMPT as ALPS_SYSTEM_PROMPT
from src.prompts.web_qa import SYSTEM_PROMPT as WEB_QA_SYSTEM_PROMPT
from src.utils.context import load_alps_context
from src.utils.logger import logger


class LLMCowriterService:
    def __init__(self, model_id: str):
        self.llm = ChatBedrockConverse(
            model_id=model_id,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            region_name=os.getenv("AWS_REGION"),
        )
        self.alps_context = load_alps_context()
        self.alps_system_prompt = ALPS_SYSTEM_PROMPT
        self.web_qa_system_prompt = WEB_QA_SYSTEM_PROMPT

    def _build_system_message(self) -> SystemMessage:
        """
        Builds a system message for ALPS template generation.

        Returns:
            SystemMessage: The system message containing ALPS template and language instruction
        """
        system_message_contents: List[str] = [
            self.alps_system_prompt,
            f"<alps-template>{self.alps_context}</alps-template>",
            "Please answer in user's language, if you don't know the language, answer in English."
        ]

        return SystemMessage(
            content=[
                {
                    "type": "text",
                    "text": "\n".join(system_message_contents),
                },
                {
                    "cachePoint": {"type": "default"},
                },
            ],
        )

    def build_alps_messages(
        self,
        message_content: str,
        recent_history: List[BaseMessage] = [],
        text_context: Optional[str] = None,
        image_context: Optional[str] = None,
    ) -> List[BaseMessage]:
        """
        Builds a list of messages with system message and user message containing context and history.

        Args:
            message_content (str): Original user message content
            recent_history (List[BaseMessage]): Recent conversation history
            text_context (Optional[str]): Text context from uploaded files
            image_context (Optional[str]): Image context from uploaded files

        Returns:
            List[BaseMessage]: List of messages ready for LLM processing
        """
        logger.info(f"Got recent history: {len(recent_history)}")

        message_contents = []

        # Add context if available
        if text_context:
            message_contents.append(f"<context>{text_context}</context>")

        # Add the original message
        message_contents.append(message_content)

        # Build the final user message
        if image_context:
            user_message = HumanMessage(content=[
                {
                    "type": "text",
                    "text": "\n\n".join(message_contents)
                },
                image_context,
            ])
        else:
            user_message = HumanMessage(content="\n\n".join(message_contents))

        return [self._build_system_message(), *recent_history, user_message]

    def build_web_search_messages(
        self,
        query: str,
        web_result: str,
    ) -> List[SystemMessage | HumanMessage]:
        """
        Builds a list of messages for web search based Q&A.

        Args:
            query (str): User's search query
            web_result (str): Search results from web search

        Returns:
            List[SystemMessage | HumanMessage]: List of messages ready for LLM processing
        """
        return [
            SystemMessage(content=self.web_qa_system_prompt),
            HumanMessage(
                content=f"<query>{query}</query>\n\n<web_result>{web_result}</web_result>"
            ),
        ]

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
        try:
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
            logger.info(f'Usage metadata: {full_response.usage_metadata}')
        except Exception as e:
            logger.error(traceback.format_exc())
            yield f"Error occurred while streaming from Bedrock: {str(e)}"
