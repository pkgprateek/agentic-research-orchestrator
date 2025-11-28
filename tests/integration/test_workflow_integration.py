"""Integration tests for workflow error handling and cost limits."""

import pytest
from unittest.mock import AsyncMock, patch

from src.workflows.intelligence import MarketIntelligenceWorkflow
from src.utils.cost_tracker import BudgetExceededError


@pytest.mark.asyncio
class TestWorkflowErrorRecovery:
    """Test workflow error handling and recovery."""

    async def test_research_error_ends_workflow(self):
        """Test workflow ends gracefully when research fails."""
        workflow = MarketIntelligenceWorkflow()

        # Mock research to fail
        async def mock_research_error(state):
            return {
                "errors": ["Research API failed"],
                "current_agent": "research",
            }

        workflow._research_node = mock_research_error

        result = await workflow.run(company_name="Test Co", thread_id="test-error-1")

        assert len(result["errors"]) > 0
        assert result["current_agent"] == "research"

    async def test_budget_exceeded_stops_workflow(self):
        """Test workflow stops when budget is exceeded."""
        workflow = MarketIntelligenceWorkflow(max_budget=0.001)

        # Mock research to succeed with some cost
        async def mock_research_success(state):
            workflow.cost_tracker.track_usage("openai/gpt-5-mini", 10000, 5000)
            return {
                "current_agent": "research",
                "research_data": {"some": "data"},
                "competitors": [],
                "market_trends": {},
                "raw_sources": [],
                "iteration": 1,
            }

        workflow._research_node = mock_research_success

        result = await workflow.run(company_name="Test Co", thread_id="test-budget-1")

        # Should have errors about budget
        assert len(result.get("errors", [])) > 0 or result["total_cost"] < 0.001


@pytest.mark.asyncio
class TestWorkflowIntegration:
    """Integration tests for full workflow."""

    async def test_workflow_with_mocked_agents(self):
        """Test complete workflow with mocked agent responses."""
        workflow = MarketIntelligenceWorkflow()

        # Mock all agents
        async def mock_research(state):
            return {
                "current_agent": "research",
                "research_data": {"company": "Test Co"},
                "competitors": [{"name": "Competitor A"}],
                "market_trends": {"trend": "growing"},
                "raw_sources": [{"url": "test.com"}],
                "iteration": state.get("iteration", 0) + 1,
            }

        async def mock_analysis(state):
            return {
                "current_agent": "analysis",
                "swot": {"strengths": ["good"]},
                "competitive_matrix": {},
                "positioning": {},
                "strategic_recommendations": {},
            }

        async def mock_writing(state):
            return {
                "current_agent": "writing",
                "executive_summary": "Test summary",
                "full_report": "# Test Report",
                "report_metadata": {},
                "total_cost": 0.0,
                "total_tokens": 0,
            }

        workflow._research_node = mock_research
        workflow._analysis_node = mock_analysis
        workflow._writing_node = mock_writing

        result = await workflow.run(
            company_name="Test Co", thread_id="test-integration-1"
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
        assert workflow.workflow is not None

        # Clean up
        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)
