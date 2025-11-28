# LangGraph Workflow Architecture

Technical documentation for the multi-agent orchestration system.

## System Architecture

```
User Input → Research Agent → Analysis Agent → Writer Agent → Report
                ↓                ↓                ↓
            Tavily API       SWOT/Matrix      Markdown
```

**State Flow:** LangGraph StateGraph manages shared state across agents with SQLite checkpointing for crash recovery.

## Agent Responsibilities

| Agent | Input | Output | External Calls |
|-------|-------|--------|----------------|
| Research | Company name, industry | Competitors, market data, sources | Tavily API (3 queries) |
| Analysis | Research data | SWOT, competitive matrix, recommendations | LLM (4-6 calls) |
| Writer | Research + Analysis | Executive summary, full report | LLM (2-3 calls) |

## Conditional Routing

**Research → Analysis:**
- If errors or no data: END
- Else: Continue to Analysis

**Human Review → END/Revision:**
- If approved: END
- If max revisions (2): END
- If feedback provided: Loop to Research

## State Schema

```python
IntelligenceState = {
    "company_name": str,
    "industry": str | None,
    "research_data": dict,
    "swot": dict,
    "full_report": str,
    "current_agent": str,
    "total_cost": float,
    "approved": bool,
    "errors": list,
    # ... 15 more fields
}
```

Full schema: `src/workflows/state.py`

## Cost Management

Budget enforcement at 3 points:
1. Before Analysis node (most expensive)
2. After each LLM call via CostTracker
3. Workflow raises `BudgetExceededError` if exceeded

Default: $2.00 per run

## Checkpointing

SQLite checkpoints (`./checkpoints.db`) enable:
- Resume after crashes
- Audit trail for compliance
- Debug state at each step

```python
# Resume from checkpoint
workflow = MarketIntelligenceWorkflow()
result = await workflow.run(
    company_name="Tesla",
    thread_id="tesla-analysis-1"  # Same ID = resume
)
```

## Error Handling

Errors accumulate in `state["errors"]`:
- Research failure → Workflow stops
- Analysis error → Logged, may continue
- Budget exceeded → Immediate stop

## Usage

**Basic:**
```python
from src.workflows.intelligence import MarketIntelligenceWorkflow

workflow = MarketIntelligenceWorkflow()
result = await workflow.run(
    company_name="Tesla Model Y",
    industry="Electric Vehicles"
)
```

**Custom Budget:**
```python
workflow = MarketIntelligenceWorkflow(max_budget=5.0)
```

## Performance Metrics

Typical execution:
- **Time:** 3-5 minutes
- **Cost:** $0 (free) to $1.50 (Claude)
- **API Calls:** 9-14 total (3 search + 6-11 LLM)
- **Tokens:** 50K-100K

## Configuration

Environment variables (`.env`):
```bash
DEFAULT_MODEL=x-ai/grok-4.1-fast:free
MAX_COST_PER_RUN=2.0
LANGCHAIN_TRACING_V2=true
```

## Observability

LangSmith integration provides:
- Full execution traces
- Agent decision debugging
- Cost tracking per call
- Performance bottleneck identification

Enable: Set `LANGCHAIN_TRACING_V2=true` in `.env`

Dashboard: https://smith.langchain.com

## Testing

```bash
pytest tests/unit/test_workflow.py -v        # 11 workflow tests
pytest tests/integration/ -v                  # Integration tests
python scripts/test_workflow.py              # E2E with real APIs
```

## Extending the Workflow

**Add New Agent:**

1. Create agent in `src/agents/new_agent.py`
2. Add node wrapper:
```python
async def _new_agent_node(self, state):
    result = await self.new_agent.run(state["research_data"])
    return {"new_field": result}
```
3. Wire into graph:
```python
graph.add_node("new_agent", self._new_agent_node)
graph.add_edge("analysis", "new_agent")
```

**Modify Routing:**
```python
def _custom_routing(self, state):
    if state["company_name"].startswith("Enterprise"):
        return "deep_analysis"
    return "standard_analysis"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Workflow stops early | Check `result["errors"]`, verify API keys |
| Budget exceeded | Increase `max_budget` or use cheaper model |
| Slow performance | Check LangSmith traces, consider caching |
| Checkpoint errors | Delete `checkpoints.db`, check permissions |

## Production Checklist

- [x] Cost tracking and budget enforcement
- [x] State persistence with checkpoints
- [x] Error recovery and graceful degradation
- [x] Observability integration
- [ ] Human-in-the-loop UI integration (Phase 5)
- [ ] Rate limiting for API calls
- [ ] Result caching for repeated queries
