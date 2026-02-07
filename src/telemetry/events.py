"""
Event definitions for federation telemetry.

OpenTelemetry-compatible event schema.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, Any, Optional
import uuid
import json


class EventType(Enum):
    """Types of telemetry events."""
    
    # Request lifecycle
    REQUEST_STARTED = "request.started"
    REQUEST_COMPLETED = "request.completed"
    REQUEST_FAILED = "request.failed"
    
    # Routing
    ROUTING_DECISION = "routing.decision"
    ROUTING_FALLBACK = "routing.fallback"
    
    # Provider interactions
    PROVIDER_CALLED = "provider.called"
    PROVIDER_RESPONDED = "provider.responded"
    PROVIDER_ERROR = "provider.error"
    
    # Health
    HEALTH_CHECK = "health.check"
    HEALTH_DEGRADED = "health.degraded"
    HEALTH_RECOVERED = "health.recovered"
    
    # System
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    CONFIG_CHANGED = "config.changed"


@dataclass
class Event:
    """
    Standardized telemetry event.
    
    Compatible with OpenTelemetry trace/span model.
    """
    
    # Event identity
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.REQUEST_STARTED
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Context
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    
    # Entity identifiers
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    task_id: Optional[str] = None
    provider_id: Optional[str] = None
    
    # Event payload
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    # Performance
    duration_ms: Optional[int] = None
    
    # Status
    status: str = "ok"  # "ok", "error", "warning"
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "task_id": self.task_id,
            "provider_id": self.provider_id,
            "attributes": self.attributes,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "error_message": self.error_message,
            "error_type": self.error_type,
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        return cls(
            event_id=data.get("event_id", str(uuid.uuid4())),
            event_type=EventType(data.get("event_type", "request.started")),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
            trace_id=data.get("trace_id"),
            span_id=data.get("span_id"),
            parent_span_id=data.get("parent_span_id"),
            tenant_id=data.get("tenant_id"),
            user_id=data.get("user_id"),
            task_id=data.get("task_id"),
            provider_id=data.get("provider_id"),
            attributes=data.get("attributes", {}),
            duration_ms=data.get("duration_ms"),
            status=data.get("status", "ok"),
            error_message=data.get("error_message"),
            error_type=data.get("error_type"),
        )


def create_event(
    event_type: EventType,
    tenant_id: Optional[str] = None,
    task_id: Optional[str] = None,
    provider_id: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[int] = None,
    status: str = "ok",
    **kwargs
) -> Event:
    """
    Convenience function to create an event.
    
    Args:
        event_type: Type of event
        tenant_id: Tenant/organization ID
        task_id: Associated task ID
        provider_id: Provider involved
        attributes: Additional event attributes
        duration_ms: Event duration in milliseconds
        status: Event status
        **kwargs: Additional fields
        
    Returns:
        Created event
    """
    return Event(
        event_type=event_type,
        tenant_id=tenant_id,
        task_id=task_id,
        provider_id=provider_id,
        attributes=attributes or {},
        duration_ms=duration_ms,
        status=status,
        **kwargs
    )
