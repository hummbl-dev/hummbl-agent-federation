"""
Provider data models for the federation registry.

Defines the core dataclasses representing model providers,
their capabilities, costs, and health status.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Any
import json


class ProviderTier(Enum):
    """Classification of provider maturity and capability."""
    FRONTIER = "frontier"           # Tier 1: OpenAI, Anthropic, Google, etc.
    CHINESE_FRONTIER = "chinese"    # Tier 2: DeepSeek, Qwen, etc.
    AGGREGATOR = "aggregator"       # Tier 3: OpenRouter, Together, etc.
    CLOUD = "cloud"                 # Tier 4: Bedrock, Vertex, Azure
    SPECIALIZED = "specialized"     # Tier 5: Phind, Perplexity, etc.
    OPENSOURCE = "opensource"       # Tier 6: Ollama, vLLM, etc.
    EMERGING = "emerging"           # Tier 7: New entrants


class ProviderStatus(Enum):
    """Operational status of a provider."""
    HEALTHY = auto()
    DEGRADED = auto()
    UNHEALTHY = auto()
    UNKNOWN = auto()
    DISABLED = auto()


@dataclass(frozen=True)
class ProviderCost:
    """Pricing information for a provider."""
    input_per_1m: float           # Cost per 1M input tokens
    output_per_1m: float          # Cost per 1M output tokens
    context_cache_hit: Optional[float] = None  # Cached context discount
    batch_discount: Optional[float] = None     # Batch processing discount
    currency: str = "USD"
    
    def estimate(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a given token count."""
        input_cost = (input_tokens / 1_000_000) * self.input_per_1m
        output_cost = (output_tokens / 1_000_000) * self.output_per_1m
        return round(input_cost + output_cost, 4)


@dataclass(frozen=True)
class ProviderCapabilities:
    """Capabilities and features supported by a provider."""
    # Model capabilities
    max_context: int              # Maximum context window
    supports_functions: bool = False
    supports_vision: bool = False
    supports_json_mode: bool = False
    supports_streaming: bool = True
    supports_batch: bool = False
    
    # Special features
    specialties: Set[str] = field(default_factory=set)
    # Examples: "code", "reasoning", "multimodal", "long_context", "cost_efficient"
    
    # Performance characteristics
    typical_latency_ms: Optional[int] = None
    throughput_tpm: Optional[int] = None  # Tokens per minute
    
    # Compliance
    soc2_compliant: bool = False
    gdpr_compliant: bool = False
    hipaa_compliant: bool = False
    data_residency: Set[str] = field(default_factory=set)  # "us", "eu", "apac"


@dataclass
class ProviderHealth:
    """Health metrics for a provider."""
    status: ProviderStatus = ProviderStatus.UNKNOWN
    last_checked: Optional[datetime] = None
    avg_latency_ms: Optional[float] = None
    error_rate_24h: Optional[float] = None
    success_rate_24h: Optional[float] = None
    
    # Circuit breaker state
    consecutive_failures: int = 0
    circuit_open: bool = False
    circuit_open_until: Optional[datetime] = None
    
    def is_available(self) -> bool:
        """Check if provider should receive traffic."""
        if self.circuit_open:
            if self.circuit_open_until and datetime.utcnow() > self.circuit_open_until:
                self.circuit_open = False
                self.consecutive_failures = 0
                return True
            return False
        return self.status in (ProviderStatus.HEALTHY, ProviderStatus.DEGRADED)


