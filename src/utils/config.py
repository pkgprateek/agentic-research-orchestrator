"""Configuration management using Pydantic Settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # === LLM Providers ===
    openrouter_api_key: str = Field(..., description="OpenRouter API key")

    # === Search APIs ===
    tavily_api_key: str = Field(..., description="Tavily API key for web search")
    brave_search_api_key: str | None = Field(
        None, description="Brave Search API key (optional backup)"
    )

    # === Observability ===
    langsmith_api_key: str | None = Field(
        None, description="LangSmith API key for tracing"
    )
    langchain_tracing_v2: bool = Field(True, description="Enable LangChain tracing")
    langchain_project: str = Field(
        "market-intelligence-prod", description="LangSmith project name"
    )
    langchain_endpoint: str = Field(
        "https://api.smith.langchain.com", description="LangSmith endpoint"
    )

    # === Application Settings ===
    environment: str = Field(
        "development", description="Environment: development, production"
    )
    default_model: str = Field(
        "x-ai/grok-4.1-fast:free",  # Free for testing; production: anthropic/claude-sonnet-4.5 or google/gemini-3-pro-preview
        description="Default LLM model (via OpenRouter)",
    )
    max_cost_per_run: float = Field(
        2.0, description="Maximum cost per workflow run (USD)"
    )

    # === Optional: Local LLM ===
    ollama_base_url: str | None = Field(
        None, description="Ollama base URL for local models"
    )
    ollama_model: str = Field("llama3.2:3b", description="Ollama model name")

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"

    @property
    def openrouter_base_url(self) -> str:
        """OpenRouter API base URL."""
        return "https://openrouter.ai/api/v1"


def get_settings() -> Settings:
    """Get settings instance (lazy-loaded)."""
    return Settings()  # type: ignore[call-arg]


# For convenience, but use get_settings() in tests
settings = None  # Will be initialized when needed
