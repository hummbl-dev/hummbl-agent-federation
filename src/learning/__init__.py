"""
Learning and optimization for the federation.

Outcome tracking, A/B testing, and adaptive routing improvements.
"""

from .outcomes import OutcomeTracker, RoutingOutcome
from .optimizer import RoutingOptimizer

__all__ = ["OutcomeTracker", "RoutingOutcome", "RoutingOptimizer"]
