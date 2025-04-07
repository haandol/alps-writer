from typing import List

from chainlit.types import CommandDict

COMMANDS: List[CommandDict] = [
    {
        "id": "search",
        "icon": "globe",
        "description": "Enter a search term to search the web for the corresponding content",
    },
]

# Sections
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

# LLM
MAX_TOKENS: int = 8192
TEMPERATURE: float = 0.33

# Memory
MAX_RECENT_HISTORY_TURNS: int = 60  # 30 pairs
MAX_RELEVANT_HISTORY_TURNS: int = 5  # 5 turns
