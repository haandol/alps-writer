import os
import asyncio
from typing import List, AsyncGenerator

from langchain.schema import BaseMessage, SystemMessage, HumanMessage
from langchain_aws import ChatBedrockConverse

from src.constant import TEMPERATURE, MAX_TOKENS
from src.prompts.section_printer import SYSTEM_PROMPT as SECTION_PRINTER_SYSTEM_PROMPT
from src.utils.context import load_alps_context
from src.utils.logger import logger


class SectionPrinterService:
    def __init__(self, model_id: str):
        self.llm = ChatBedrockConverse(
            model_id=model_id,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            region_name=os.getenv("AWS_REGION"),
        )
        self.alps_context = load_alps_context()
        self.section_printer_system_prompt = SECTION_PRINTER_SYSTEM_PROMPT

    def _build_system_message(self) -> SystemMessage:
        """
        Builds a system message for ALPS template generation.

        Returns:
            SystemMessage: The system message containing ALPS template and language instruction
        """
        system_message_contents: List[str] = [
            self.section_printer_system_prompt,
            f"<alps-template>{self.alps_context}</alps-template>",
            "Please print the section in the requested locale.",
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

    def build_section_printer_messages(self, messages: List[BaseMessage], section: str, locale: str) -> List[BaseMessage]:
        """
        Builds a list of messages for section printer.
        Prompt cache should be added to the history before building the messages.

        Args:
            messages (List[BaseMessage]): List of messages including system message and user message
            section (str): Section to print
            locale (str): Locale to print the section in

        Returns:
            List[BaseMessage]: List of messages for section printer
        """
        system_message = self._build_system_message()
        user_message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": f"<locale>{locale}</locale>\n<section>{section}</section>\nPlease print the section in the requested locale.",
                },
            ],
        )
        return [system_message, *messages, user_message]

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