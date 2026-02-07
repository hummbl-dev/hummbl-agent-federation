"""
Event ingestion system for telemetry.

Collects and routes events to storage backends.
"""

import asyncio
from datetime import datetime
from typing import Callable, Dict, List, Optional, Any
from collections import deque
import json

from .events import Event, EventType


class EventIngestor:
    """
    Ingests telemetry events and routes to storage.
    
    Features:
    - Async batch ingestion
    - Multiple backends (stdout, file, HTTP, etc.)
    - In-memory buffer with overflow handling
    """
    
    def __init__(
        self,
        buffer_size: int = 10000,
        flush_interval: float = 5.0,
        batch_size: int = 100,
    ):
        """
        Initialize ingestor.
        
        Args:
            buffer_size: Maximum events to hold in memory
            flush_interval: Seconds between automatic flushes
            batch_size: Number of events per batch write
        """
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.batch_size = batch_size
        
        # In-memory buffer
        self._buffer: deque = deque(maxlen=buffer_size)
        
        # Backend handlers
        self._backends: List[Callable[[List[Event]], None]] = []
        
        # Stats
        self._total_ingested = 0
        self._total_dropped = 0
        self._total_flushed = 0
        
        # Async lock
        self._lock = asyncio.Lock()
    
    def add_backend(self, handler: Callable[[List[Event]], None]):
        """
        Add a backend handler for events.
        
        Args:
            handler: Function that takes a list of events
        """
        self._backends.append(handler)
    
    async def ingest(self, event: Event):
        """
        Ingest a single event.
        
        Args:
            event: Event to ingest
        """
        async with self._lock:
            if len(self._buffer) >= self.buffer_size:
                self._total_dropped += 1
                return
            
            self._buffer.append(event)
            self._total_ingested += 1
    
    async def ingest_batch(self, events: List[Event]):
        """
        Ingest multiple events.
        
        Args:
            events: List of events to ingest
        """
        async with self._lock:
            for event in events:
                if len(self._buffer) >= self.buffer_size:
                    self._total_dropped += 1
                    continue
                
                self._buffer.append(event)
                self._total_ingested += 1
    
    async def flush(self):
        """Manually flush buffer to backends."""
        async with self._lock:
            if not self._buffer:
                return
            
            # Get all events from buffer
            events = list(self._buffer)
            self._buffer.clear()
            
            # Send to all backends
            for handler in self._backends:
                try:
                    handler(events)
                except Exception as e:
                    # Log error but continue with other backends
                    print(f"Backend error: {e}")
            
            self._total_flushed += len(events)
    
    async def start(self):
        """Start automatic flush loop."""
        while True:
            await asyncio.sleep(self.flush_interval)
            await self.flush()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ingestor statistics."""
        return {
            "total_ingested": self._total_ingested,
            "total_dropped": self._total_dropped,
            "total_flushed": self._total_flushed,
            "buffer_size": len(self._buffer),
            "backends": len(self._backends),
        }


class StdoutBackend:
    """Backend that prints events to stdout."""
    
    def __init__(self, pretty: bool = False):
        self.pretty = pretty
    
    def __call__(self, events: List[Event]):
        for event in events:
            if self.pretty:
                print(json.dumps(event.to_dict(), indent=2, default=str))
            else:
                print(event.to_json())


class FileBackend:
    """Backend that writes events to a file."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
    
    def __call__(self, events: List[Event]):
        with open(self.filepath, "a") as f:
            for event in events:
                f.write(event.to_json() + "\n")


class CallbackBackend:
    """Backend that calls a custom callback function."""
    
    def __init__(self, callback: Callable[[Event], None]):
        self.callback = callback
    
    def __call__(self, events: List[Event]):
        for event in events:
            self.callback(event)


# Global ingestor instance (for convenience)
_ingestor: Optional[EventIngestor] = None


def get_ingestor() -> EventIngestor:
    """Get or create global ingestor instance."""
    global _ingestor
    if _ingestor is None:
        _ingestor = EventIngestor()
        # Add stdout backend by default
        _ingestor.add_backend(StdoutBackend())
    return _ingestor


def set_ingestor(ingestor: EventIngestor):
    """Set global ingestor instance."""
    global _ingestor
    _ingestor = ingestor


async def emit(event: Event):
    """
    Emit an event to the global ingestor.
    
    Args:
        event: Event to emit
    """
    await get_ingestor().ingest(event)


async def emit_event(
    event_type: EventType,
    tenant_id: Optional[str] = None,
    task_id: Optional[str] = None,
    provider_id: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    **kwargs
):
    """
    Convenience function to create and emit an event.
    
    Args:
        event_type: Type of event
        tenant_id: Tenant ID
        task_id: Task ID
        provider_id: Provider ID
        attributes: Event attributes
        **kwargs: Additional event fields
    """
    from .events import create_event
    
    event = create_event(
        event_type=event_type,
        tenant_id=tenant_id,
        task_id=task_id,
        provider_id=provider_id,
        attributes=attributes,
        **kwargs
    )
    
    await emit(event)
