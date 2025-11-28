"""
Test the complete LangGraph workflow.

Replaces test_agents.py with proper workflow orchestration.
"""

import asyncio

from src.workflows.intelligence import MarketIntelligenceWorkflow


async def test_workflow():
    """Test complete workflow with LangGraph orchestration."""

    print("=" * 80)
    print("TESTING LANGGRAPH WORKFLOW")
    print("=" * 80)
    print()

    # Initialize workflow
    workflow = MarketIntelligenceWorkflow(
        checkpoint_path="./test_checkpoints.db", max_budget=2.0
    )

    # Run on Instagram viral query
    company_name = "going viral on Instagram using AI without showing face"
    industry = "Social Media Marketing"

    print(f"Query: {company_name}")
    print(f"Industry: {industry}")
    print()
    print("Running workflow...")
    print("-" * 80)

    try:
        final_state = await workflow.run(
            company_name=company_name, industry=industry, thread_id="test-run-1"
        )

        print("\nWorkflow Complete!")
        print("=" * 80)

        # Display results
        print(f"\nCompany: {final_state['company_name']}")
        print(f"Final Agent: {final_state['current_agent']}")
        print(f"Iterations: {final_state['iteration']}")
        print(f"Approved: {final_state['approved']}")
        print(f"Errors: {len(final_state['errors'])}")

        print(f"\nCost: ${final_state['total_cost']:.4f}")
        print(f"Tokens: {final_state['total_tokens']:,}")
        print(f"Sources: {len(final_state.get('raw_sources', []))}")

        print("\n" + "=" * 80)
        print("EXECUTIVE SUMMARY")
        print("=" * 80)
        print(final_state["executive_summary"])

        print("\n" + "=" * 80)
        print("FULL REPORT (first 1000 chars)")
        print("=" * 80)
        print(final_state["full_report"][:1000] + "...")

        # Save report
        with open("workflow_test_report.md", "w") as f:
            f.write(f"# Market Intelligence Report\n\n")
            f.write(f"Generated via LangGraph Workflow\n\n")
            f.write(f"---\n\n")
            f.write(final_state["full_report"])
            f.write(f"\n\n---\n\n")
            f.write(f"**Cost:** ${final_state['total_cost']:.4f}\n")
            f.write(f"**Tokens:** {final_state['total_tokens']:,}\n")

        print(f"\n\nReport saved to: workflow_test_report.md")
        print("\nTest PASSED!")

    except Exception as e:
        print(f"\nTest FAILED: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_workflow())
