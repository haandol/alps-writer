from typing import List, Dict, Optional

import chainlit as cl

from src.services.web_search import WebSearchService


class WebSearchHandler:
    """Handler for web search commands"""

    def __init__(self, web_search_service: WebSearchService):
        """
        Args:
            web_search_service (WebSearchService): Web search service instance
        """
        self.web_search_service = web_search_service

    async def handle(self, message: cl.Message) -> Optional[str]:
        """
        Process web search commands.

        Args:
            message (cl.Message): User message
        """
        query = message.content.replace("/web", "").strip()
        if not query:
            await cl.Message(
                content="Please enter a search term. Example: /web What is ChatGPT?"
            ).send()
            return

        try:
            # Display the search step as a Step
            async with cl.Step(name="Web search", type="tool") as step:
                step.input = query

                results = await self.web_search_service.search(query)
                if not results:
                    step.output = "No search results found."
                    return

                content = self._format_results(results)
                step.output = content

            # Send the final result message
            return content

        except Exception as e:
            await cl.Message(
                content=f"An error occurred while searching: {str(e)}"
            ).send()
            return

    def _format_results(self, results: List[Dict]) -> str:
        """Format search results as markdown."""
        formatted = ""
        for i, result in enumerate(results, 1):
            formatted += f"{i}. **[{result['title']}]({result['url']})**\n"
            formatted += f"   {result['content']}\n\n"
        return formatted
