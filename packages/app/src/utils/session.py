from typing import List, cast

from chainlit.user_session import UserSession

from src.utils.memory import RecentMemoryManager
from src.services.prompt_cache import PromptCacheService
from src.utils.logger import logger


def load_cache_point_indices(user_session: UserSession) -> List[int]:
    """Load the cache point indices from the user session.

    Args:
        user_session (UserSession): User session

    Returns:
        List[int]: Cache point indices
    """
    return user_session.get("cache_point_indices", [])


def save_cache_point_indices(user_session: UserSession, cache_point_indices: List[int]) -> None:
    """Save the cache point indices to the user session.

    Args:
        user_session (UserSession): User session
        cache_point_indices (List[int]): Cache point indices

    Returns:
        None
    """
    user_session.set("cache_point_indices", cache_point_indices or [])


def create_latest_cache_point(user_session: UserSession, prompt_cache_service: PromptCacheService) -> int:
    """Create a cache point at the end of the message history.

    Args:
        user_session (UserSession): User session
        prompt_cache_service (PromptCacheService): Prompt cache service

    Returns:
        int: Cache point index, -1 if no cache point should be created
    """
    cache_point_index = -1

    # Determine if a cache point should be created based on the entire message history
    recent_memory = cast(
        RecentMemoryManager, user_session.get("recent_memory"),
    )
    cache_point_indices = load_cache_point_indices(user_session)
    recent_history = recent_memory.get_conversation_history()
    if not recent_history:
        logger.debug("No recent history found, skipping cache point creation")
        return

    if prompt_cache_service.should_create_cache_point(cache_point_indices, recent_history):
        # Create cache point at the end of the message history
        new_cache_point_indices = prompt_cache_service.create_cache_point(
            history_index=len(recent_history) - 1,
            cache_point_indices=cache_point_indices,
        )
        save_cache_point_indices(user_session, new_cache_point_indices)
        cache_point_index = new_cache_point_indices[-1]
        logger.info("Created cache point at index",
                    cache_point_index=cache_point_index)

    return cache_point_index
