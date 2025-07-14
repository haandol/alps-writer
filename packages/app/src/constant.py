from typing import List
from enum import Enum

from chainlit.types import CommandDict


# LLM
class LLMBackend(Enum):
    AWS = "aws"
    ANTHROPIC = "anthropic"


MAX_TOKENS: int = 1024 * 16
TEMPERATURE: float = 0.33


# Chainlit COMMANDS
COMMANDS: List[CommandDict] = [
    {
        "id": "search",
        "icon": "globe",
        "description": "Enter a search term to search the web for the corresponding content",
    },
    {
        "id": "save",
        "icon": "save",
        "description": "Save the current document in the requested locale",
    },
]

# Sections
SECTIONS: List[str] = [
    "- Section 1. Overview",
    "- Section 2. MVP Goals and Key Metrics",
    "- Section 3. Demo Scenario",
    "- Section 4. High-Level Architecture",
    "- Section 5. Design Specification",
    "- Section 6. Requirements Summary",
    "- Section 7. Feature-Level Specification",
    "- Section 8. MVP Metrics",
    "- Section 9. Out of Scope",
]
