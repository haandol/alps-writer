from typing import List

from langchain.schema import BaseMessage, SystemMessage, HumanMessage

from src.services.llm import LLMService
from src.prompts.section_printer import SYSTEM_PROMPT
from src.constant import LLMBackend
from src.utils.context import load_alps_context
from src.utils.logger import logger


class SectionPrinterService(LLMService):
    def __init__(self, llm_backend: LLMBackend, model_id: str):
        super().__init__(llm_backend, model_id)

        self.alps_context = load_alps_context()
        self.section_printer_system_prompt = SYSTEM_PROMPT

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

        if self.llm_backend == LLMBackend.AWS:
            return SystemMessage(
                content=[
                    {
                        "type": "text",
                        "text": "\n".join(system_message_contents),
                    },
                    {
                        "cachePoint": {"type": "default"}
                    }
                ],
            )
        else:
            return SystemMessage(
                content=[
                    {
                        "type": "text",
                        "text": "\n".join(system_message_contents),
                        "cache_control": {"type": "ephemeral"}
                    }
                ]
            )

    def build_section_printer_messages(self, recent_history: List[BaseMessage], section: str, locale: str) -> List[BaseMessage]:
        """
        Builds a list of messages for section printer.
        Prompt cache should be added to the history before building the messages.

        Args:
            recent_history (List[BaseMessage]): Recent conversation history
            section (str): Section to print
            locale (str): Locale to print the section in

        Returns:
            List[BaseMessage]: List of messages for section printer
        """
        logger.info("Got recent history",
                    length=len(recent_history))

        system_message = self._build_system_message()
        user_message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": f"<locale>{locale}</locale>\n<section>{section}</section>\nPlease print the section in the requested locale.",
                },
            ],
        )
        return [system_message, *recent_history, user_message]
