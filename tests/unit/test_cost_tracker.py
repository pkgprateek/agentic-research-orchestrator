"""Unit tests for cost tracking utility."""

import pytest

from src.utils.cost_tracker import CostTracker, TokenUsage, BudgetExceededError


def test_token_usage():
    """Test TokenUsage dataclass."""
    usage = TokenUsage(input_tokens=1000, output_tokens=500, model="test-model")

    assert usage.input_tokens == 1000
    assert usage.output_tokens == 500
    assert usage.total_tokens == 1500
    assert usage.model == "test-model"


def test_calculate_cost_claude():
    """Test cost calculation for Claude model."""
    tracker = CostTracker()

    # Claude Sonnet 4.5: $3/1M input, $15/1M output
    cost = tracker.calculate_cost(
        "anthropic/claude-sonnet-4.5", input_tokens=10_000, output_tokens=5_000
    )

    expected = (10_000 * 3.00 / 1_000_000) + (5_000 * 15.00 / 1_000_000)
    assert abs(cost - expected) < 0.0001


def test_calculate_cost_gpt5_mini():
    """Test cost calculation for GPT-5-mini."""
    tracker = CostTracker()

    # GPT-5-mini: $0.25/1M input, $2.00/1M output
    cost = tracker.calculate_cost(
        "openai/gpt-5-mini", input_tokens=100_000, output_tokens=50_000
    )

    expected = (100_000 * 0.25 / 1_000_000) + (50_000 * 2.00 / 1_000_000)
    assert abs(cost - expected) < 0.0001


def test_calculate_cost_ollama():
    """Test cost calculation for Ollama (should be free)."""
    tracker = CostTracker()

    cost = tracker.calculate_cost("ollama", input_tokens=100_000, output_tokens=50_000)

    assert cost == 0.0


def test_track_usage():
    """Test usage tracking updates total cost."""
    tracker = CostTracker()

    assert tracker.total_cost == 0.0
    assert len(tracker.usage_history) == 0

    # Track first usage
    cost1 = tracker.track_usage("openai/gpt-5-mini", 10_000, 5_000)
    assert tracker.total_cost == cost1
    assert len(tracker.usage_history) == 1

    # Track second usage
    cost2 = tracker.track_usage("anthropic/claude-sonnet-4.5", 20_000, 10_000)
    assert abs(tracker.total_cost - (cost1 + cost2)) < 0.0001
    assert len(tracker.usage_history) == 2


def test_budget_check_within_limit():
    """Test budget check passes when within limit."""
    tracker = CostTracker()
    tracker.track_usage("openai/gpt-5-mini", 10_000, 5_000)

    # Should not raise
    tracker.check_budget(max_budget=1.0)


def test_budget_check_exceeds_limit():
    """Test budget check raises exception when exceeded."""
    tracker = CostTracker()
    # Track expensive usage
    tracker.track_usage("anthropic/claude-3.5-sonnet", 100_000, 200_000)

    # Should raise BudgetExceededError
    with pytest.raises(BudgetExceededError, match="exceeds budget"):
        tracker.check_budget(max_budget=0.01)


def test_get_summary():
    """Test cost summary generation."""
    tracker = CostTracker()

    tracker.track_usage("openai/gpt-5-mini", 10_000, 5_000)
    tracker.track_usage("anthropic/claude-sonnet-4.5", 20_000, 10_000)
    tracker.track_usage("openai/gpt-5-mini", 5_000, 2_500)  # Same model again

    summary = tracker.get_summary()

    assert summary["calls"] == 3
    assert summary["total_input_tokens"] == 35_000
    assert summary["total_output_tokens"] == 17_500
    assert summary["total_tokens"] == 52_500
    assert "openai/gpt-5-mini" in summary["by_model"]
    assert "anthropic/claude-sonnet-4.5" in summary["by_model"]

    # Check model-specific costs
    gpt_mini = summary["by_model"]["openai/gpt-5-mini"]
    assert gpt_mini["input_tokens"] == 15_000  # 10k + 5k
    assert gpt_mini["output_tokens"] == 7_500  # 5k + 2.5k

    claude = summary["by_model"]["anthropic/claude-sonnet-4.5"]
    assert claude["input_tokens"] == 20_000
    assert claude["output_tokens"] == 10_000


def test_unknown_model_fallback():
    """Test unknown model falls back to GPT-5-mini pricing."""
    tracker = CostTracker()

    cost = tracker.calculate_cost("unknown/model", 10_000, 5_000)
    expected_cost = tracker.calculate_cost("openai/gpt-5-mini", 10_000, 5_000)

    assert abs(cost - expected_cost) < 0.0001
