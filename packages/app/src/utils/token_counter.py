import logging
import traceback

import tiktoken

logger = logging.getLogger(__name__)

# Claude models use the cl100k_base encoding
ENCODING_NAME = "cl100k_base"


def count_tokens(text: str) -> int:
    """
    Count the number of tokens in a text string using tiktoken.

    Args:
        text: The text to count tokens for

    Returns:
        int: The number of tokens in the text
    """
    try:
        # Get the encoding for Claude models
        encoding = tiktoken.get_encoding(ENCODING_NAME)

        # Count tokens
        tokens = encoding.encode(text)
        return len(tokens)
    except Exception:
        logger.error(traceback.format_exc())
        # Fallback to approximate count if encoding fails
        return len(text) // 4  # Rough approximation
