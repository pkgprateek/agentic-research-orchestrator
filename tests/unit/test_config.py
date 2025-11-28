"""Unit tests for configuration management."""

import pytest
from pydantic import ValidationError

from src.utils.config import Settings


def test_settings_with_valid_env(monkeypatch):
    """Test settings load correctly with valid environment variables."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
    monkeypatch.setenv("ENVIRONMENT", "production")

    settings = Settings()

    assert settings.openrouter_api_key == "test-openrouter-key"
    assert settings.tavily_api_key == "test-tavily-key"
    assert settings.environment == "production"
    assert settings.is_production is True


def test_settings_with_defaults(monkeypatch):
    """Test settings use defaults for optional fields."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    settings = Settings()

    assert settings.default_model == "x-ai/grok-4.1-fast:free"
    assert settings.max_cost_per_run == 2.0
    assert settings.langchain_project == "market-intelligence-prod"


def test_settings_with_missing_keys():
    """Test settings when some keys are missing (should use defaults)."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test"}, clear=True):
        settings = Settings()
        assert settings.openrouter_api_key == "test"
        assert (
            settings.default_model == "x-ai/grok-4.1-fast:free"
        )  # Falls back to default


def test_openrouter_base_url():
    """Test OpenRouter base URL property."""
    # Use minimal valid settings
    settings = Settings(openrouter_api_key="test", tavily_api_key="test")
    assert settings.openrouter_base_url == "https://openrouter.ai/api/v1"


def test_is_production_property(monkeypatch):
    """Test is_production property works correctly."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("TAVILY_API_KEY", "test")

    # Test development
    monkeypatch.setenv("ENVIRONMENT", "development")
    settings = Settings()
    assert settings.is_production is False

    # Test production
    monkeypatch.setenv("ENVIRONMENT", "production")
    settings = Settings()
    assert settings.is_production is True
