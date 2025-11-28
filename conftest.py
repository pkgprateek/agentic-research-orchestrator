"""Pytest configuration and fixtures."""

import sys
import pytest
from pathlib import Path

# Add project root to Python path for src imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Mock environment variables for all tests."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-mock-key")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-mock-key")
    monkeypatch.setenv("LANGSMITH_API_KEY", "lsv2-mock-key")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")
    monkeypatch.setenv("LANGCHAIN_PROJECT", "test-project")
