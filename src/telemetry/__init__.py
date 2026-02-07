"""
Telemetry and observability for the federation.

Event ingestion, metrics collection, and health monitoring.
"""

from .events import Event, EventType, create_event
from .ingestor import EventIngestor

__all__ = ["Event", "EventType", "create_event", "EventIngestor"]
