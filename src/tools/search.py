"""Search tools for web research using Tavily API."""

from typing import Dict, List, Optional

from tavily import TavilyClient

from src.utils.config import get_settings
from src.utils.logging import setup_logger

logger = setup_logger(__name__)


class TavilySearchTool:
    """
    Wrapper for Tavily search API optimized for research agents.

    Tavily is designed for AI agents and provides clean, structured
    results ideal for LLM consumption.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Tavily search tool.

        Args:
            api_key: Optional Tavily API key (uses config if None)
        """
        settings = get_settings()
        self.api_key = api_key or settings.tavily_api_key
        self.client = TavilyClient(api_key=self.api_key)

        logger.info("Tavily search tool initialized")

    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "advanced",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> Dict:
        """
        Perform web search using Tavily.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            search_depth: "basic" or "advanced" (advanced is more comprehensive)
            include_domains: Optional list of domains to include
            exclude_domains: Optional list of domains to exclude

        Returns:
            Dictionary with search results:
                - results: List of search results
                - query: Original query
                - answer: Tavily's AI-generated answer (if available)
        """
        try:
            logger.info(f"Tavily search: {query}")

            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
            )

            logger.info(f"Tavily returned {len(response.get('results', []))} results")

            return response

        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            raise

    async def get_company_info(
        self,
        company_name: str,
        max_results: int = 10,
    ) -> Dict:
        """
        Get comprehensive company information.

        Args:
            company_name: Company name to research
            max_results: Maximum results to retrieve

        Returns:
            Search results focused on company information
        """
        query = f"{company_name} company overview products services business model"
        return await self.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
        )

    async def get_competitor_info(
        self,
        company_name: str,
        industry: Optional[str] = None,
        max_results: int = 10,
    ) -> Dict:
        """
        Find competitors for a given company.

        Args:
            company_name: Company name
            industry: Optional industry context
            max_results: Maximum results

        Returns:
            Search results about competitors
        """
        industry_context = f"in {industry}" if industry else ""
        query = f"{company_name} competitors alternatives {industry_context}"

        return await self.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
        )

    async def get_market_trends(
        self,
        industry: str,
        year: Optional[str] = "2025",
        max_results: int = 8,
    ) -> Dict:
        """
        Get market trends for an industry.

        Args:
            industry: Industry name
            year: Year for trends (default: 2025)
            max_results: Maximum results

        Returns:
            Search results about market trends
        """
        query = f"{industry} market trends {year} growth forecast opportunities"

        return await self.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
        )

    def format_results_for_llm(self, search_response: Dict) -> str:
        """
        Format search results for LLM consumption.

        Args:
            search_response: Tavily search response

        Returns:
            Formatted string with search results
        """
        results = search_response.get("results", [])

        if not results:
            return "No search results found."

        formatted = []
        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            url = result.get("url", "")
            content = result.get("content", "No content")
            score = result.get("score", 0)

            formatted.append(
                f"[{i}] {title}\n"
                f"URL: {url}\n"
                f"Relevance: {score:.2f}\n"
                f"Content: {content}\n"
            )

        # Add AI answer if available
        if answer := search_response.get("answer"):
            formatted.insert(0, f"AI Summary: {answer}\n\n")

        return "\n".join(formatted)


class WikipediaSearchTool:
    """
    Wikipedia search for factual company/product information.

    Note: This is a simple wrapper. For production, consider using
    the wikipedia-api library for more robust access.
    """

    def __init__(self):
        """Initialize Wikipedia search tool."""
        logger.info("Wikipedia search tool initialized")

    async def search(self, query: str, max_results: int = 3) -> Dict:
        """
        Search Wikipedia (placeholder for now).

        Args:
            query: Search query
            max_results: Maximum results

        Returns:
            Search results dictionary
        """
        # TODO: Implement actual Wikipedia API integration
        # For now, we'll use Tavily which can search Wikipedia
        logger.info(f"Wikipedia search: {query}")

        return {
            "query": query,
            "results": [],
            "note": "Wikipedia integration pending - using Tavily for now",
        }
