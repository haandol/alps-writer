import os
import asyncio
import logging
import traceback
from typing import AsyncGenerator, List, Optional

from langchain_aws import ChatBedrockConverse
from langchain.schema import HumanMessage, SystemMessage

from src.constant import MAX_RECENT_HISTORY_TURNS, TEMPERATURE, MAX_TOKENS
from src.prompts.alps import SYSTEM_PROMPT as ALPS_SYSTEM_PROMPT
from src.prompts.web_qa import SYSTEM_PROMPT as WEB_QA_SYSTEM_PROMPT
from src.utils.context import load_alps_context

logger = logging.getLogger(__name__)


class LLMCowriterService:
    def __init__(self, model_id: str):
        self.llm = ChatBedrockConverse(
            model_id=model_id,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            region_name=os.getenv("AWS_REGION"),
        )
        # TODO: split alps template into sections and load them as context on demand via RAG to reduce token usage
        self.alps_context = load_alps_context()
        # TODO: apply prompt cache on alps_context or use RAG for the context
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

        return SystemMessage(content="\n".join(system_message_contents))

    def build_alps_messages(
        self,
        message_content: str,
        recent_history: Optional[str] = None,
        relevant_history: Optional[str] = None,
        text_context: Optional[str] = None,
        image_context: Optional[str] = None,
    ) -> List[SystemMessage | HumanMessage]:
        """
        Builds a list of messages with system message and user message containing context and history.

        Args:
            message_content: Original user message content
            recent_history: Recent conversation history
            relevant_history: Relevant conversation history from vector search
            text_context: Text context from uploaded files
            image_context: Image context from uploaded files

        Returns:
            List[SystemMessage | HumanMessage]: List of messages ready for LLM processing
        """
        logger.info(
            f"Using recent history: {len(recent_history.strip()) > 0} and relevant history: {len(relevant_history.strip()) > 0}")

        message_contents = []

        # Add conversation history if available
        if recent_history and len(recent_history.strip()) > 0:
            logger.info(
                f"Adding recent history to user message: {len(recent_history)}")
            message_contents.append(
                f"<recent_conversation>\n{recent_history}\n</recent_conversation>"
            )

        if recent_history and len(recent_history.split('\n')) >= MAX_RECENT_HISTORY_TURNS:
            logger.info(
                f"Adding relevant history to user message: {len(relevant_history)}")
            message_contents.append(
                f"<relevant_conversation>\n{relevant_history}\n</relevant_conversation>"
            )

        # Add context if available
        if text_context:
            message_contents.append(f"<context>{text_context}</context>")

        # Add the original message
        message_contents.append(message_content)

        # Create the final user message
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

        return [self._build_system_message(), user_message]

    def build_web_search_messages(
        self,
        query: str,
        web_result: str,
    ) -> List[SystemMessage | HumanMessage]:
        """
        Builds a list of messages for web search based Q&A.

        Args:
            query: User's search query
            web_result: Search results from web search

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
        messages: List[HumanMessage | SystemMessage],
    ) -> AsyncGenerator[str, None]:
        """
        Streams LLM response for the given messages.

        Args:
            messages: List of messages including system message and user message

        Returns:
            AsyncGenerator[str, None]: Generated text stream
        """
        try:
            async for chunk in self.llm.astream(messages):
                for content in chunk.content:
                    yield content.get("text", "")
                await asyncio.sleep(0)
        except Exception as e:
            logger.error(traceback.format_exc())
            yield f"Error occurred while streaming from Bedrock: {str(e)}"
