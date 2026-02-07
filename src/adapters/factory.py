"""
Adapter factory for creating provider adapters.
"""

import os
from typing import Dict, Optional, Type

from .base import BaseAdapter
from .openai import OpenAIAdapter
from .anthropic import AnthropicAdapter
from .openrouter import OpenRouterAdapter
from .deepseek import DeepSeekAdapter
from .groq import GroqAdapter
from .ollama import OllamaAdapter


# Registry of adapter classes
ADAPTER_REGISTRY: Dict[str, Type[BaseAdapter]] = {
    "openai": OpenAIAdapter,
    "anthropic": AnthropicAdapter,
    "openrouter": OpenRouterAdapter,
    "deepseek": DeepSeekAdapter,
    "groq": GroqAdapter,
    "ollama": OllamaAdapter,
}


class AdapterFactory:
    """
    Factory for creating provider adapters.
    
    Automatically loads API keys from environment variables
    and creates appropriate adapter instances.
    """
    
    @classmethod
    def create(
        cls,
        provider_id: str,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        **kwargs
    ) -> BaseAdapter:
        """
        Create an adapter for the specified provider.
        
        Args:
            provider_id: Provider identifier (e.g., "openai", "anthropic")
            api_key: API key (if None, loaded from environment)
            api_base: Custom API base URL (optional)
            **kwargs: Additional provider-specific configuration
            
        Returns:
            Configured adapter instance
            
        Raises:
            ValueError: If provider not supported
            RuntimeError: If API key not found
        """
        if provider_id not in ADAPTER_REGISTRY:
            raise ValueError(
                f"Unknown provider: {provider_id}. "
                f"Supported: {list(ADAPTER_REGISTRY.keys())}"
            )
        
        adapter_class = ADAPTER_REGISTRY[provider_id]
        
        # Get API key if not provided
        if api_key is None:
            api_key = cls._get_api_key(provider_id)
        
        if not api_key:
            raise RuntimeError(
                f"API key required for {provider_id}. "
                f"Set {provider_id.upper()}_API_KEY environment variable."
            )
        
        # Get API base if not provided
        if api_base is None:
            api_base = cls._get_api_base(provider_id)
        
        # Create adapter
        return adapter_class(api_key=api_key, api_base=api_base, **kwargs)
    
    @classmethod
    def _get_api_key(cls, provider_id: str) -> Optional[str]:
        """Get API key from environment."""
        env_var = f"{provider_id.upper()}_API_KEY"
        return os.getenv(env_var)
    
    @classmethod
    def _get_api_base(cls, provider_id: str) -> Optional[str]:
        """Get custom API base from environment."""
        env_var = f"{provider_id.upper()}_API_BASE"
        return os.getenv(env_var)
    
    @classmethod
    def register(cls, provider_id: str, adapter_class: Type[BaseAdapter]):
        """
        Register a new adapter class.
        
        Args:
            provider_id: Unique identifier for the provider
            adapter_class: Adapter class (must inherit from BaseAdapter)
        """
        if not issubclass(adapter_class, BaseAdapter):
            raise ValueError("Adapter class must inherit from BaseAdapter")
        
        ADAPTER_REGISTRY[provider_id] = adapter_class
    
    @classmethod
    def list_providers(cls) -> list:
        """List all supported providers."""
        return list(ADAPTER_REGISTRY.keys())
    
    @classmethod
    def is_supported(cls, provider_id: str) -> bool:
        """Check if a provider is supported."""
        return provider_id in ADAPTER_REGISTRY


# Convenience function
def get_adapter(provider_id: str, **kwargs) -> BaseAdapter:
    """
    Get an adapter for the specified provider.
    
    Args:
        provider_id: Provider identifier
        **kwargs: Additional configuration
        
    Returns:
        Configured adapter
    """
    return AdapterFactory.create(provider_id, **kwargs)
