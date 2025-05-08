from typing import List
from enum import Enum

from chainlit.types import CommandDict


# LLM
class LLMBackend(Enum):
    AWS = "aws"
    ANTHROPIC = "anthropic"


MAX_TOKENS: int = 8192
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

# ALPS Sections
SECTIONS: List[str] = [
    "- Section 1. Overview",
    "- Section 2. MVP Goals and Key Metrics",
    "- Section 3. Requirements Summary",
    "- Section 4. High-Level Architecture",
    "- Section 5. Design Specification",
    "- Section 6. Feature-Level Specification",
    "- Section 7. Data Model/Schema",
    "- Section 8. API Endpoint Specification",
    "- Section 9. Deployment & Operation",
    "- Section 10. MVP Metrics",
    "- Section 11. Out of Scope",
]
