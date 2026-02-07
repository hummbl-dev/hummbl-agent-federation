"""
Pytest fixtures and configuration.
"""

import pytest
from pathlib import Path

from src.registry.models import Provider, ProviderCapabilities, ProviderCost, ProviderHealth
from src.registry.loader import RegistryLoader
from src.registry.store import SQLiteStore
from src.engine.router import Router
from src.engine.classifier import IntentClassifier


@pytest.fixture
def mock_provider():
    """Create a mock provider for testing."""
    return Provider(
        id="test-provider",
        name="Test Provider",
        api_base="https://api.test.com/v1",
        api_key_env="TEST_API_KEY",
        capabilities=ProviderCapabilities(
            max_context=4096,
            supports_functions=True,
            supports_streaming=True,
            specialties={"code", "test"},
            typical_latency_ms=500,
        ),
        cost=ProviderCost(input_per_1m=1.0, output_per_1m=2.0),
        quality_score=0.85,
        reliability_score=0.95,
        models=["test-model-v1"],
    )


@pytest.fixture
def mock_providers():
    """Create multiple mock providers for testing."""
    return {
        "openai": Provider(
            id="openai",
            name="OpenAI",
            api_base="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
            capabilities=ProviderCapabilities(
                max_context=128_000,
                supports_functions=True,
                specialties={"code", "reasoning"},
                typical_latency_ms=1200,
            ),
            cost=ProviderCost(input_per_1m=2.50, output_per_1m=10.00),
            quality_score=0.95,
        ),
        "deepseek": Provider(
            id="deepseek",
            name="DeepSeek",
            api_base="https://api.deepseek.com",
            api_key_env="DEEPSEEK_API_KEY",
            capabilities=ProviderCapabilities(
                max_context=64_000,
                supports_functions=True,
                specialties={"code", "cost_efficient"},
                typical_latency_ms=2100,
            ),
            cost=ProviderCost(input_per_1m=0.14, output_per_1m=0.28),
            quality_score=0.88,
        ),
        "groq": Provider(
            id="groq",
            name="Groq",
            api_base="https://api.groq.com/openai/v1",
            api_key_env="GROQ_API_KEY",
            capabilities=ProviderCapabilities(
                max_context=128_000,
                supports_functions=True,
                specialties={"speed"},
                typical_latency_ms=300,
            ),
            cost=ProviderCost(input_per_1m=0.59, output_per_1m=0.79),
            quality_score=0.85,
        ),
    }


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary SQLite database."""
    db_path = tmp_path / "test.db"
    return SQLiteStore(str(db_path))


@pytest.fixture
def router(mock_providers, temp_db):
    """Create a router with mock providers."""
    for provider in mock_providers.values():
        temp_db.save_provider(provider)
    
    return Router(temp_db)


@pytest.fixture
def classifier():
    """Create an intent classifier."""
    return IntentClassifier()


@pytest.fixture
def sample_tasks():
    """Sample tasks for testing classification."""
    return {
        "code": "Implement a function to calculate fibonacci numbers",
        "research": "Research the latest developments in quantum computing",
        "documentation": "Write documentation for the authentication API",
        "debugging": "Debug this error: KeyError 'user_id' not found",
        "summarize": "Summarize the key points from this article",
    }
