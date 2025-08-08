from abc import ABC, abstractmethod
from typing import Dict, List, Any

from strands.types.content import Message


class MemoryManager(ABC):
    """Abstract base class for memory management."""

    @abstractmethod
    def add_user_message(self, message_content: str) -> None:
        """
        Add user message to memory.

        Args:
            message_content (str): User message content
        """
        pass

    @abstractmethod
    def add_ai_message(self, user_message: str, ai_message: str) -> None:
        """
        Add AI response to memory.

        Args:
            user_message (str): User message content
            ai_message (str): AI response content
        """
        pass

    def add_message_history(self, message_history: List[Dict[str, Any]]) -> None:
        """
        Add message history to memory.

        Args:
            message_history (List[Dict[str, Any]]): Message history list
        """
        for i in range(0, len(message_history), 2):
            if i + 1 < len(message_history):
                user_message = message_history[i]
                ai_message = message_history[i + 1]

                if (
                    user_message.get("role") == "user"
                    and ai_message.get("role") == "assistant"
                ):
                    self.add_ai_message(
                        user_message.get("content", ""), ai_message.get("content", "")
                    )


class RecentMemoryManager(MemoryManager):
    """Simple in-memory recent history as strands Message list."""

    def __init__(self):
        self._history: List[Message] = []

    def add_user_message(self, message_content: str) -> None:
        self._history.append(
            {
                "role": "user",
                "content": [{"text": message_content}],
            }
        )

    def add_ai_message(self, user_message: str, ai_message: str) -> None:
        # Append both for parity with previous behavior
        self._history.append(
            {
                "role": "user",
                "content": [{"text": user_message}],
            }
        )
        self._history.append(
            {
                "role": "assistant",
                "content": [{"text": ai_message}],
            }
        )

    def get_conversation_history(self) -> List[Message]:
        """
        Return the stored conversation history as a list of messages.

        Returns:
            List[Message]: Conversation history list
        """
        return list(self._history)

    def add_message_history(self, message_history: List[Dict[str, Any]]) -> None:
        """Add thread history into internal message list."""
        for item in message_history:
            role = item.get("role")
            content = item.get("content", "")
            if role in ("user", "assistant") and isinstance(content, str):
                self._history.append(
                    {
                        "role": role,
                        "content": [{"text": content}],
                    }
                )
