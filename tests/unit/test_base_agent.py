"""Unit tests for base agent class."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.base import BaseAgent
from src.utils.cost_tracker import CostTracker


class TestAgent(BaseAgent):
    """Concrete test agent for testing base class."""

    def get_system_prompt(self) -> str:
        return "Test system prompt"

    async def run(self, **kwargs):
        return {"result": "test"}


@pytest.mark.asyncio
async def test_base_agent_initialization():
    """Test base agent initializes correctly."""
    tracker = CostTracker()

    with patch("src.agents.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            default_model="x-ai/grok-4.1-fast:free",
            openrouter_api_key="test-key",
            openrouter_base_url="https://openrouter.ai/api/v1",
        )

        agent = TestAgent(
            name="TestAgent",
            model="openai/gpt-5-mini",
            temperature=0.5,
            cost_tracker=tracker,
        )

        assert agent.name == "TestAgent"
        assert agent.model_name == "openai/gpt-5-mini"
        assert agent.cost_tracker == tracker


@pytest.mark.asyncio
async def test_base_agent_uses_default_model():
    """Test agent uses default model from config."""
    with patch("src.agents.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            default_model="x-ai/grok-4.1-fast:free",
            openrouter_api_key="test-key",
            openrouter_base_url="https://openrouter.ai/api/v1",
        )

        agent = TestAgent(name="TestAgent")

        assert agent.model_name == "x-ai/grok-4.1-fast:free"


@pytest.mark.asyncio
async def test_create_messages():
    """Test message creation."""
    with patch("src.agents.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            default_model="test-model",
            openrouter_api_key="test-key",
            openrouter_base_url="https://test.com",
        )

        agent = TestAgent(name="TestAgent")

        messages = agent._create_messages("test user message")

        assert len(messages) == 2
        assert messages[0].content == "Test system prompt"
        assert messages[1].content == "test user message"


@pytest.mark.asyncio
async def test_get_cost_summary():
    """Test cost summary retrieval."""
    tracker = CostTracker()

    with patch("src.agents.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            default_model="test-model",
            openrouter_api_key="test-key",
            openrouter_base_url="https://test.com",
        )

        agent = TestAgent(name="TestAgent", cost_tracker=tracker)

        # Track some usage
        tracker.track_usage("openai/gpt-5-mini", 1000, 500)

        summary = agent.get_cost_summary()

        assert summary["total_input_tokens"] == 1000
        assert summary["total_output_tokens"] == 500
        assert summary["calls"] == 1
