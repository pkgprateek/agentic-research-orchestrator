"""Cost tracking utility for LLM API usage monitoring."""

from dataclasses import dataclass, field
from typing import ClassVar

from src.utils.logging import setup_logger

logger = setup_logger(__name__)


@dataclass
class TokenUsage:
    """Track token usage for an LLM call."""

    input_tokens: int
    output_tokens: int
    model: str

    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.input_tokens + self.output_tokens


@dataclass
class CostTracker:
    """
    Track costs for LLM API usage across different providers.

    Pricing updated: November 2025
    OpenRouter adds ~5% commission to provider pricing.
    """

    # Pricing per 1M tokens (input/output) - Verified by user (Nov 28, 2025)
    PRICING: ClassVar[dict[str, dict[str, float]]] = {
        # === FREE TIER (for testing) ===
        "x-ai/grok-4.1-fast:free": {"input": 0.0, "output": 0.0},
        "meta-llama/llama-3.3-70b-instruct:free": {"input": 0.0, "output": 0.0},
        "ollama": {"input": 0.0, "output": 0.0},  # Local
        # === CHEAP (testing/development) ===
        # OpenAI
        "openai/gpt-5-nano": {"input": 0.05 / 1_000_000, "output": 0.40 / 1_000_000},
        "openai/gpt-5-mini": {"input": 0.25 / 1_000_000, "output": 2.00 / 1_000_000},
        # === PRODUCTION ===
        # Google (enterprise credibility + advanced reasoning)
        "google/gemini-2.5-flash-lite": {
            "input": 0.10 / 1_000_000,
            "output": 0.40 / 1_000_000,
        },
        "google/gemini-3-pro-preview": {
            "input": 2.00 / 1_000_000,
            "output": 12.00 / 1_000_000,
        },
        # Anthropic (best for technical audiences - strong code/reasoning)
        "anthropic/claude-sonnet-4.5": {
            "input": 3.00 / 1_000_000,
            "output": 15.00 / 1_000_000,
        },
    }

    total_cost: float = field(default=0.0)
    usage_history: list[TokenUsage] = field(default_factory=list)

    def calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """
        Calculate cost for a single LLM call.

        Args:
            model: Model name (e.g., "anthropic/claude-3.5-sonnet")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        # Get pricing for model (fallback to GPT-5-mini if unknown)
        pricing = self.PRICING.get(model, self.PRICING["openai/gpt-5-mini"])

        cost = (input_tokens * pricing["input"]) + (output_tokens * pricing["output"])

        logger.debug(
            f"Cost calculated for {model}: ${cost:.4f} "
            f"(input: {input_tokens}, output: {output_tokens})"
        )

        return cost

    def track_usage(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Track LLM usage and update total cost.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost for this call (USD)
        """
        usage = TokenUsage(
            input_tokens=input_tokens, output_tokens=output_tokens, model=model
        )

        cost = self.calculate_cost(model, input_tokens, output_tokens)

        self.usage_history.append(usage)
        self.total_cost += cost

        logger.info(
            f"Usage tracked: {model} - ${cost:.4f} (total: ${self.total_cost:.4f})"
        )

        return cost

    def check_budget(self, max_budget: float) -> None:
        """
        Check if total cost exceeds budget and raise exception if so.

        Args:
            max_budget: Maximum allowed budget (USD)

        Raises:
            BudgetExceededError: If total cost exceeds budget
        """
        if self.total_cost > max_budget:
            raise BudgetExceededError(
                f"Cost ${self.total_cost:.2f} exceeds budget ${max_budget:.2f}"
            )

    def get_summary(self) -> dict:
        """
        Get summary of cost and usage.

        Returns:
            Dictionary with cost summary
        """
        total_input = sum(u.input_tokens for u in self.usage_history)
        total_output = sum(u.output_tokens for u in self.usage_history)

        # Group by model
        model_costs = {}
        for usage in self.usage_history:
            if usage.model not in model_costs:
                model_costs[usage.model] = {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0,
                }

            model_costs[usage.model]["input_tokens"] += usage.input_tokens
            model_costs[usage.model]["output_tokens"] += usage.output_tokens
            model_costs[usage.model]["cost"] += self.calculate_cost(
                usage.model, usage.input_tokens, usage.output_tokens
            )

        return {
            "total_cost": round(self.total_cost, 4),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "calls": len(self.usage_history),
            "by_model": model_costs,
        }


class BudgetExceededError(Exception):
    """Raised when API usage exceeds budget."""

    pass
