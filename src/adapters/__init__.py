"""
Provider adapters for the federation.

Unified interface to multiple LLM providers.
"""

from .base import BaseAdapter, AdapterResponse
from .factory import AdapterFactory

__all__ = ["BaseAdapter", "AdapterResponse", "AdapterFactory"]
