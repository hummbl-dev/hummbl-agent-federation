"""SDK data models."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class RouteConstraints:
    """Constraints for routing decisions."""
    max_cost: Optional[float] = None
    max_latency_ms: Optional[int] = None
    data_residency: Optional[str] = None
    gdpr_required: bool = False
    soc2_required: bool = False
    hipaa_required: bool = False
    provider_preference: Optional[str] = None


@dataclass
class RouteResponse:
    """Response from routing a task."""
    provider: str
    model: str
    content: str
    cost: float
    latency_ms: int
    input_tokens: int
    output_tokens: int
    confidence: float
    reasoning: str
    created_at: datetime
    raw_response: Optional[Dict[str, Any]] = None
