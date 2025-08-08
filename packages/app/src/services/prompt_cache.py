from typing import List
from copy import deepcopy

from strands.types.content import Message

from src.utils.token_counter import count_tokens
from src.utils.logger import logger
from src.constant import LLMBackend


class PromptCacheService:
    """
    Service to manage prompt caching for Claude 3.7.

    This service handles:
    - Creating cache points based on token thresholds
    - Storing cache points in user session
    - Recovering cache points for message building
    """

    MAX_CACHE_POINTS = 3  # 1 has been used for the system message
    MIN_TOKENS_FOR_CACHE = 2000

    def __init__(self, llm_backend: LLMBackend):
        self.llm_backend = llm_backend

    def should_create_cache_point(
        self, cache_point_indices: List[int], messages: List[Message]
    ) -> bool:
        """
        Determine if a cache point should be created based on the token count of the messages from the last cache point to the end of the message history.

        Args:
            cache_point_indices (List[int]): List of cache point indices
            messages (List[Message]): List of messages in the current history

        Returns:
            bool: True if a cache point should be created
        """
        last_cache_point_index = cache_point_indices[-1] if cache_point_indices else 0

        # Calculate the total token count of messages from the last cache point to the end of the message history
        total_tokens = 0
        for i in range(last_cache_point_index, len(messages)):
            message = messages[i]
            content = ""

            # Extract the content of the message (only text is processed)
            for item in message.get("content", []):
                if isinstance(item, dict) and "text" in item:
                    content += item.get("text", "")

            # Calculate the token count and sum it up
            message_tokens = count_tokens(content)
            total_tokens += message_tokens
            logger.debug("Message token count", index=i, token_count=message_tokens)

        logger.info(
            "Total tokens since last cache point",
            total_tokens=total_tokens,
            last_cache_point_index=last_cache_point_index,
        )

        if total_tokens < self.MIN_TOKENS_FOR_CACHE:
            logger.info(
                "No cache point created",
                total_tokens=total_tokens,
                min_tokens=self.MIN_TOKENS_FOR_CACHE,
            )
            return False

        logger.info(
            "Cache point should be created",
            total_tokens=total_tokens,
            min_tokens=self.MIN_TOKENS_FOR_CACHE,
        )
        return True

    def create_cache_point(
        self, history_index: int, cache_point_indices: List[int]
    ) -> List[int]:
        """
        Create a cache point at the specified history index.

        Args:
            history_index: Index in the message history
            cache_point_indices: List of cache point indices

        Returns:
            List[int]: Updated list of cache point indices
        """
        logger.info(
            "Created cache point",
            history_index=history_index,
            total=len(cache_point_indices),
        )

        return [*cache_point_indices, history_index][-self.MAX_CACHE_POINTS :]

    def add_cache_points_to_messages(
        self, cache_point_indices: List[int], messages: List[Message]
    ) -> List[Message]:
        """
        Add cache point markers to the messages.

        Args:
            messages: List of message dictionaries

        Returns:
            List[Message]: Messages with cache points added
        """
        if not cache_point_indices:
            return messages

        new_messages = deepcopy(messages)
        # Add cache point markers to messages at stored indices
        for i, message in enumerate(new_messages):
            if i in cache_point_indices:
                if "content" not in message or not isinstance(message["content"], list):
                    message["content"] = []
                message["content"].append({"cachePoint": {"type": "default"}})
        return new_messages
