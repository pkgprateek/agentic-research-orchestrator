"""State definitions for LangGraph workflow."""

from typing import Annotated, Literal, TypedDict
import operator


class IntelligenceState(TypedDict):
    """
    State for market intelligence workflow.

    This state is passed between agents and persisted across checkpoints.
    """

    # Input
    company_name: str
    industry: str | None

    # Research phase outputs
    research_data: dict
    competitors: list[dict]
    market_trends: dict
    raw_sources: list[dict]

    # Analysis phase outputs
    swot: dict
    competitive_matrix: dict
    positioning: dict
    strategic_recommendations: dict

    # Writing phase outputs
    executive_summary: str
    full_report: str
    report_metadata: dict

    # Workflow metadata
    current_agent: Literal["research", "analysis", "writing", "human_review", "done"]
    iteration: int
    total_cost: float
    total_tokens: int
    errors: Annotated[list, operator.add]  # Accumulate errors across nodes

    # Human-in-the-loop
    human_feedback: str | None
    approved: bool
    revision_count: int
