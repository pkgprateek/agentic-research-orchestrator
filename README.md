# Agentic Market Research

Multi-agent AI system that automates competitive market intelligence. 80x faster than manual research, 1500x cheaper.

**[Live Demo →](https://huggingface.co/spaces/pkgprateek/agentic-market-research)**

## The Problem

Competitive market research costs $3,000 and takes 20 hours per analysis. Businesses need faster, cheaper intelligence.

## The Solution

Automated multi-agent system delivers comprehensive market intelligence in 15 minutes for $0.50-$2.

**Architecture:**

```mermaid
graph LR
    Input Task --> Research[Research Agent]
    Research --> Analysis[Analysis Agent]
    Analysis --> Writer[Writer Agent]
    Writer --> Report[Intelligence Report]
    
    Research -.-> Tavily[Tavily Search]
    Analysis -.-> LLM[Claude/GPT/Gemini]
    Writer -.-> LLM
    
    style Research fill:#7ed321
    style Analysis fill:#f5a623
    style Writer fill:#bd10e0
```

**Agents:**
- **Research**: Web search + data gathering (Tavily API)
- **Analysis**: SWOT analysis + competitive positioning
- **Writer**: Professional markdown reports with citations

**Stack:** LangGraph | OpenRouter | FastAPI | Gradio | Docker

## Quick Start

```bash
git clone https://github.com/pkgprateek/agentic-market-research.git
cd agentic-market-research

# Install
python -m venv venv && source venv/bin/activate
pip install uv && uv pip install -r requirements.txt

# Configure
cp .env.example .env
# Add OPENROUTER_API_KEY and TAVILY_API_KEY

# Run
python src/ui/app.py
# Open http://localhost:7860
```

## Key Features

| Feature | Implementation | Business Value |
|---------|---------------|----------------|
| Multi-agent orchestration | LangGraph state machine | Reliable, reproducible results |
| Cost tracking | Real-time budget enforcement | Prevent runaway costs |
| State persistence | SQLite checkpoints | Resume after failures |
| Human-in-the-loop | Approval workflow | Quality control gate |
| Observability | LangSmith integration | Debug production issues |

## Economics

| Approach | Time | Cost | Result |
|----------|------|------|--------|
| Manual analyst | 20 hours | $3,000 | Variable quality |
| This system | 15 minutes | $0.50-$2 | Consistent reports |
| **Improvement** | **80x** | **1500-6000x** | **Standardized** |

## Model Options

Configure via `.env`:

```bash
# Free (testing)
DEFAULT_MODEL=x-ai/grok-4.1-fast:free

# Production (best quality)
DEFAULT_MODEL=anthropic/claude-sonnet-4.5
```

Supports 400+ models via OpenRouter.

## API

```python
from src.workflows.intelligence import MarketIntelligenceWorkflow

workflow = MarketIntelligenceWorkflow()
result = await workflow.run(
    company_name="Tesla Model Y",
    industry="Electric Vehicles"
)
print(result["full_report"])
```

REST API at `http://localhost:8000/docs` when running `uvicorn src.api.main:app`

## Testing

```bash
pytest tests/unit/ -v        # 18 tests
pytest tests/integration/ -v # Integration tests
```

## Deployment

**Production:** [HuggingFace Spaces](https://huggingface.co/spaces/pkgprateek/agentic-market-research) (auto-deploys via GitHub Actions)

**Local:** `docker-compose up`

## Technical Highlights

**For Hiring Managers:**
- Production-grade error handling and state management
- Automated CI/CD pipeline (GitHub Actions → HF Spaces)
- Cost optimization ($0-$2 vs $3,000 manual research)
- Real-world business value (80x time savings)

**For Technical Teams:**
- LangGraph 1.0.4 for multi-agent coordination
- AsyncSqliteSaver for checkpoint persistence
- OpenRouter for cost-optimized LLM routing
- Comprehensive testing (unit + integration)
- FastAPI async background tasks

## Project Structure

```
agentic-market-research/
├── src/
│   ├── agents/       # Research, Analysis, Writer
│   ├── workflows/    # LangGraph orchestration
│   ├── api/          # FastAPI endpoints
│   └── ui/           # Gradio interface
├── tests/
│   ├── unit/         # 18 passing tests
│   └── integration/  # Workflow integration tests
└── docs/             # Technical documentation
```

## Documentation

- [Workflow Architecture](docs/WORKFLOW.md) - Implementation details
- [API Docs](http://localhost:8000/docs) - Interactive API reference

## License

MIT

---

**Built by Prateek Kumar Goel** | [GitHub](https://github.com/pkgprateek/agentic-market-research) | [Live Demo](https://huggingface.co/spaces/pkgprateek/agentic-market-research)
