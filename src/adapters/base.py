"""
Base adapter interface for LLM providers.

All provider adapters must implement this interface for unified access.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Dict, List, Optional, Any
from datetime import datetime


@dataclass
class AdapterResponse:
    """Standardized response from any provider adapter."""
    
    # Content
    content: str
    model: str
    provider: str
    
    # Usage
    input_tokens: int
    output_tokens: int
    total_tokens: int
    
    # Cost (calculated by adapter)
    cost_usd: float
    
    # Metadata
    response_id: Optional[str] = None
    finish_reason: Optional[str] = None
    
    # Timing
    latency_ms: int = 0
    created_at: datetime = None
    
    # Raw response (for debugging)
    raw_response: Optional[Dict] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class AdapterRequest:
    """Standardized request to any provider adapter."""
    
    # Required
    prompt: str
    
    # Optional context
    system_prompt: Optional[str] = None
    messages: Optional[List[Dict[str, str]]] = None
    
    # Model configuration
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    
    # Feature flags
    stream: bool = False
    json_mode: bool = False
    
    # Federation metadata
    task_id: Optional[str] = None
    routing_decision: Optional[Dict] = None


class BaseAdapter(ABC):
    """
    Abstract base class for all provider adapters.
    
    Implementations must provide:
    - authenticate(): Validate credentials
    - complete(): Non-streaming completion
    - stream(): Streaming completion (if supported)
    - health_check(): Verify connectivity
    """
    
    def __init__(self, provider_id: str, api_key: str, api_base: str, **kwargs):
        """
        Initialize adapter.
        
        Args:
            provider_id: Unique identifier for this provider
            api_key: API key for authentication
            api_base: Base URL for API requests
            **kwargs: Additional provider-specific configuration
        """
        self.provider_id = provider_id
        self.api_key = api_key
        self.api_base = api_base.rstrip('/')
        self.config = kwargs
        
        # Metrics
        self.total_requests = 0
        self.total_errors = 0
        self.avg_latency_ms = 0.0
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Validate API credentials.
        
        Returns:
            True if authentication successful
        """
        pass
    
    @abstractmethod
    async def complete(self, request: AdapterRequest) -> AdapterResponse:
        """
        Send completion request (non-streaming).
        
        Args:
            request: The completion request
            
        Returns:
            Standardized response
        """
        pass
    
    async def stream(self, request: AdapterRequest) -> AsyncIterator[AdapterResponse]:
        """
        Send completion request (streaming).
        
        Args:
            request: The completion request
            
        Yields:
            Response chunks as they're received
            
        Note:
            Default implementation raises NotImplementedError.
            Adapters that support streaming should override.
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support streaming")
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check provider health/connectivity.
        
        Returns:
            Health status dictionary
        """
        pass
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost based on provider pricing.
        
        Override if provider has complex pricing.
        """
        from ..registry.models import ProviderCost
        
        # Default cost calculation (should be overridden)
        cost_per_1m_input = self.config.get('cost_input_per_1m', 0.0)
        cost_per_1m_output = self.config.get('cost_output_per_1m', 0.0)
        
        cost = ProviderCost(
            input_per_1m=cost_per_1m_input,
            output_per_1m=cost_per_1m_output
        )
        
        return cost.estimate(input_tokens, output_tokens)
    
    def _update_metrics(self, latency_ms: int, error: bool = False):
        """Update internal metrics."""
        self.total_requests += 1
        if error:
            self.total_errors += 1
        
        # Exponential moving average for latency
        alpha = 0.1  # Smoothing factor
        self.avg_latency_ms = (alpha * latency_ms) + (1 - alpha) * self.avg_latency_ms
    
    @property
    def error_rate(self) -> float:
        """Calculate current error rate."""
        if self.total_requests == 0:
            return 0.0
        return self.total_errors / self.total_requests
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get adapter metrics."""
        return {
            'provider_id': self.provider_id,
            'total_requests': self.total_requests,
            'total_errors': self.total_errors,
            'error_rate': self.error_rate,
            'avg_latency_ms': self.avg_latency_ms,
        }
