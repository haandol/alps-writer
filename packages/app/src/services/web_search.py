from typing import Dict, List, Optional

from tavily import TavilyClient
from tavily.errors import (
    MissingAPIKeyError,
    InvalidAPIKeyError,
    UsageLimitExceededError,
)

from src.config import config


class WebSearchService:
    """Service class for using the Tavily search API"""

    def __init__(self):
        """
        Initialize the Tavily API client.
        The TAVILY_API_KEY environment variable is required.
        """
        self.client = TavilyClient(api_key=config.tavily_api_key)

    async def search(self, query: str) -> Optional[List[Dict]]:
        """
        Perform a web search with the given query.

        Args:
            query (str): The query string to search for

        Returns:
            Optional[List[Dict]]: The search results list. Returns None if failed
        """
        try:
            response = self.client.search(
                query,
                max_results=config.tavily_max_results,
            )
            return response.get("results", [])
        except (MissingAPIKeyError, InvalidAPIKeyError) as e:
            raise Exception("The Tavily API key is invalid.") from e
        except UsageLimitExceededError as e:
            raise Exception(
                "The Tavily API usage limit has been exceeded.") from e
        except Exception as e:
            raise Exception(
                f"An error occurred during web search: {str(e)}") from e
