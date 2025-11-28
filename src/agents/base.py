"""Base agent class for all agents in the system."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.utils.config import get_settings
from src.utils.cost_tracker import CostTracker
from src.utils.logging import setup_logger

logger = setup_logger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents in the multi-agent system.

    Provides common functionality for LLM interaction, cost tracking,
    and error handling.
    """

    def __init__(
        self,
        name: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        cost_tracker: Optional[CostTracker] = None,
    ):
        """
        Initialize base agent.

        Args:
            name: Agent name for logging
            model: LLM model to use (defaults to config default)
            temperature: LLM sampling temperature (0-1)
            cost_tracker: Optional cost tracker instance
        """
        self.name = name
        self.cost_tracker = cost_tracker or CostTracker()

        settings = get_settings()
        self.model_name = model or settings.default_model

        # Initialize LLM via OpenRouter
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=temperature,
            openai_api_key=settings.openrouter_api_key,
            openai_api_base=settings.openrouter_base_url,
        )

        logger.info(f"Initialized {name} with model {self.model_name}")

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.

        Returns:
            System prompt string
        """
        pass

    @abstractmethod
    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the agent's main task.

        Args:
            **kwargs: Agent-specific parameters

        Returns:
            Dictionary with results
        """
        pass

    async def _invoke_llm(
        self,
        messages: list[BaseMessage],
        **llm_kwargs,
    ) -> str:
        """
        Invoke LLM and track costs.

        Args:
            messages: List of messages to send
            **llm_kwargs: Additional LLM parameters

        Returns:
            LLM response text
        """
        try:
            response = await self.llm.ainvoke(messages, **llm_kwargs)

            # Track usage if available
            if hasattr(response, "response_metadata"):
                usage = response.response_metadata.get("usage", {})
                if usage:
                    self.cost_tracker.track_usage(
                        model=self.model_name,
                        input_tokens=usage.get("prompt_tokens", 0),
                        output_tokens=usage.get("completion_tokens", 0),
                    )

            logger.info(
                f"{self.name} LLM call complete",
                extra={
                    "extra_fields": {
                        "model": self.model_name,
                        "total_cost": self.cost_tracker.total_cost,
                    }
                },
            )

            return response.content

        except Exception as e:
            logger.error(f"{self.name} LLM call failed: {e}")
            raise

    def _create_messages(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
    ) -> list[BaseMessage]:
        """
        Create message list for LLM.

        Args:
            user_message: User message content
            system_prompt: Optional system prompt (uses default if None)

        Returns:
            List of messages
        """
        messages = []

        # Add system message
        prompt = system_prompt or self.get_system_prompt()
        messages.append(SystemMessage(content=prompt))

        # Add user message
        messages.append(HumanMessage(content=user_message))

        return messages

    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get cost summary for this agent's operations.

        Returns:
            Cost summary dictionary
        """
        return self.cost_tracker.get_summary()
