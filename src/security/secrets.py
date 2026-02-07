"""
Secrets management with HashiCorp Vault integration.
"""

import os
from abc import ABC, abstractmethod
from typing import Optional


class SecretsBackend(ABC):
    """Abstract base for secrets backends."""
    
    @abstractmethod
    def get(self, key: str, tenant_id: Optional[str] = None) -> Optional[str]:
        pass
    
    @abstractmethod
    def set(self, key: str, value: str, tenant_id: Optional[str] = None):
        pass


class EnvironmentBackend(SecretsBackend):
    """Read secrets from environment variables."""
    
    def get(self, key: str, tenant_id: Optional[str] = None) -> Optional[str]:
        return os.getenv(key.upper())
    
    def set(self, key: str, value: str, tenant_id: Optional[str] = None):
        raise RuntimeError("Environment backend is read-only")


class SecretsManager:
    """Manages API keys and secrets."""
    
    def __init__(self, backends: Optional[list] = None):
        self.backends = backends or [EnvironmentBackend()]
    
    def get_api_key(self, provider_id: str, tenant_id: Optional[str] = None) -> Optional[str]:
        """Get API key for a provider."""
        key = f"{provider_id.upper()}_API_KEY"
        
        for backend in self.backends:
            try:
                value = backend.get(key, tenant_id)
                if value:
                    return value
            except Exception:
                continue
        
        return None
    
    def set_api_key(self, provider_id: str, api_key: str, tenant_id: Optional[str] = None):
        """Set API key for a provider."""
        key = f"{provider_id.upper()}_API_KEY"
        
        for backend in self.backends:
            try:
                backend.set(key, api_key, tenant_id)
                return
            except RuntimeError:
                continue
        
        raise RuntimeError("No writable backend available")
