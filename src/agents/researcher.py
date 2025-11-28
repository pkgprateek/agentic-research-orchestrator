"""Research Agent for gathering market intelligence data."""

from typing import Any, Dict, Optional

from src.agents.base import BaseAgent
from src.tools.search import TavilySearchTool
from src.utils.cost_tracker import CostTracker
from src.utils.logging import setup_logger

logger = setup_logger(__name__)


class ResearchAgent(BaseAgent):
    """
    Research Agent responsible for gathering data from web sources.

    Uses Tavily API for web search and can gather:
    - Company information
    - Competitor analysis data
    - Market trends and insights
    - Industry news
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.3,  # Lower for more factual responses
        cost_tracker: Optional[CostTracker] = None,
    ):
        """
        Initialize Research Agent.

        Args:
            model: LLM model to use
            temperature: Sampling temperature (lower for research)
            cost_tracker: Cost tracker instance
        """
        super().__init__(
            name="ResearchAgent",
            model=model,
            temperature=temperature,
            cost_tracker=cost_tracker,
        )

        self.search_tool = TavilySearchTool()

    def get_system_prompt(self) -> str:
        """Get system prompt for research agent."""
        return """You are a professional business research analyst specializing in competitive intelligence.

Your role is to gather and synthesize information about companies, markets, and competitors from web sources.

When analyzing search results, you should:
1. Focus on factual, verifiable information
2. Identify key data points: revenue, employees, products, market position
3. Note dates and sources for important claims
4. Distinguish between facts and opinions
5. Highlight competitive advantages and weaknesses

Provide your analysis in a structured format with clear sections and bullet points.
Always cite sources when making specific claims."""

    async def run(
        self,
        company_name: str,
        industry: Optional[str] = None,
        research_depth: str = "comprehensive",
    ) -> Dict[str, Any]:
        """
        Gather research data about a company.

        Args:
            company_name: Target company name
            industry: Optional industry context
            research_depth: "basic" or "comprehensive"

        Returns:
            Dictionary with research results:
                - company_overview: Company information
                - competitors: Competitor analysis
                - market_trends: Industry trends
                - raw_sources: List of sources used
        """
        logger.info(f"Starting research for: {company_name}")

        results = {
            "company_name": company_name,
            "industry": industry,
            "company_overview": "",
            "competitors": "",
            "market_trends": "",
            "raw_sources": [],
        }

        try:
            # 1. Company Overview
            company_data = await self.search_tool.get_company_info(
                company_name=company_name,
                max_results=10 if research_depth == "comprehensive" else 5,
            )

            results["raw_sources"].extend(company_data.get("results", []))

            # Analyze company data with LLM
            company_context = self.search_tool.format_results_for_llm(company_data)
            company_analysis = await self._analyze_company(
                company_name, company_context
            )
            results["company_overview"] = company_analysis

            # 2. Competitor Analysis
            competitor_data = await self.search_tool.get_competitor_info(
                company_name=company_name,
                industry=industry,
                max_results=10 if research_depth == "comprehensive" else 5,
            )

            results["raw_sources"].extend(competitor_data.get("results", []))

            competitor_context = self.search_tool.format_results_for_llm(
                competitor_data
            )
            competitor_analysis = await self._analyze_competitors(
                company_name, competitor_context
            )
            results["competitors"] = competitor_analysis

            # 3. Market Trends (if industry provided)
            if industry:
                trend_data = await self.search_tool.get_market_trends(
                    industry=industry,
                    max_results=8 if research_depth == "comprehensive" else 4,
                )

                results["raw_sources"].extend(trend_data.get("results", []))

                trend_context = self.search_tool.format_results_for_llm(trend_data)
                trend_analysis = await self._analyze_trends(industry, trend_context)
                results["market_trends"] = trend_analysis

            logger.info(
                f"Research complete for {company_name}. "
                f"Processed {len(results['raw_sources'])} sources"
            )

            return results

        except Exception as e:
            logger.error(f"Research failed for {company_name}: {e}")
            raise

    async def _analyze_company(
        self,
        company_name: str,
        search_context: str,
    ) -> str:
        """
        Analyze company information from search results.

        Args:
            company_name: Company name
            search_context: Formatted search results

        Returns:
            Structured company analysis
        """
        user_message = f"""Analyze the following search results about {company_name}.

Provide a structured analysis covering:
1. Company Overview (founded, headquarters, size)
2. Products & Services (main offerings)
3. Business Model (how they make money)
4. Market Position (market share, ranking)
5. Key Metrics (revenue, employees, growth)

Search Results:
{search_context}

Provide your analysis in clear sections with bullet points. Cite sources for specific claims."""

        messages = self._create_messages(user_message)
        response = await self._invoke_llm(messages)

        return response

    async def _analyze_competitors(
        self,
        company_name: str,
        search_context: str,
    ) -> str:
        """
        Analyze competitor landscape.

        Args:
            company_name: Target company
            search_context: Formatted search results

        Returns:
            Competitor analysis
        """
        user_message = f"""Analyze the competitive landscape for {company_name}.

Based on the search results, identify:
1. Main Competitors (list 3-5 key competitors)
2. Competitive Positioning (how each differs)
3. Market Dynamics (who leads, who follows)
4. Differentiation Factors (what makes each unique)

Search Results:
{search_context}

Format as a structured list with clear comparisons."""

        messages = self._create_messages(user_message)
        response = await self._invoke_llm(messages)

        return response

    async def _analyze_trends(
        self,
        industry: str,
        search_context: str,
    ) -> str:
        """
        Analyze market trends.

        Args:
            industry: Industry name
            search_context: Formatted search results

        Returns:
            Trend analysis
        """
        user_message = f"""Analyze market trends for the {industry} industry.

Identify:
1. Key Trends (major shifts in the market)
2. Growth Drivers (what's fueling growth)
3. Challenges (obstacles facing the industry)
4. Future Outlook (predictions for next 1-2 years)

Search Results:
{search_context}

Provide analysis with clear trends and supporting evidence."""

        messages = self._create_messages(user_message)
        response = await self._invoke_llm(messages)

        return response