@dataclass
class Provider:
    """
    Complete representation of a model provider in the federation.
    
    This is the core data structure used for routing decisions.
    """
    # Identity
    id: str                       # Unique identifier (e.g., "openai", "deepseek")
    name: str                     # Display name
    tier: ProviderTier
    emoji: str = "🤖"            # Visual identifier
    
    # API configuration
    api_base: str
    api_key_env: str              # Environment variable name for API key
    
    # Capabilities and pricing
    capabilities: ProviderCapabilities = field(default_factory=ProviderCapabilities)
    cost: ProviderCost = field(default_factory=lambda: ProviderCost(0.0, 0.0))
    
    # Operational state
    health: ProviderHealth = field(default_factory=ProviderHealth)
    enabled: bool = True
    
    # Routing weights (override defaults)
    quality_score: Optional[float] = None      # 0.0 - 1.0
    reliability_score: Optional[float] = None  # 0.0 - 1.0
    
    # Metadata
    models: List[str] = field(default_factory=list)
    docs_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Custom configuration
    config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate provider configuration."""
        if not self.id:
            raise ValueError("Provider must have an id")
        if not self.api_base:
            raise ValueError("Provider must have an api_base")
    
    @property
    def is_healthy(self) -> bool:
        """Quick health check."""
        return self.enabled and self.health.is_available()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize provider to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "tier": self.tier.value,
            "emoji": self.emoji,
            "api_base": self.api_base,
            "api_key_env": self.api_key_env,
            "capabilities": {
                "max_context": self.capabilities.max_context,
                "supports_functions": self.capabilities.supports_functions,
                "supports_vision": self.capabilities.supports_vision,
                "supports_json_mode": self.capabilities.supports_json_mode,
                "supports_streaming": self.capabilities.supports_streaming,
                "supports_batch": self.capabilities.supports_batch,
                "specialties": list(self.capabilities.specialties),
                "typical_latency_ms": self.capabilities.typical_latency_ms,
                "throughput_tpm": self.capabilities.throughput_tpm,
                "soc2_compliant": self.capabilities.soc2_compliant,
                "gdpr_compliant": self.capabilities.gdpr_compliant,
                "hipaa_compliant": self.capabilities.hipaa_compliant,
                "data_residency": list(self.capabilities.data_residency),
            },
            "cost": {
                "input_per_1m": self.cost.input_per_1m,
                "output_per_1m": self.cost.output_per_1m,
                "currency": self.cost.currency,
            },
            "health": {
                "status": self.health.status.name,
                "is_available": self.health.is_available(),
            },
            "enabled": self.enabled,
            "quality_score": self.quality_score,
            "reliability_score": self.reliability_score,
            "models": self.models,
        }
    
    def __repr__(self) -> str:
        return f"Provider({self.emoji} {self.id} - {self.health.status.name})"


# Pre-defined provider configurations for quick setup
DEFAULT_PROVIDERS = {
    "openai": Provider(
        id="openai",
        name="OpenAI",
        tier=ProviderTier.FRONTIER,
        emoji="🅾️",
        api_base="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        capabilities=ProviderCapabilities(
            max_context=128_000,
            supports_functions=True,
            supports_vision=True,
            supports_json_mode=True,
            specialties={"code", "reasoning", "multimodal"},
            typical_latency_ms=1200,
            soc2_compliant=True,
        ),
        cost=ProviderCost(input_per_1m=2.50, output_per_1m=10.00),
        quality_score=0.95,
        reliability_score=0.99,
        models=["gpt-4o", "gpt-4o-mini", "o1", "o3-mini"],
    ),
    "anthropic": Provider(
        id="anthropic",
        name="Anthropic",
        tier=ProviderTier.FRONTIER,
        emoji="🅰️",
        api_base="https://api.anthropic.com/v1",
        api_key_env="ANTHROPIC_API_KEY",
        capabilities=ProviderCapabilities(
            max_context=200_000,
            supports_functions=True,
            supports_vision=True,
            supports_json_mode=True,
            specialties={"analysis", "documentation", "safety"},
            typical_latency_ms=1500,
            soc2_compliant=True,
        ),
        cost=ProviderCost(input_per_1m=3.00, output_per_1m=15.00),
        quality_score=0.96,
        reliability_score=0.98,
        models=["claude-3-5-sonnet", "claude-3-opus", "claude-3-haiku"],
    ),
    "deepseek": Provider(
        id="deepseek",
        name="DeepSeek",
        tier=ProviderTier.CHINESE_FRONTIER,
        emoji="🐋",
        api_base="https://api.deepseek.com",
        api_key_env="DEEPSEEK_API_KEY",
        capabilities=ProviderCapabilities(
            max_context=64_000,
            supports_functions=True,
            supports_json_mode=True,
            specialties={"code", "reasoning", "cost_efficient"},
            typical_latency_ms=2100,
        ),
        cost=ProviderCost(input_per_1m=0.14, output_per_1m=0.28),
        quality_score=0.88,
        reliability_score=0.95,
        models=["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
    ),
    "groq": Provider(
        id="groq",
        name="Groq",
        tier=ProviderTier.AGGREGATOR,
        emoji="⚡",
        api_base="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
        capabilities=ProviderCapabilities(
            max_context=128_000,
            supports_functions=True,
            supports_json_mode=True,
            specialties={"speed", "throughput"},
            typical_latency_ms=300,
            throughput_tpm=1_000_000,
        ),
        cost=ProviderCost(input_per_1m=0.59, output_per_1m=0.79),
        quality_score=0.85,
        reliability_score=0.94,
        models=["llama-3.1-70b", "llama-3.1-8b", "mixtral-8x7b"],
    ),
    "ollama": Provider(
        id="ollama",
        name="Ollama (Local)",
        tier=ProviderTier.OPENSOURCE,
        emoji="🏠",
        api_base="http://localhost:11434/v1",
        api_key_env="OLLAMA_API_KEY",  # Optional for local
        capabilities=ProviderCapabilities(
            max_context=128_000,
            supports_functions=False,
            supports_json_mode=False,
            specialties={"privacy", "offline", "zero_cost"},
            typical_latency_ms=100,
            data_residency={"local"},
        ),
        cost=ProviderCost(input_per_1m=0.0, output_per_1m=0.0),
        quality_score=0.80,
        reliability_score=0.99,
        models=["llama3.2", "mistral", "qwen2.5"],
    ),
}
