"""Unit tests for LangGraph workflow state and nodes."""

import pytest

from src.workflows.state import IntelligenceState
from src.workflows.intelligence import MarketIntelligenceWorkflow


class TestIntelligenceState:
    """Test state schema validation."""

    def test_state_has_required_fields(self):
        """Verify state schema has all required fields."""
        required_fields = [
            "company_name",
            "industry",
            "research_data",
            "competitors",
            "market_trends",
            "raw_sources",
            "swot",
            "competitive_matrix",
            "positioning",
            "strategic_recommendations",
            "executive_summary",
            "full_report",
            "report_metadata",
            "current_agent",
            "iteration",
            "total_cost",
            "total_tokens",
            "errors",
            "human_feedback",
            "approved",
            "revision_count",
        ]

        state_annotations = IntelligenceState.__annotations__

        for field in required_fields:
            assert field in state_annotations, f"Missing required field: {field}"


class TestWorkflowInitialization:
    """Test workflow initialization."""

    def test_workflow_initializes(self):
        """Test workflow can be initialized."""
        workflow = MarketIntelligenceWorkflow()

        assert workflow is not None
        assert workflow.max_budget == 2.0
        assert workflow.research_agent is not None
        assert workflow.analysis_agent is not None
        assert workflow.writer_agent is not None

    def test_custom_budget(self):
        """Test workflow with custom budget."""
        workflow = MarketIntelligenceWorkflow(max_budget=5.0)

        assert workflow.max_budget == 5.0


class TestConditionalRouting:
    """Test workflow routing logic."""

    def test_should_continue_to_analysis_success(self):
        """Test routing to analysis when research succeeds."""
        workflow = MarketIntelligenceWorkflow()

        state = {
            "research_data": {"some": "data"},
            "errors": [],
        }

        result = workflow._should_continue_to_analysis(state)
        assert result == "analysis"

    def test_should_continue_to_analysis_with_errors(self):
        """Test routing ends when research has errors."""
        workflow = MarketIntelligenceWorkflow()

        state = {
            "research_data": {},
            "errors": ["Some error"],
        }

        result = workflow._should_continue_to_analysis(state)
        assert result == "end"

    def test_should_continue_to_analysis_no_data(self):
        """Test routing ends when no research data."""
        workflow = MarketIntelligenceWorkflow()

        state = {
            "errors": [],
        }

        result = workflow._should_continue_to_analysis(state)
        assert result == "end"

    def test_check_approval_approved(self):
        """Test approval check when approved."""
        workflow = MarketIntelligenceWorkflow()

        state = {
            "approved": True,
            "revision_count": 0,
        }

        result = workflow._check_approval(state)
        assert result == "approved"

    def test_check_approval_max_revisions(self):
        """Test approval check at max revisions."""
        workflow = MarketIntelligenceWorkflow()

        state = {
            "approved": False,
            "revision_count": 2,
        }

        result = workflow._check_approval(state)
        assert result == "max_revisions"

    def test_check_approval_revision_requested(self):
        """Test approval check with feedback."""
        workflow = MarketIntelligenceWorkflow()

        state = {
            "approved": False,
            "revision_count": 0,
            "human_feedback": "Please add more details",
        }

        result = workflow._check_approval(state)
        assert result == "revise"


@pytest.mark.asyncio
class TestWorkflowNodes:
    """Test individual workflow nodes."""

    async def test_research_node_structure(self):
        """Test research node returns correct state structure."""
        workflow = MarketIntelligenceWorkflow()

        state = {
            "company_name": "Test Company",
            "industry": "Technology",
            "iteration": 0,
        }

        # This will make real API calls, so we just test structure
        # In a real test, we'd mock the agents
        result = await workflow._research_node(state)

        assert "current_agent" in result
        assert result["current_agent"] == "research"
        assert "iteration" in result

    async def test_human_review_node_auto_approves(self):
        """Test human review node auto-approves for now."""
        workflow = MarketIntelligenceWorkflow()

        state = {
            "company_name": "Test Company",
        }

        result = await workflow._human_review_node(state)

        assert result["current_agent"] == "human_review"
        assert result["approved"] is True
        assert result["human_feedback"] is None
