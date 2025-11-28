"""Gradio UI for Market Intelligence System."""

import gradio as gr
import asyncio
from datetime import datetime

from src.workflows.intelligence import MarketIntelligenceWorkflow
from src.utils.logging import setup_logger

logger = setup_logger(__name__)


def create_ui():
    """Create and configure Gradio interface."""

    # Shared state for workflow
    current_workflow = None

    async def run_analysis(
        company_name: str,
        industry: str,
        model_choice: str,
        max_budget: float,
    ):
        """Run market intelligence analysis."""
        if not company_name:
            return ("Please enter a company name", "", 0.0, "Not started", "")

        # Model mapping
        model_map = {
            "Grok 4.1 Fast (Free)": "x-ai/grok-4.1-fast:free",
            "GPT-5 Mini (Cheap)": "openai/gpt-5-mini",
            "Claude Sonnet 4.5 (Best)": "anthropic/claude-sonnet-4.5",
            "Gemini 2.5 Flash Lite (Fast)": "google/gemini-2.5-flash-lite",
        }

        model = model_map.get(model_choice, "x-ai/grok-4.1-fast:free")

        try:
            # Create workflow
            workflow = MarketIntelligenceWorkflow(max_budget=max_budget)

            # Run analysis
            activity_log = f"Starting analysis for {company_name}..."

            result = await workflow.run(
                company_name=company_name,
                industry=industry if industry else None,
                thread_id=f"ui-{datetime.now().timestamp()}",
            )

            # Format activity log
            activity = f"""Analysis Complete!

Company: {result["company_name"]}
Sources: {len(result.get("raw_sources", []))}
Cost: ${result["total_cost"]:.4f}
Tokens: {result["total_tokens"]:,}
Status: {"✅ Approved" if result.get("approved") else "❌ Not Approved"}
"""

            # Return results
            return (
                activity,
                result.get("full_report", "No report generated"),
                result.get("total_cost", 0.0),
                f"✅ Complete - ${result['total_cost']:.4f}"
                if not result.get("errors")
                else "❌ Failed",
                result.get("executive_summary", ""),
            )

        except Exception as e:
            logger.error(f"UI analysis failed: {e}")
            return (f"Error: {str(e)}", "", 0.0, f"❌ Failed: {str(e)}", "")

    # Build UI
    with gr.Blocks(
        theme=gr.themes.Soft(),
        title="Market Intelligence Agent",
        css="""
        .gradio-container {
            max-width: 1400px !important;
        }
        """,
    ) as demo:
        gr.Markdown("""
        # AI Market Intelligence Agent
        ### Competitive intelligence in 15 minutes, powered by LangGraph
        """)

        with gr.Row():
            # Left column - Inputs
            with gr.Column(scale=1):
                gr.Markdown("### 📝 Analysis Configuration")

                company_input = gr.Textbox(
                    label="Company/Product Name",
                    placeholder="e.g., Tesla Model Y, Notion, ChatGPT",
                    info="The company or product to analyze",
                )

                industry_input = gr.Textbox(
                    label="Industry (optional)",
                    placeholder="e.g., Electric Vehicles, Productivity Software",
                    info="Helps contextualize the analysis",
                )

                model_choice = gr.Dropdown(
                    choices=[
                        "Grok 4.1 Fast (Free)",
                        "GPT-5 Mini (Cheap)",
                        "Claude Sonnet 4.5 (Best)",
                        "Gemini 2.5 Flash Lite (Fast)",
                    ],
                    value="Grok 4.1 Fast (Free)",
                    label="AI Model",
                    info="Free models for testing, paid for production",
                )

                budget_slider = gr.Slider(
                    minimum=0.5,
                    maximum=5.0,
                    value=2.0,
                    step=0.5,
                    label="Max Budget (USD)",
                    info="Maximum cost limit",
                )

                run_btn = gr.Button("🚀 Run Analysis", variant="primary", size="lg")

                gr.Markdown("### 💰 Cost Tracker")

                cost_display = gr.Number(
                    label="Current Run Cost ($)", value=0, precision=4
                )

                budget_status = gr.Textbox(
                    label="Status", value="Ready", interactive=False
                )

                gr.Markdown("""
                ---
                **Note:** Free tier models (Grok) cost $0.00.
                Paid models range from $0.10-$1.50 per analysis.
                """)

            # Right column - Outputs
            with gr.Column(scale=2):
                gr.Markdown("### 🤖 Agent Activity")

                activity_log = gr.Textbox(
                    label="Live Activity Log",
                    lines=6,
                    max_lines=10,
                    interactive=False,
                    show_copy_button=True,
                )

                gr.Markdown("### 📋 Executive Summary")

                exec_summary = gr.Textbox(
                    label="Executive Summary",
                    lines=8,
                    max_lines=15,
                    interactive=False,
                    show_copy_button=True,
                )

                gr.Markdown("### 📊 Full Intelligence Report")

                report_display = gr.Markdown()

                with gr.Row():
                    download_md_btn = gr.Button("📄 Download Markdown")
                    download_txt_btn = gr.Button("📝 Download Text")

        # Event handlers
        run_btn.click(
            fn=run_analysis,
            inputs=[company_input, industry_input, model_choice, budget_slider],
            outputs=[
                activity_log,
                report_display,
                cost_display,
                budget_status,
                exec_summary,
            ],
        )

        # Download handlers would save the report_display content
        # Simplified for now

        gr.Markdown("""
        ---
        ### 🎯 How It Works
        1. Enter a company/product name
        2. Optionally specify industry for context
        3. Choose your AI model (free or paid)
        4. Click "Run Analysis"
        5. Wait 3-5 minutes for complete report
        
        ### 🔍 What You Get
        - Company overview with key facts
        - Competitor landscape analysis
        - SWOT analysis (Strengths, Weaknesses, Opportunities, Threats)
        - Competitive positioning matrix
        - Market trends and insights
        - Strategic recommendations
        
        **Powered by:** LangGraph, OpenRouter, Tavily Search
        """)

    return demo


if __name__ == "__main__":
    app = create_ui()
    app.launch(server_name="0.0.0.0", server_port=7860, share=False, show_error=True)
