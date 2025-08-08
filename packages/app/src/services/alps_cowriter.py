from typing import List, Optional

from strands.types.content import Message

from src.services.llm import LLMService
from src.prompts.cowriter import SYSTEM_PROMPT as ALPS_SYSTEM_PROMPT
from src.prompts.web_qa import SYSTEM_PROMPT as WEB_QA_SYSTEM_PROMPT
from src.constant import LLMBackend
from src.utils.context import load_alps_context
from src.utils.logger import logger


class ALPSCowriterService(LLMService):
    def __init__(self, llm_backend: LLMBackend, model_id: str):
        super().__init__(llm_backend, model_id)

        self.alps_context = load_alps_context()
        self.alps_system_prompt = ALPS_SYSTEM_PROMPT
        self.web_qa_system_prompt = WEB_QA_SYSTEM_PROMPT

    def _build_system_prompt(self) -> str:
        """
        Builds a system message for ALPS template generation.

        Returns:
            str: The system prompt string including ALPS template and instruction
        """
        system_message_contents: List[str] = [
            self.alps_system_prompt,
            f"<alps-template>{self.alps_context}</alps-template>",
            "Please answer in user's language, if you don't know the language, answer in English.",
        ]

        # Strands models accept a separate system prompt string
        return "\n".join(system_message_contents)

    def build_alps_messages(
        self,
        message_content: str,
        recent_history: List[Message] = [],
        text_context: Optional[str] = None,
        image_context: Optional[str] = None,
    ) -> List[Message]:
        """
        Builds a list of messages with system message and user message containing context and history.
        Prompt cache should be added to the history before building the messages.

        Args:
            message_content (str): Original user message content
            recent_history (List[Message]): Recent conversation history
            text_context (Optional[str]): Text context from uploaded files
            image_context (Optional[str]): Image context from uploaded files

        Returns:
            List[Message]: List of messages ready for LLM processing
        """
        logger.info("Got recent history", length=len(recent_history))

        message_contents: List[str] = []

        # Add context if available
        if text_context:
            message_contents.append(f"<context>{text_context}</context>")

        # Add the original message
        message_contents.append(message_content)

        # Build the final user message
        if image_context:
            user_message: Message = {
                "role": "user",
                "content": [
                    {"text": "\n\n".join(message_contents)},
                    image_context,  # already in Bedrock image content format
                ],
            }
        else:
            user_message = {
                "role": "user",
                "content": [
                    {"text": "\n\n".join(message_contents)},
                ],
            }

        # Do not include system message here; strands uses separate system_prompt
        return [*recent_history, user_message]

    def build_web_search_messages(
        self,
        query: str,
        web_result: str,
    ) -> List[Message]:
        """
        Builds a list of messages for web search based Q&A.

        Args:
            query (str): User's search query
            web_result (str): Search results from web search

        Returns:
            List[Message]: List of messages ready for LLM processing
        """
        return [
            {
                "role": "user",
                "content": [
                    {
                        "text": f"<query>{query}</query>\n\n<web_result>{web_result}</web_result>",
                    },
                ],
            }
        ]

    def get_system_prompt_for_web_qa(self) -> str:
        return self.web_qa_system_prompt

    def get_system_prompt_for_alps(self) -> str:
        return self._build_system_prompt()
