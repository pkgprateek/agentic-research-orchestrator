"""
Test script to run agents manually on a real query.

This demonstrates the agent pipeline without LangGraph orchestration.
"""

import asyncio
import sys

from src.agents.researcher import ResearchAgent
from src.agents.analyst import AnalysisAgent
from src.agents.writer import WriterAgent
from src.utils.cost_tracker import CostTracker


async def test_complete_pipeline():
    """Test the complete agent pipeline."""

    # Query from user
    query = "going viral on Instagram using AI without showing face"
    industry = "Social Media Marketing"

    print("=" * 80)
    print(f"TESTING AGENT PIPELINE")
    print(f"Query: {query}")
    print(f"Industry: {industry}")
    print("=" * 80)
    print()

    # Shared cost tracker
    cost_tracker = CostTracker()

    try:
        # Step 1: Research Agent
        print("\n[STEP 1] Running Research Agent...")
        print("-" * 80)
        researcher = ResearchAgent(cost_tracker=cost_tracker)

        research_results = await researcher.run(
            company_name=query, industry=industry, research_depth="comprehensive"
        )

        print(f"\nResearch completed!")
        print(f"Sources gathered: {len(research_results.get('raw_sources', []))}")
        print(f"\nCompany Overview (first 500 chars):")
        print(research_results["company_overview"][:500] + "...")

        # Step 2: Analysis Agent
        print("\n\n[STEP 2] Running Analysis Agent...")
        print("-" * 80)
        analyst = AnalysisAgent(cost_tracker=cost_tracker)

        analysis_results = await analyst.run(research_data=research_results)

        print(f"\nAnalysis completed!")
        print(f"\nSWOT Analysis (first 500 chars):")
        print(analysis_results["swot"][:500] + "...")

        # Step 3: Writer Agent
        print("\n\n[STEP 3] Running Writer Agent...")
        print("-" * 80)
        writer = WriterAgent(cost_tracker=cost_tracker)

        report_results = await writer.run(
            research_data=research_results, analysis_data=analysis_results
        )

        print(f"\nReport generation completed!")

        # Display results
        print("\n\n" + "=" * 80)
        print("EXECUTIVE SUMMARY")
        print("=" * 80)
        print(report_results["executive_summary"])

        print("\n\n" + "=" * 80)
        print("FULL REPORT")
        print("=" * 80)
        print(report_results["full_report"])

        # Cost summary
        print("\n\n" + "=" * 80)
        print("COST SUMMARY")
        print("=" * 80)
        summary = cost_tracker.get_summary()
        print(f"Total Cost: ${summary['total_cost']:.4f}")
        print(f"Total Tokens: {summary['total_tokens']:,}")
        print(f"API Calls: {summary['calls']}")
        print(f"\nBreakdown by model:")
        for model, data in summary["by_model"].items():
            print(f"  {model}:")
            print(f"    Input: {data['input_tokens']:,} tokens")
            print(f"    Output: {data['output_tokens']:,} tokens")
            print(f"    Cost: ${data['cost']:.4f}")

        # Save report
        output_file = "test_report.md"
        with open(output_file, "w") as f:
            f.write(f"# Market Intelligence Report\n\n")
            f.write(f"**Query:** {query}\n\n")
            f.write(f"**Industry:** {industry}\n\n")
            f.write(f"---\n\n")
            f.write(f"## Executive Summary\n\n")
            f.write(report_results["executive_summary"])
            f.write(f"\n\n---\n\n")
            f.write(report_results["full_report"])
            f.write(f"\n\n---\n\n")
            f.write(f"**Total Cost:** ${summary['total_cost']:.4f}\n")

        print(f"\n\nReport saved to: {output_file}")

        return True

    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\nStarting agent test...")
    print("Make sure you have .env file with API keys set up!\n")

    result = asyncio.run(test_complete_pipeline())

    if result:
        print("\n\nTest PASSED!")
        sys.exit(0)
    else:
        print("\n\nTest FAILED!")
        sys.exit(1)
