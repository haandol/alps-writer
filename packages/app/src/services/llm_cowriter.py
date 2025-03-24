import os
import asyncio
import logging
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

    def _build_system_message(
        self,
        recent_history: Optional[str] = None,
        relevant_history: Optional[str] = None,
    ) -> SystemMessage:
        """
        Builds a system message for ALPS template generation.

        Args:
            recent_history: Recent conversation history
            relevant_history: Relevant conversation history (optional)

        Returns:
            List of BaseMessage
        """
        system_message_contents: List[str] = [
            self.alps_system_prompt,
            f"<alps-template>{self.alps_context}</alps-template>",
        ]

        if recent_history and len(recent_history.strip()) > 0:
            logger.info(
                f"Using system prompt with recent history: {len(recent_history)}")
            system_message_contents.append(
                f"<recent_conversation>\n{recent_history}\n</recent_conversation>"
            )

        # append relevant history if recent history has 20 lines or more
        if len(recent_history.split('\n')) >= MAX_RECENT_HISTORY_TURNS:
            logger.info(
                f"Using system prompt with relevant history: {len(relevant_history)}")
            system_message_contents.append(
                f"<relevant_conversation>\n{relevant_history}\n</relevant_conversation>"
            )
        else:
            logger.info("No relevant history")

        system_message_contents.append(
            "Please answer in user's language, if you don't know the language, answer in English."
        )

        return SystemMessage(content="\n".join(system_message_contents))

    async def answer_question_stream(
        self, query: str, web_result: str
    ) -> AsyncGenerator[str, None]:
        """Process a question based on web search results in a streaming manner."""
        messages = [
            SystemMessage(content=self.web_qa_system_prompt),
            HumanMessage(
                content=f"<query>{query}</query>\n\n<web_result>{web_result}</web_result>"
            ),
        ]

        try:
            async for chunk in self.llm.astream(messages):
                for content in chunk.content:
                    yield content.get("text", "")
                await asyncio.sleep(0)

        except Exception as e:
            logger.error(f"Error streaming from Bedrock: {e}")
            yield f"Error occurred while streaming from Bedrock: {str(e)}"

    async def cowrite_alps_template_stream(
        self,
        user_message: HumanMessage,
        recent_history: Optional[str] = None,
        relevant_history: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate ALPS template interactively in a streaming manner.

        Args:
            user_message: User message
            recent_history: Recent conversation history
            relevant_history: Relevant conversation history

        Returns:
            Generated text stream
        """
        try:
            system_message = self._build_system_message(
                recent_history,
                relevant_history,
            )
            async for chunk in self.llm.astream([system_message, user_message]):
                for content in chunk.content:
                    yield content.get("text", "")
                await asyncio.sleep(0)
        except Exception as e:
            logger.error(f"Error streaming from Bedrock: {e}")
            yield f"Error occurred while streaming from Bedrock: {str(e)}"
