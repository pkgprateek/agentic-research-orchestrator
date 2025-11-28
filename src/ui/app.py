"""Gradio UI for Market Intelligence System."""

import gradio as gr
import asyncio
import logging
import queue
import tempfile

from datetime import datetime

from src.workflows.market_analysis import MarketIntelligenceWorkflow
from src.utils.logging import setup_logger

logger = setup_logger(__name__)


class QueueHandler(logging.Handler):
    """Custom handler to send logs to a queue."""

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        try:
            # Strip src. prefix for cleaner logs
            if record.name.startswith("src."):
                record.name = record.name[4:]
            msg = self.format(record)
            self.log_queue.put(msg)
        except Exception:
            self.handleError(record)


def create_ui():
    """Create and configure Gradio interface."""

    # Shared state for workflow
    # current_workflow = None

    def validate_model_selection(model_name):
        """Validate model selection and revert if unavailable."""
        if "Temporarily Unavailable" in model_name:
            gr.Warning(
                "This model request limit for today is reached so it is temporarily unavailable. Please try another model."
            )
            return "Grok 4.1 Fast (Free)"
        return model_name

    async def run_analysis(
        company_name: str,
        industry: str,
        model_choice: str,
        max_budget: float,
        research_depth: str,
    ):
        """Run market intelligence analysis with live logging."""
        if not company_name:
            yield ("Please enter a company name", "", 0.0, "Not started", "")
            return

        # Model mapping
        model_map = {
            "Grok 4.1 Fast (Free)": "x-ai/grok-4.1-fast:free",
            "GPT-5 Mini (Cheap)": "openai/gpt-5-mini",
            "Claude Sonnet 4.5 (Best) - Temporarily Unavailable": "anthropic/claude-sonnet-4.5",
            "Gemini 2.5 Flash Lite (Fast)": "google/gemini-2.5-flash-lite",
        }

        # Setup logging
        log_queue: queue.Queue = queue.Queue()
        queue_handler = QueueHandler(log_queue)
        queue_handler.setFormatter(
            logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        )

        # Attach to root logger or specific modules
        root_logger = logging.getLogger()
        root_logger.addHandler(queue_handler)

        # Dynamically attach to all existing src loggers because they have propagate=False
        for name, logger_obj in logging.Logger.manager.loggerDict.items():
            if name.startswith("src") and isinstance(logger_obj, logging.Logger):
                logger_obj.addHandler(queue_handler)

        model = model_map.get(model_choice, "x-ai/grok-4.1-fast:free")

        logs = []
        activity_text = ""

        try:
            # Create workflow
            workflow = MarketIntelligenceWorkflow(
                max_budget=max_budget, model_name=model
            )

            # Create task for workflow execution
            task = asyncio.create_task(
                workflow.run(
                    company_name=company_name,
                    industry=industry if industry else None,
                    thread_id=f"ui-{datetime.now().timestamp()}",
                    research_depth=research_depth,
                )
            )

            # Loop while task is running to stream logs
            while not task.done():
                # Check for new logs
                while not log_queue.empty():
                    try:
                        log_entry = log_queue.get_nowait()
                        logs.append(log_entry)
                        activity_text = "\n".join(logs)
                    except queue.Empty:
                        break

                # Yield current state (logs only, other fields empty/default)
                yield (
                    activity_text,
                    "Analysis in progress...",
                    0.0,
                    "🔄 Running...",
                    "Generating summary...",
                )

                await asyncio.sleep(0.1)

            # Get final result
            result = await task

            # Flush remaining logs
            while not log_queue.empty():
                try:
                    log_entry = log_queue.get_nowait()
                    logs.append(log_entry)
                except queue.Empty:
                    break

            activity_text = "\n".join(logs)

            # Format final output
            final_status = (
                f"✅ Complete - ${result['total_cost']:.4f}"
                if not result.get("errors")
                else "❌ Failed"
            )

            yield (
                activity_text,
                result.get("full_report", "No report generated"),
                result.get("total_cost", 0.0),
                final_status,
                result.get("executive_summary", ""),
            )

        except Exception as e:
            logger.error(f"UI analysis failed: {e}")
            yield (f"Error: {str(e)}", "", 0.0, f"❌ Failed: {str(e)}", "")

        finally:
            # Cleanup handlers
            root_logger.removeHandler(queue_handler)
            for name, logger_obj in logging.Logger.manager.loggerDict.items():
                if name.startswith("src") and isinstance(logger_obj, logging.Logger):
                    logger_obj.removeHandler(queue_handler)

    # Build UI
    with gr.Blocks(title="Agentic Market Research Orchestrator") as demo:
        gr.Markdown("""
        # 🚀 Agentic Market Research Orchestrator
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

                research_depth = gr.Radio(
                    choices=["Basic", "Comprehensive"],
                    value="Comprehensive",
                    label="Research Depth",
                    info="Basic: Faster, less detail. Comprehensive: Deeper, more sources.",
                )

                with gr.Accordion("⚙️ Advanced Settings", open=False):
                    model_choice = gr.Dropdown(
                        choices=[
                            "Grok 4.1 Fast (Free)",
                            "GPT-5 Mini (Cheap)",
                            "Claude Sonnet 4.5 (Best) - Temporarily Unavailable",
                            "Gemini 2.5 Flash Lite (Fast)",
                        ],
                        value="Grok 4.1 Fast (Free)",
                        label="AI Model",
                        info="Free models for testing, paid for production",
                    )

                    budget_slider = gr.Slider(
                        minimum=0.1,
                        maximum=2.0,
                        value=0.5,
                        step=0.1,
                        label="Max Budget (USD)",
                        info="Strict limit: $2.00 max",
                    )

                run_btn = gr.Button("🚀 Run Analysis", variant="primary", size="lg")
                clear_btn = gr.Button("🗑️ Clear Inputs", variant="secondary")

                gr.Markdown("### 💰 Cost Tracker")
                cost_display = gr.Number(
                    label="Current Run Cost ($)", value=0, precision=4
                )
                budget_status = gr.Textbox(
                    label="Status", value="Ready", interactive=False
                )

            # Right column - Outputs
            with gr.Column(scale=2):
                with gr.Tabs():
                    with gr.TabItem("🤖 Activity Log"):
                        activity_log = gr.Textbox(
                            label="Live Activity Log",
                            lines=20,
                            max_lines=30,
                            interactive=False,
                            show_label=False,
                            autoscroll=True,
                        )

                    with gr.TabItem("📋 Executive Summary"):
                        exec_summary = gr.Textbox(
                            label="Executive Summary",
                            lines=30,
                            max_lines=50,
                            interactive=False,
                            show_label=False,
                        )

                    with gr.TabItem("📊 Full Report"):
                        report_display = gr.Markdown()

                    with gr.TabItem("📥 Download"):
                        gr.Markdown("### Download Full Report")
                        download_btn = gr.DownloadButton("Download Report (Markdown)")

        # Event handlers
        model_choice.change(
            fn=validate_model_selection,
            inputs=[model_choice],
            outputs=[model_choice],
        )

        def clear_inputs():
            return "", "", "Comprehensive", "Grok 4.1 Fast (Free)", 0.5

        clear_btn.click(
            fn=clear_inputs,
            outputs=[
                company_input,
                industry_input,
                research_depth,
                model_choice,
                budget_slider,
            ],
        )

        run_btn.click(
            fn=run_analysis,
            inputs=[
                company_input,
                industry_input,
                model_choice,
                budget_slider,
                research_depth,
            ],
            outputs=[
                activity_log,
                report_display,
                cost_display,
                budget_status,
                exec_summary,
            ],
        )

        def download_report(report_content):
            if not report_content:
                return None

            # Create a temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".md", encoding="utf-8"
            ) as temp:
                temp.write(report_content)
                temp_path = temp.name

            return temp_path

        download_btn.click(
            fn=download_report,
            inputs=[report_display],
            outputs=[download_btn],
        )

        gr.HTML("""
        <div style="text-align: center; margin-top: 2rem; padding: 1rem; border-top: 1px solid #eee; color: #666;">
            <p><strong>Agentic Market Research Orchestrator</strong></p>
            <p>Powered by LangGraph • OpenRouter • Tavily Search</p>
        </div>
        """)

    return demo


if __name__ == "__main__":
    app = create_ui()
    app.launch(server_name="0.0.0.0", server_port=7860, share=False, show_error=True)
