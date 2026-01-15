"""Web search utilities using Serper API."""

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class WebSearchTool:
    """
    Web search tool using Serper.dev API.

    Serper provides Google Search API access with:
    - Organic search results
    - Knowledge graph
    - Related searches
    - Answer boxes
    """

    def __init__(self, api_key: str) -> None:
        """
        Initialize the web search tool.

        Args:
            api_key: Serper API key
        """
        self.api_key = api_key
        self.base_url = "https://google.serper.dev/search"

    def search(
        self,
        query: str,
        num_results: int = 10,
        include_answer_box: bool = True,
        include_knowledge_graph: bool = True,
    ) -> dict[str, Any]:
        """
        Perform a web search using Serper API.

        Args:
            query: Search query
            num_results: Number of results to return (default: 10)
            include_answer_box: Include answer box if available
            include_knowledge_graph: Include knowledge graph if available

        Returns:
            Search results dictionary with organic results, answer box, knowledge graph

        Raises:
            Exception: If API request fails
        """
        if not self.api_key:
            logger.warning("Serper API key not configured, returning empty results")
            return {
                "organic": [],
                "answerBox": None,
                "knowledgeGraph": None,
                "error": "API key not configured",
            }

        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "q": query,
            "num": num_results,
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            # Extract relevant information
            results = {
                "organic": data.get("organic", []),
                "answerBox": data.get("answerBox") if include_answer_box else None,
                "knowledgeGraph": data.get("knowledgeGraph") if include_knowledge_graph else None,
                "relatedSearches": data.get("relatedSearches", []),
            }

            logger.info(f"Web search completed: {query} ({len(results['organic'])} results)")
            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Web search failed: {e}")
            raise Exception(f"Web search failed: {e}")

    def search_and_format(
        self,
        query: str,
        num_results: int = 5,
        max_snippet_length: int = 200,
    ) -> str:
        """
        Perform search and return formatted text results for LLM consumption.

        Args:
            query: Search query
            num_results: Number of results to return
            max_snippet_length: Maximum length of each snippet

        Returns:
            Formatted search results as string
        """
        results = self.search(query, num_results=num_results)

        if results.get("error"):
            return f"Search unavailable: {results['error']}"

        formatted_parts = []

        # Add answer box if available
        if results.get("answerBox"):
            answer = results["answerBox"]
            if answer.get("answer"):
                formatted_parts.append(f"**Answer:** {answer['answer']}\n")
            elif answer.get("snippet"):
                formatted_parts.append(f"**Answer:** {answer['snippet']}\n")

        # Add knowledge graph if available
        if results.get("knowledgeGraph"):
            kg = results["knowledgeGraph"]
            if kg.get("title"):
                formatted_parts.append(f"**{kg['title']}**")
                if kg.get("description"):
                    formatted_parts.append(f"{kg['description']}\n")

        # Add organic results
        formatted_parts.append("**Search Results:**\n")
        for i, result in enumerate(results.get("organic", []), 1):
            title = result.get("title", "No title")
            link = result.get("link", "")
            snippet = result.get("snippet", "")

            # Truncate snippet if needed
            if len(snippet) > max_snippet_length:
                snippet = snippet[:max_snippet_length] + "..."

            formatted_parts.append(f"{i}. **{title}**")
            formatted_parts.append(f"   {snippet}")
            formatted_parts.append(f"   Source: {link}\n")

        # Add related searches
        related = results.get("relatedSearches", [])
        if related:
            formatted_parts.append("\n**Related Searches:**")
            for search in related[:5]:
                formatted_parts.append(f"- {search.get('query', '')}")

        return "\n".join(formatted_parts)

    def search_for_competitors(self, industry: str, product_type: str) -> str:
        """
        Search for competitors in a specific industry/product category.

        Args:
            industry: Industry or market segment
            product_type: Type of product or service

        Returns:
            Formatted competitor information
        """
        query = f"{product_type} {industry} competitors companies startups"
        return self.search_and_format(query, num_results=10)

    def search_for_market_size(self, market: str) -> str:
        """
        Search for market size information.

        Args:
            market: Market or industry to research

        Returns:
            Formatted market size information
        """
        query = f"{market} market size TAM SAM statistics"
        return self.search_and_format(query, num_results=5)

    def search_for_trends(self, topic: str) -> str:
        """
        Search for trends and recent developments.

        Args:
            topic: Topic to research trends for

        Returns:
            Formatted trend information
        """
        query = f"{topic} trends 2025 2026 developments innovations"
        return self.search_and_format(query, num_results=5)


# Singleton instance for reuse
_web_search_instance: WebSearchTool | None = None


def get_web_search_tool(api_key: str | None = None) -> WebSearchTool:
    """
    Get or create the web search tool singleton.

    Args:
        api_key: Serper API key (uses cached instance if not provided)

    Returns:
        WebSearchTool instance
    """
    global _web_search_instance

    if api_key:
        _web_search_instance = WebSearchTool(api_key)
    elif _web_search_instance is None:
        # Create with empty key (will return errors on search)
        _web_search_instance = WebSearchTool("")

    return _web_search_instance
