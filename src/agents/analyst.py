"""Analysis Agent for competitive intelligence and SWOT analysis."""

from typing import Any, Dict, List, Optional

from src.agents.base import BaseAgent
from src.utils.cost_tracker import CostTracker
from src.utils.logging import setup_logger

logger = setup_logger(__name__)


class AnalysisAgent(BaseAgent):
    """
    Analysis Agent responsible for strategic business analysis.

    Takes research data and produces:
    - SWOT analysis
    - Competitive matrix
    - Market positioning analysis
    - Strategic recommendations
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.4,  # Balanced for analytical reasoning
        cost_tracker: Optional[CostTracker] = None,
    ):
        """
        Initialize Analysis Agent.

        Args:
            model: LLM model to use
            temperature: Sampling temperature
            cost_tracker: Cost tracker instance
        """
        super().__init__(
            name="AnalysisAgent",
            model=model,
            temperature=temperature,
            cost_tracker=cost_tracker,
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for analysis agent."""
        return """You are a strategic business analyst specializing in competitive intelligence and market analysis.

Your role is to analyze research data and provide actionable strategic insights.

When performing analysis, you should:
1. Use structured frameworks (SWOT, competitive matrices, positioning maps)
2. Identify clear patterns and trends
3. Provide specific, actionable recommendations
4. Support conclusions with evidence from the research
5. Consider multiple perspectives (competitors, customers, market forces)

Your analysis should be:
- Objective and data-driven
- Structured and easy to scan
- Focused on business impact
- Actionable for decision-makers

Use bullet points, clear headings, and strategic language."""

    async def run(
        self,
        research_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Perform comprehensive analysis on research data.

        Args:
            research_data: Output from ResearchAgent containing:
                - company_overview
                - competitors
                - market_trends

        Returns:
            Dictionary with analysis results:
                - swot: SWOT analysis
                - competitive_matrix: Competitor comparison
                - positioning: Market positioning analysis
                - strategic_recommendations: Action items
        """
        company_name = research_data.get("company_name", "Unknown Company")
        logger.info(f"Starting analysis for: {company_name}")

        results = {
            "company_name": company_name,
            "swot": "",
            "competitive_matrix": "",
            "positioning": "",
            "strategic_recommendations": "",
        }

        try:
            # 1. SWOT Analysis
            swot = await self._perform_swot_analysis(research_data)
            results["swot"] = swot

            # 2. Competitive Matrix
            matrix = await self._create_competitive_matrix(research_data)
            results["competitive_matrix"] = matrix

            # 3. Market Positioning
            positioning = await self._analyze_market_positioning(research_data)
            results["positioning"] = positioning

            # 4. Strategic Recommendations
            recommendations = await self._generate_recommendations(research_data, swot)
            results["strategic_recommendations"] = recommendations

            logger.info(f"Analysis complete for {company_name}")

            return results

        except Exception as e:
            logger.error(f"Analysis failed for {company_name}: {e}")
            raise

    async def _perform_swot_analysis(
        self,
        research_data: Dict[str, Any],
    ) -> str:
        """
        Generate SWOT analysis from research data.

        Args:
            research_data: Research results

        Returns:
            SWOT analysis text
        """
        company_name = research_data.get("company_name")
        company_overview = research_data.get("company_overview", "")
        competitors = research_data.get("competitors", "")
        market_trends = research_data.get("market_trends", "")

        user_message = f"""Based on the research data, perform a comprehensive SWOT analysis for {company_name}.

Research Data:

COMPANY OVERVIEW:
{company_overview}

COMPETITORS:
{competitors}

MARKET TRENDS:
{market_trends}

Provide a detailed SWOT analysis with:

STRENGTHS (internal positive factors):
- List 4-6 key strengths
- Focus on competitive advantages, resources, capabilities

WEAKNESSES (internal negative factors):
- List 4-6 key weaknesses
- Include operational limits, resource constraints, vulnerabilities

OPPORTUNITIES (external positive factors):
- List 4-6 market opportunities
- Consider market trends, gaps, emerging needs

THREATS (external negative factors):
- List 4-6 threats
- Include competitive threats, market risks, industry challenges

Use bullet points and be specific with evidence."""

        messages = self._create_messages(user_message)
        response = await self._invoke_llm(messages)

        return response

    async def _create_competitive_matrix(
        self,
        research_data: Dict[str, Any],
    ) -> str:
        """
        Create competitive comparison matrix.

        Args:
            research_data: Research results

        Returns:
            Competitive matrix as formatted text
        """
        company_name = research_data.get("company_name")
        competitors_info = research_data.get("competitors", "")

        user_message = f"""Based on the competitor research, create a competitive matrix comparing {company_name} with its main competitors.

Competitor Research:
{competitors_info}

Create a comparison matrix with these dimensions:
1. Market Share/Size
2. Product Range
3. Pricing Strategy
4. Technology/Innovation
5. Customer Segments
6. Strengths
7. Weaknesses

Format as a clear table or structured comparison.
Include 3-5 main competitors plus {company_name}.
Use "High/Medium/Low" or specific data points where available."""

        messages = self._create_messages(user_message)
        response = await self._invoke_llm(messages)

        return response

    async def _analyze_market_positioning(
        self,
        research_data: Dict[str, Any],
    ) -> str:
        """
        Analyze market positioning strategy.

        Args:
            research_data: Research results

        Returns:
            Positioning analysis
        """
        company_name = research_data.get("company_name")
        company_overview = research_data.get("company_overview", "")
        competitors = research_data.get("competitors", "")

        user_message = f"""Analyze the market positioning of {company_name}.

Company Overview:
{company_overview}

Competitive Landscape:
{competitors}

Provide analysis covering:

1. CURRENT POSITIONING
   - How is {company_name} currently positioned in the market?
   - What is their value proposition?
   - What customer segments do they target?

2. COMPETITIVE DIFFERENTIATION
   - What makes {company_name} different from competitors?
   - What is their unique selling proposition (USP)?
   - Where do they fit in the competitive landscape?

3. POSITIONING GAPS
   - Are there market segments they're missing?
   - Are there positioning opportunities?
   - How could they strengthen their position?

Be specific and strategic."""

        messages = self._create_messages(user_message)
        response = await self._invoke_llm(messages)

        return response

    async def _generate_recommendations(
        self,
        research_data: Dict[str, Any],
        swot: str,
    ) -> str:
        """
        Generate strategic recommendations.

        Args:
            research_data: Research results
            swot: SWOT analysis

        Returns:
            Strategic recommendations
        """
        company_name = research_data.get("company_name")
        market_trends = research_data.get("market_trends", "")

        user_message = f"""Based on the SWOT analysis and market trends, provide strategic recommendations for {company_name}.

SWOT ANALYSIS:
{swot}

MARKET TRENDS:
{market_trends}

Provide 5-7 actionable strategic recommendations organized by priority:

HIGH PRIORITY (immediate action needed):
- Recommendation 1 (with rationale)
- Recommendation 2 (with rationale)

MEDIUM PRIORITY (next 6-12 months):
- Recommendation 3 (with rationale)
- Recommendation 4 (with rationale)

LONG-TERM (strategic initiatives):
- Recommendation 5 (with rationale)

Each recommendation should:
- Be specific and actionable
- Address a key opportunity or threat
- Leverage strengths or address weaknesses
- Include expected impact"""

        messages = self._create_messages(user_message)
        response = await self._invoke_llm(messages)

        return response
