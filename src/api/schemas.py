"""Pydantic schemas for API request/response models."""

from typing import Literal
from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """Request to analyze a company/product."""

    company_name: str = Field(
        ...,
        description="Name of company or product to analyze",
        min_length=1,
        max_length=200,
        examples=["Tesla Model Y", "Notion", "ChatGPT"],
    )

    industry: str | None = Field(
        None,
        description="Industry context (optional)",
        max_length=100,
        examples=["Electric Vehicles", "Productivity Software", "AI"],
    )

    model: str = Field(
        default="x-ai/grok-4.1-fast:free",
        description="LLM model to use",
        examples=[
            "x-ai/grok-4.1-fast:free",
            "anthropic/claude-sonnet-4.5",
            "openai/gpt-5-mini",
        ],
    )

    max_budget: float = Field(
        default=2.0, ge=0.0, le=10.0, description="Maximum cost in USD"
    )


class AnalysisResponse(BaseModel):
    """Response from analysis endpoint."""

    run_id: str = Field(..., description="Unique run identifier")
    status: Literal["pending", "running", "completed", "failed"] = Field(
        ..., description="Current status"
    )
    company_name: str = Field(..., description="Company being analyzed")

    # Results (populated when completed)
    executive_summary: str | None = Field(None, description="Executive summary")
    full_report: str | None = Field(None, description="Full markdown report")

    # Metadata
    total_cost: float = Field(default=0.0, description="Total cost in USD")
    total_tokens: int = Field(default=0, description="Total tokens used")
    sources_count: int = Field(default=0, description="Number of sources processed")

    # Errors
    errors: list[str] = Field(default_factory=list, description="Error messages")

    # Human approval
    approved: bool = Field(default=False, description="Human approval status")


class StatusResponse(BaseModel):
    """Response for status check."""

    run_id: str
    status: Literal["pending", "running", "completed", "failed"]
    current_agent: str | None = Field(None, description="Currently executing agent")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Progress 0-1")
    message: str | None = Field(None, description="Status message")


class HistoryItem(BaseModel):
    """Historical analysis item."""

    run_id: str
    company_name: str
    created_at: str
    status: str
    total_cost: float
    approved: bool


class HistoryResponse(BaseModel):
    """Response for history endpoint."""

    analyses: list[HistoryItem]
    total: int
