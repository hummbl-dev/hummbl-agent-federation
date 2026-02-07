"""
Federation Routing Engine

Intelligent task routing across 50+ providers with quality-cost-latency optimization.
"""

from .models import Task, TaskIntent, TaskRequirements, RoutingDecision
from .classifier import IntentClassifier
from .router import Router
from .cost import CostCalculator

__all__ = [
    "Task",
    "TaskIntent",
    "TaskRequirements",
    "RoutingDecision",
    "IntentClassifier",
    "Router",
    "CostCalculator",
]
