"""Main LangGraph workflow for market intelligence."""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from src.workflows.state import IntelligenceState
from src.agents.researcher import ResearchAgent
from src.agents.analyst import AnalysisAgent
from src.agents.writer import WriterAgent
from src.utils.cost_tracker import CostTracker, BudgetExceededError
from src.utils.logging import setup_logger

logger = setup_logger(__name__)


class MarketIntelligenceWorkflow:
    """
    LangGraph workflow orchestrating research, analysis, and writing agents.

    Features:
    - Multi-agent coordination
    - State persistence with checkpointing
    - Cost tracking and budget enforcement
    - Human-in-the-loop approval
    - Error recovery
    """

    def __init__(
        self, checkpoint_path: str = "./checkpoints.db", max_budget: float = 2.0
    ):
        """
        Initialize workflow.

        Args:
            checkpoint_path: Path to SQLite checkpoint database
            max_budget: Maximum cost per run in USD
        """
        self.max_budget = max_budget
        self.cost_tracker = CostTracker()
        self.checkpoint_path = checkpoint_path

        # Initialize agents (shared cost tracker)
        self.research_agent = ResearchAgent(cost_tracker=self.cost_tracker)
        self.analysis_agent = AnalysisAgent(cost_tracker=self.cost_tracker)
        self.writer_agent = WriterAgent(cost_tracker=self.cost_tracker)

        # Build workflow graph
        self.workflow = self._build_graph()

        logger.info("Market Intelligence Workflow initialized")

    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow."""
        # Initialize graph
        graph = StateGraph(IntelligenceState)

        # Add nodes (agent wrappers)
        graph.add_node("research", self._research_node)
        graph.add_node("analysis", self._analysis_node)
        graph.add_node("writing", self._writing_node)
        graph.add_node("human_review", self._human_review_node)

        # Set entry point
        graph.set_entry_point("research")

        # Add edges
        graph.add_conditional_edges(
            "research",
            self._should_continue_to_analysis,
            {"analysis": "analysis", "end": END},
        )

        graph.add_edge("analysis", "writing")
        graph.add_edge("writing", "human_review")

        graph.add_conditional_edges(
            "human_review",
            self._check_approval,
            {"approved": END, "revise": "research", "max_revisions": END},
        )

        # Compile with SQLite checkpointing for production persistence
        checkpointer = SqliteSaver.from_conn_string(self.checkpoint_path)
        return graph.compile(checkpointer=checkpointer)

    async def _research_node(self, state: IntelligenceState) -> dict:
        """Research agent node."""
        logger.info(f"Research node: {state['company_name']}")

        try:
            # Run research agent
            research_results = await self.research_agent.run(
                company_name=state["company_name"],
                industry=state.get("industry"),
                research_depth="comprehensive",
            )

            # Update state
            return {
                "current_agent": "research",
                "research_data": research_results,
                "competitors": research_results.get("competitors", []),
                "market_trends": research_results.get("market_trends", {}),
                "raw_sources": research_results.get("raw_sources", []),
                "iteration": state.get("iteration", 0) + 1,
            }

        except Exception as e:
            logger.error(f"Research node failed: {e}")
            return {
                "errors": [f"Research failed: {str(e)}"],
                "current_agent": "research",
            }

    async def _analysis_node(self, state: IntelligenceState) -> dict:
        """Analysis agent node."""
        logger.info(f"Analysis node: {state['company_name']}")

        try:
            # Check budget before expensive analysis
            self.cost_tracker.check_budget(self.max_budget)

            # Run analysis agent
            analysis_results = await self.analysis_agent.run(
                research_data=state["research_data"]
            )

            # Update state
            return {
                "current_agent": "analysis",
                "swot": analysis_results.get("swot", {}),
                "competitive_matrix": analysis_results.get("competitive_matrix", {}),
                "positioning": analysis_results.get("positioning", {}),
                "strategic_recommendations": analysis_results.get(
                    "strategic_recommendations", {}
                ),
            }

        except BudgetExceededError as e:
            logger.error(f"Budget exceeded: {e}")
            return {
                "errors": [f"Budget exceeded: {str(e)}"],
                "current_agent": "analysis",
            }
        except Exception as e:
            logger.error(f"Analysis node failed: {e}")
            return {
                "errors": [f"Analysis failed: {str(e)}"],
                "current_agent": "analysis",
            }

    async def _writing_node(self, state: IntelligenceState) -> dict:
        """Writer agent node."""
        logger.info(f"Writing node: {state['company_name']}")

        try:
            # Run writer agent
            report_results = await self.writer_agent.run(
                research_data=state["research_data"],
                analysis_data={
                    "swot": state.get("swot", {}),
                    "competitive_matrix": state.get("competitive_matrix", {}),
                    "positioning": state.get("positioning", {}),
                    "strategic_recommendations": state.get(
                        "strategic_recommendations", {}
                    ),
                },
            )

            # Get cost summary
            cost_summary = self.cost_tracker.get_summary()

            # Update state
            return {
                "current_agent": "writing",
                "executive_summary": report_results.get("executive_summary", ""),
                "full_report": report_results.get("full_report", ""),
                "report_metadata": report_results.get("metadata", {}),
                "total_cost": cost_summary["total_cost"],
                "total_tokens": cost_summary["total_tokens"],
            }

        except Exception as e:
            logger.error(f"Writing node failed: {e}")
            return {
                "errors": [f"Writing failed: {str(e)}"],
                "current_agent": "writing",
            }

    async def _human_review_node(self, state: IntelligenceState) -> dict:
        """Human review node (placeholder for now)."""
        logger.info(f"Human review node: {state['company_name']}")

        # For now, auto-approve
        # In Phase 5, this will connect to the Gradio UI
        return {
            "current_agent": "human_review",
            "approved": True,  # Auto-approve for testing
            "human_feedback": None,
        }

    def _should_continue_to_analysis(self, state: IntelligenceState) -> str:
        """Decide whether to continue to analysis or end."""
        # Check if research was successful
        if state.get("errors") and state["errors"]:
            logger.warning("Research had errors, ending workflow")
            return "end"

        if not state.get("research_data"):
            logger.warning("No research data, ending workflow")
            return "end"

        return "analysis"

    def _check_approval(self, state: IntelligenceState) -> str:
        """Check if report is approved or needs revision."""
        # Check max revisions
        revision_count = state.get("revision_count", 0)
        if revision_count >= 2:
            logger.warning("Max revisions reached")
            return "max_revisions"

        # Check approval
        if state.get("approved"):
            return "approved"

        # Revision requested
        if state.get("human_feedback"):
            return "revise"

        # Default to approved
        return "approved"

    async def run(
        self,
        company_name: str,
        industry: str | None = None,
        thread_id: str | None = None,
    ) -> dict:
        """
        Run the complete workflow.

        Args:
            company_name: Target company name
            industry: Optional industry context
            thread_id: Optional thread ID for checkpointing

        Returns:
            Final state dictionary
        """
        logger.info(f"Starting workflow for: {company_name}")

        # Initial state
        initial_state = {
            "company_name": company_name,
            "industry": industry,
            "research_data": {},
            "competitors": [],
            "market_trends": {},
            "raw_sources": [],
            "swot": {},
            "competitive_matrix": {},
            "positioning": {},
            "strategic_recommendations": {},
            "executive_summary": "",
            "full_report": "",
            "report_metadata": {},
            "current_agent": "research",
            "iteration": 0,
            "total_cost": 0.0,
            "total_tokens": 0,
            "errors": [],
            "human_feedback": None,
            "approved": False,
            "revision_count": 0,
        }

        # Run workflow
        config = {"configurable": {"thread_id": thread_id or "default"}}

        try:
            final_state = await self.workflow.ainvoke(initial_state, config)
            logger.info(f"Workflow complete. Cost: ${final_state['total_cost']:.4f}")
            return final_state

        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            raise
