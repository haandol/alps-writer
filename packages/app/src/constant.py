from typing import List

from chainlit.types import CommandDict

COMMANDS: List[CommandDict] = [
    {
        "id": "search",
        "icon": "globe",
        "description": "Enter a search term to search the web for the corresponding content",
    },
]

CHAPTERS: List[str] = [
    "1. Overview",
    "2. MVP Goal & Metrics",
    "3. Requirements Summary",
    "4. High-Level Architecture",
    "5. Design Specification",
    "6. Feature-Level Specification",
    "7. Data Model",
    "8. API Endpoint Specification",
    "9. Deployment & Operation",
    "10. MVP Metrics",
    "11. Out of Scope",
]
