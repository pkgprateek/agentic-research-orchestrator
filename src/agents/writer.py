"""Writer Agent for generating professional market intelligence reports."""

from datetime import datetime
from typing import Any, Dict, Optional

from src.agents.base import BaseAgent
from src.utils.cost_tracker import CostTracker
from src.utils.logging import setup_logger

logger = setup_logger(__name__)


class WriterAgent(BaseAgent):
    """
    Writer Agent responsible for generating final reports.

    Takes research and analysis data and creates:
    - Executive summary
    - Comprehensive market intelligence report
    - Properly formatted markdown with citations
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.6,  # Higher for better writing quality
        cost_tracker: Optional[CostTracker] = None,
    ):
        """
        Initialize Writer Agent.

        Args:
            model: LLM model to use
            temperature: Sampling temperature
            cost_tracker: Cost tracker instance
        """
        super().__init__(
            name="WriterAgent",
            model=model,
            temperature=temperature,
            cost_tracker=cost_tracker,
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for writer agent."""
        return """You are a professional business report writer specializing in market intelligence and competitive analysis.

Your role is to transform research and analysis into polished, executive-ready reports.

When writing reports, you should:
1. Use clear, professional business language
2. Structure content logically with proper headings
3. Include executive summaries for busy stakeholders
4. Use bullet points and tables for scannability
5. Cite sources properly
6. Make insights actionable

Report format guidelines:
- Use markdown formatting
- Include clear section headers (#, ##, ###)
- Use tables for competitive comparisons
- Include bullet points for lists
- Add citations [source]
- Keep executive summary to 200-300 words

Write for senior executives and decision-makers."""

    async def run(
        self,
        research_data: Dict[str, Any],
        analysis_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate comprehensive market intelligence report.

        Args:
            research_data: Output from ResearchAgent
            analysis_data: Output from AnalysisAgent

        Returns:
            Dictionary with report components:
                - executive_summary: Brief overview
                - full_report: Complete markdown report
                - metadata: Report metadata (date, sources count, etc.)
        """
        company_name = research_data.get("company_name", "Unknown Company")
        logger.info(f"Starting report generation for: {company_name}")

        try:
            # Generate report sections
            exec_summary = await self._write_executive_summary(
                research_data, analysis_data
            )

            full_report = await self._write_full_report(
                research_data, analysis_data, exec_summary
            )

            # Gather metadata
            metadata = {
                "company_name": company_name,
                "industry": research_data.get("industry"),
                "generated_date": datetime.now().isoformat(),
                "sources_count": len(research_data.get("raw_sources", [])),
                "model_used": self.model_name,
            }

            logger.info(f"Report generation complete for {company_name}")

            return {
                "executive_summary": exec_summary,
                "full_report": full_report,
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"Report generation failed for {company_name}: {e}")
            raise

    async def _write_executive_summary(
        self,
        research_data: Dict[str, Any],
        analysis_data: Dict[str, Any],
    ) -> str:
        """
        Write executive summary (200-300 words).

        Args:
            research_data: Research results
            analysis_data: Analysis results

        Returns:
            Executive summary text
        """
        company_name = research_data.get("company_name")

        user_message = f"""Write a concise executive summary for a market intelligence report on {company_name}.

Use this information:

COMPANY OVERVIEW:
{research_data.get("company_overview", "")}

KEY INSIGHTS FROM SWOT:
{analysis_data.get("swot", "")}

STRATEGIC RECOMMENDATIONS:
{analysis_data.get("strategic_recommendations", "")}

Requirements:
- 200-300 words
- Cover: company overview, market position, key findings, main recommendations
- Written for senior executives (clear, actionable)
- Professional business tone

Start directly with content (no "Executive Summary" heading)."""

        messages = self._create_messages(user_message)
        response = await self._invoke_llm(messages)

        return response

    async def _write_full_report(
        self,
        research_data: Dict[str, Any],
        analysis_data: Dict[str, Any],
        exec_summary: str,
    ) -> str:
        """
        Write complete markdown report.

        Args:
            research_data: Research results
            analysis_data: Analysis results
            exec_summary: Executive summary

        Returns:
            Full report in markdown format
        """
        company_name = research_data.get("company_name")
        industry = research_data.get("industry") or "Market"

        # Build comprehensive context
        context = f"""
COMPANY: {company_name}
INDUSTRY: {industry}

RESEARCH DATA:
Company Overview: {research_data.get("company_overview", "")}
Competitors: {research_data.get("competitors", "")}
Market Trends: {research_data.get("market_trends", "")}

ANALYSIS DATA:
SWOT: {analysis_data.get("swot", "")}
Competitive Matrix: {analysis_data.get("competitive_matrix", "")}
Market Positioning: {analysis_data.get("positioning", "")}
Strategic Recommendations: {analysis_data.get("strategic_recommendations", "")}

EXECUTIVE SUMMARY:
{exec_summary}
"""

        user_message = f"""Create a comprehensive market intelligence report for {company_name} in markdown format.

Use all the provided research and analysis data.

Structure the report as follows:

# Market Intelligence Report: {company_name}

## Executive Summary
[Insert the provided executive summary]

## 1. Company Overview
[Detailed company information from research]

## 2. Competitive Landscape
[Competitor analysis and competitive matrix]

## 3. SWOT Analysis
[Detailed SWOT with clear sections: Strengths, Weaknesses, Opportunities, Threats]

## 4. Market Positioning
[Positioning analysis and differentiation]

## 5. Market Trends & Insights
[Industry trends and market dynamics]

## 6. Strategic Recommendations
[Prioritized recommendations with rationale]

## 7. Sources
[List key sources used]

---
Report generated: {datetime.now().strftime("%B %d, %Y")}

Data to use:
{context}

Format requirements:
- Use proper markdown (headers, bullets, tables)
- Make it professional and polished
- Include all relevant details
- Cite sources where appropriate
- Make it actionable for executives"""

        messages = self._create_messages(user_message)
        response = await self._invoke_llm(messages)

        return response
