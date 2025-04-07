import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any

import faiss
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_aws import BedrockEmbeddings
from langchain.memory import VectorStoreRetrieverMemory, ConversationBufferWindowMemory
from langchain.schema import BaseMessage
from src.constant import MAX_RECENT_HISTORY_TURNS, MAX_RELEVANT_HISTORY_TURNS

logger = logging.getLogger(__name__)


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


class VectorMemoryManager(MemoryManager):
    """Memory management class using VectorStoreRetrieverMemory."""

    def __init__(self, k: int = MAX_RELEVANT_HISTORY_TURNS):
        """
        Initialize memory manager.

        Args:
            k (int): Maximum number of items to search
        """
        self.embeddings = BedrockEmbeddings(
            model_id="amazon.titan-embed-text-v2:0",
            region_name=os.getenv("AWS_REGION")
        )
        index = faiss.IndexFlatL2(1024)
        self.vector_store = FAISS(
            embedding_function=self.embeddings.embed_query,
            index=index,
            docstore=InMemoryDocstore({}),
            index_to_docstore_id={}
        )
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": k})
        self.memory = VectorStoreRetrieverMemory(
            retriever=self.retriever,
        )
        self.k = k

    def add_user_message(self, message_content: str) -> None:
        self.memory.save_context(
            {"input": message_content},
            {"output": ""}
        )

    def add_ai_message(self, user_message: str, ai_message: str) -> None:
        self.memory.save_context(
            {"input": user_message},
            {"output": ai_message}
        )

    def get_relevant_history(self, query: str, recent_history: List[BaseMessage] = None) -> str:
        """
        Search for relevant conversation history for the given query.

        Args:
            query (str): Search query
            recent_history (List[BaseMessage], optional): Recent conversation history to exclude from results

        Returns:
            str: Relevant conversation history
        """
        relevant_history = self.memory.load_memory_variables({"output": query})[
            "history"]

        # If recent_history is provided, remove duplicates
        if recent_history:
            # Convert recent_history messages to a set of tuples for easy comparison
            recent_messages = set()
            for msg in recent_history:
                if hasattr(msg, 'content'):
                    if isinstance(msg.content, str):
                        recent_messages.add(msg.content)
                    elif isinstance(msg.content, list):
                        # Handle multi-modal content
                        for content in msg.content:
                            if isinstance(content, dict) and content.get('type') == 'text':
                                recent_messages.add(content.get('text', ''))

            # Filter out messages that are in recent_history
            filtered_history = []
            for line in relevant_history.split('\n'):
                line = line.strip()
                if line and line not in recent_messages:
                    filtered_history.append(line)

            relevant_history = '\n'.join(filtered_history)

        return relevant_history


class RecentMemoryManager(MemoryManager):
    """Memory management class using ConversationBufferWindowMemory."""

    def __init__(self, k: int = MAX_RECENT_HISTORY_TURNS // 2):
        """
        Initialize recent memory manager.

        Args:
            k (int): Maximum number of message pairs to store
        """
        self.memory = ConversationBufferWindowMemory(k=k, return_messages=True)
        self.k = k

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

        # save only recent k message pairs
        recent_pairs = pairs[-self.k:] if len(pairs) > self.k else pairs

        # initialize memory and add recent message pairs
        for user_msg, ai_msg in recent_pairs:
            self.memory.save_context(
                {"input": user_msg},
                {"output": ai_msg}
            )
