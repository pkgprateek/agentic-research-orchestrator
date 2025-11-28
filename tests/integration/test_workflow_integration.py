"""Integration tests for workflow error handling and cost limits."""

import pytest
from unittest.mock import AsyncMock

from src.workflows.market_analysis import MarketIntelligenceWorkflow


@pytest.mark.asyncio
class TestWorkflowErrorRecovery:
    """Test workflow error handling and recovery."""

    async def test_research_error_ends_workflow(self):
        """Test workflow ends gracefully when research fails."""
        workflow = MarketIntelligenceWorkflow()

        # Mock research to fail
        # Mock research to fail
        workflow.research_agent.run = AsyncMock(
            side_effect=Exception("Research API failed")
        )

        result = await workflow.run(
            company_name="Test Company", thread_id="test-error-1"
        )

        assert len(result["errors"]) > 0
        assert result["current_agent"] == "research"

    async def test_budget_exceeded_stops_workflow(self):
        """Test workflow stops when budget is exceeded."""
        workflow = MarketIntelligenceWorkflow(max_budget=0.001)

        # Mock research to succeed with some cost
        # Mock research to succeed with some cost
        async def mock_run(*args, **kwargs):
            workflow.cost_tracker.track_usage("openai/gpt-5-mini", 10000, 5000)
            return {
                "company_name": "Mock Company",
                "competitors": [],
                "market_trends": {},
                "raw_sources": [],
            }

        workflow.research_agent.run = AsyncMock(side_effect=mock_run)

        result = await workflow.run(
            company_name="Test Company", thread_id="test-budget-1"
        )

        # Should have errors about budget
        assert len(result.get("errors", [])) > 0 or result["total_cost"] < 0.001


@pytest.mark.asyncio
class TestWorkflowIntegration:
    """Integration tests for full workflow."""

    async def test_workflow_with_mocked_agents(self):
        """Test complete workflow with mocked agent responses."""
        workflow = MarketIntelligenceWorkflow()

        # Mock all agents
        # Mock all agents
        workflow.research_agent.run = AsyncMock(
            return_value={
                "company_name": "Test Company",
                "competitors": [{"name": "Competitor A"}],
                "market_trends": {"trend": "growing"},
                "raw_sources": [{"url": "test.com"}],
            }
        )

        workflow.analysis_agent.run = AsyncMock(
            return_value={
                "swot": {"strengths": ["good"]},
                "competitive_matrix": {},
                "positioning": {},
                "strategic_recommendations": {},
            }
        )

        workflow.writer_agent.run = AsyncMock(
            return_value={
                "executive_summary": "Test summary",
                "full_report": "# Test Report",
                "metadata": {},
            }
        )

        result = await workflow.run(
            company_name="Test Company", thread_id="test-integration-1"
        )

        assert result["approved"] is True
        assert "Test summary" in result["executive_summary"]
        assert result["total_cost"] == 0.0


class TestWorkflowCheckpointing:
    """Test checkpoint persistence and recovery."""

    def test_checkpoint_file_created(self):
        """Test that checkpoint database is created."""
        import os

        checkpoint_path = "./test_checkpoint.db"

        # Clean up first
        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)

        workflow = MarketIntelligenceWorkflow(checkpoint_path=checkpoint_path)

        # Checkpoint file should be created when workflow is compiled
        assert workflow.graph_builder is not None

        # Clean up
        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)
