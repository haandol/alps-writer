from abc import ABC, abstractmethod
from typing import Dict, List, Any

from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage


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

                if user_message.get("role") == "user" and ai_message.get("role") == "assistant":
                    self.add_ai_message(
                        user_message.get("content", ""),
                        ai_message.get("content", "")
                    )


class RecentMemoryManager(MemoryManager):
    """Memory management class using ConversationBufferMemory."""

    def __init__(self):
        """
        Initialize recent memory manager.

        Args:
            k (int): Maximum number of message pairs to store
        """
        self.memory = ConversationBufferMemory(return_messages=True)

    def add_user_message(self, message_content: str) -> None:
        # ConversationBufferWindowMemory is stored as a pair, so nothing is done here
        pass

    def add_ai_message(self, user_message: str, ai_message: str) -> None:
        self.memory.save_context(
            {"input": user_message},
            {"output": ai_message}
        )

    def get_conversation_history(self) -> List[BaseMessage]:
        """
        Return the stored conversation history as a list of messages.

        Returns:
            List[BaseMessage]: Conversation history list
        """
        return self.memory.load_memory_variables({})["history"]

    def add_message_history(self, message_history: List[Dict[str, Any]]) -> None:
        """
        Add only recent k message pairs from message history to memory.

        Args:
            message_history (List[Dict[str, Any]]): List of message history
        """
        # form message pairs to add to memory
        pairs = []
        for i in range(0, len(message_history), 2):
            if i + 1 < len(message_history):
                user_message = message_history[i]
                ai_message = message_history[i + 1]

                if user_message.get("role") == "user" and ai_message.get("role") == "assistant":
                    pair = (user_message.get("content", ""),
                            ai_message.get("content", ""))
                    pairs.append(pair)

        # initialize memory and add recent message pairs
        for user_msg, ai_msg in pairs:
            self.memory.save_context(
                {"input": user_msg},
                {"output": ai_msg}
            )
