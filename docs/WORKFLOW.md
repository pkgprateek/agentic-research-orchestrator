# LangGraph Workflow Documentation

## Overview

The Market Intelligence workflow orchestrates three specialized agents using LangGraph's StateGraph to generate comprehensive market analysis reports.

## Architecture

```
START → Research → Analysis → Writing → Human Review → END
          ↓          ↓          ↓
       Tavily    SWOT/Matrix  Report
```

### State Management

The workflow maintains a shared state (`IntelligenceState`) that flows between agents:

```python
{
    "company_name": str,
    "industry": str | None,
    "research_data": dict,      # From Research Agent
    "swot": dict,                # From Analysis Agent  
    "full_report": str,          # From Writer Agent
    "total_cost": float,         # Cost tracking
    "approved": bool,            # Human approval
    # ... additional fields
}
```

## Workflow Nodes

### 1. Research Node
- **Input**: Company name, industry
- **Process**: Tavily search queries (company info, competitors, trends)
- **Output**: Research data, competitors list, market trends
- **Errors**: Network failures, API limits

### 2. Analysis Node
- **Input**: Research data
- **Process**: LLM-powered SWOT, competitive positioning
- **Output**: Structured analysis (SWOT, matrix, recommendations)
- **Budget Check**: Enforces max cost before expensive analysis

### 3. Writing Node
- **Input**: Research + Analysis data
- **Process**: Generate executive summary and full markdown report
- **Output**: Professional business intelligence report

### 4. Human Review Node
- **Input**: Generated report
- **Process**: Approval gate (currently auto-approves)
- **Output**: Approval decision or revision request

## Conditional Routing

### Research → Analysis
```python
if errors or no_data:
    END  # Stop workflow
else:
    CONTINUE to Analysis
```

### Human Review → END/Revision
```python
if approved:
    END  # Complete
elif max_revisions_reached:
    END  # Give up
else:
    REVISE  # Loop back to Research
```

## Cost Management

Budget is enforced at multiple points:
- Before Analysis Node (most expensive)
- After each LLM call via CostTracker
- Workflow fails with BudgetExceededError if limit hit

Default: $2.00 per run

## Checkpointing

SQLite checkpoints enable:
- **Resume**: Continue after crashes
- **Audit**: Full execution history
- **Debug**: Inspect state at each step

Checkpoint file: `./checkpoints.db`

## Error Handling

Errors accumulate in `state["errors"]` list:
- Research failures → Workflow stops
- Analysis errors → Logged, workflow may continue
- Budget exceeded → Immediate stop

## Usage Examples

### Basic Usage

```python
from src.workflows.intelligence import MarketIntelligenceWorkflow

workflow = MarketIntelligenceWorkflow()

result = await workflow.run(
    company_name="Tesla Model Y",
    industry="Electric Vehicles"
)

print(result["full_report"])
print(f"Cost: ${result['total_cost']:.2f}")
```

### Custom Budget

```python
workflow = MarketIntelligenceWorkflow(max_budget=5.0)

result = await workflow.run(
    company_name="Notion",
    thread_id="notion-analysis-1"  # For checkpointing
)
```

### Resume from Checkpoint

```python
# If workflow crashed, resume using same thread_id
result = await workflow.run(
    company_name="Notion",
    thread_id="notion-analysis-1"  # Same ID resumes
)
```

## Performance

Typical execution:
- **Time**: 3-5 minutes  
- **Cost**: $0.00 (free Grok) to $1.50 (Claude 4.5)
- **API Calls**: 6-8 LLM calls, 3 search queries
- **Tokens**: 50K-100K total

## Configuration

Via `.env`:
```bash
DEFAULT_MODEL=x-ai/grok-4.1-fast:free  # Free tier
MAX_COST_PER_RUN=2.0
LANGCHAIN_TRACING_V2=true  # Enable LangSmith
```

## Observability

With LangSmith enabled:
- View full execution trace
- Debug agent decisions
- Optimize prompts
- Track costs per call

Dashboard: https://smith.langchain.com

## Production Considerations

1. **Checkpointing**: Essential for long-running workflows
2. **Cost Limits**: Prevent runaway LLM costs
3. **Error Recovery**: Graceful degradation
4. **Human Review**: Required for high-stakes decisions
5. **Observability**: Critical for debugging production issues

## Testing

```bash
# Unit tests
pytest tests/unit/test_workflow.py -v

# Integration tests  
pytest tests/integration/test_workflow_integration.py -v

# End-to-end (uses real APIs)
python scripts/test_workflow.py
```

## Extending

### Add New Agent Node

1. Create agent class in `src/agents/`
2. Add node wrapper in workflow:
   ```python
   async def _my_agent_node(self, state):
       result = await self.my_agent.run(state["research_data"])
       return {"my_output": result}
   ```
3. Add to graph:
   ```python
   graph.add_node("my_agent", self._my_agent_node)
   graph.add_edge("analysis", "my_agent")
   ```

### Modify Routing Logic

Update conditional functions:
```python
def _should_use_special_analysis(self, state):
    if state["company_name"].startswith("Enterprise"):
        return "deep_analysis"
    return "standard_analysis"
```

## Troubleshooting

**Workflow stops early**:  
- Check `result["errors"]` for failures  
- Verify API keys in `.env`

**Budget exceeded frequently**:  
- Increase `max_budget` parameter  
- Use cheaper models (grok-4.1-fast:free)

**Slow performance**:  
- Check LangSmith traces for bottlenecks  
- Consider caching search results

**Checkpoint errors**:  
- Delete `checkpoints.db` to reset  
- Check file permissions
