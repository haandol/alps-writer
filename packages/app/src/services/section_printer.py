from typing import List

from strands.types.content import Message

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

    def _build_system_prompt(self) -> str:
        """
        Builds a system message for ALPS template generation.

        Returns:
            str: The system prompt string including ALPS template and instruction
        """
        system_message_contents: List[str] = [
            self.section_printer_system_prompt,
            f"<alps-template>{self.alps_context}</alps-template>",
            "Please print the section in the requested locale.",
        ]

        return "\n".join(system_message_contents)

    def build_section_printer_messages(
        self, recent_history: List[Message], section: str, locale: str
    ) -> List[Message]:
        """
        Builds a list of messages for section printer.
        Prompt cache should be added to the history before building the messages.

        Args:
            recent_history (List[Message]): Recent conversation history
            section (str): Section to print
            locale (str): Locale to print the section in

        Returns:
            List[Message]: List of messages for section printer
        """
        logger.info("Got recent history", length=len(recent_history))

        user_message: Message = {
            "role": "user",
            "content": [
                {
                    "text": f"<locale>{locale}</locale>\n<section>{section}</section>\nPlease print the section in the requested locale.",
                },
            ],
        }
        # Do not include system message here; provided separately to model.stream
        return [*recent_history, user_message]

    def get_system_prompt(self) -> str:
        return self._build_system_prompt()
