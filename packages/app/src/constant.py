from typing import List

from chainlit.types import CommandDict

COMMANDS: List[CommandDict] = [
    {
        "id": "search",
        "icon": "globe",
        "description": "Enter a search term to search the web for the corresponding content",
    },
]

# LLM
MAX_TOKENS: int = 8192
TEMPERATURE: float = 0.33

# Memory
MAX_RECENT_HISTORY_TURNS: int = 20
