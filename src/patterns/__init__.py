"""
Advanced coordination patterns for multi-agent workflows.
"""

from .mapreduce import MapReducePattern
from .consensus import DebatePattern
from .pipeline import PipelinePattern

__all__ = ["MapReducePattern", "DebatePattern", "PipelinePattern"]
