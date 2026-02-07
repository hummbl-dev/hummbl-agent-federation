"""
Tests for the provider registry.
"""

import pytest
from src.registry.models import Provider, ProviderCapabilities, ProviderCost, ProviderTier
from src.registry.loader import RegistryLoader


class TestProviderModel:
    """Test the Provider dataclass."""
    
    def test_provider_creation(self, mock_provider):
        """Test creating a provider."""
        assert mock_provider.id == "test-provider"
        assert mock_provider.name == "Test Provider"
        assert mock_provider.is_healthy
    
    def test_provider_cost_estimate(self, mock_provider):
        """Test cost estimation."""
        cost = mock_provider.cost.estimate(1000, 500)
        # (1000/1M * $1.00) + (500/1M * $2.00) = $0.001 + $0.001 = $0.002
        assert cost == pytest.approx(0.002, rel=1e-3)
    
    def test_provider_to_dict(self, mock_provider):
        """Test provider serialization."""
        data = mock_provider.to_dict()
        assert data["id"] == "test-provider"
        assert "capabilities" in data
        assert "cost" in data


class TestRegistryLoader:
    """Test the registry loader."""
    
    def test_load_defaults(self):
        """Test loading default providers."""
        loader = RegistryLoader()
        providers = loader.load_defaults()
        
        assert len(providers) >= 5
        assert "openai" in providers
        assert "anthropic" in providers
        assert "deepseek" in providers
    
    def test_create_provider_from_dict(self):
        """Test creating provider from dict config."""
        loader = RegistryLoader()
        
        config = {
            "id": "test",
            "name": "Test Provider",
            "tier": "frontier",
            "api_base": "https://api.test.com",
            "capabilities": {
                "max_context": 4096,
                "supports_functions": True,
            },
            "cost": {
                "input_per_1m": 1.0,
                "output_per_1m": 2.0,
            },
        }
        
        provider = loader._create_provider(config)
        
        assert provider.id == "test"
        assert provider.capabilities.max_context == 4096
        assert provider.cost.input_per_1m == 1.0


class TestProviderStore:
    """Test the provider store backends."""
    
    def test_sqlite_save_and_get(self, temp_db, mock_provider):
        """Test saving and retrieving a provider."""
        temp_db.save_provider(mock_provider)
        
        retrieved = temp_db.get_provider(mock_provider.id)
        assert retrieved is not None
        assert retrieved.id == mock_provider.id
    
    def test_sqlite_get_all(self, temp_db, mock_providers):
        """Test retrieving all providers."""
        for provider in mock_providers.values():
            temp_db.save_provider(provider)
        
        all_providers = temp_db.get_all_providers()
        assert len(all_providers) == len(mock_providers)
    
    def test_sqlite_health_history(self, temp_db, mock_provider):
        """Test saving and retrieving health history."""
        temp_db.save_provider(mock_provider)
        
        from datetime import datetime
        from src.registry.models import ProviderHealth, ProviderStatus
        
        health = ProviderHealth(
            status=ProviderStatus.HEALTHY,
            last_checked=datetime.utcnow(),
            avg_latency_ms=100.0,
        )
        
        temp_db.save_health(mock_provider.id, health)
        history = temp_db.get_health_history(mock_provider.id)
        
        assert len(history) == 1
        assert history[0]["status"] == "HEALTHY"
