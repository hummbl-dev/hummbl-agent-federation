"""
Outcome tracking for routing decisions.

Records what happened after a routing decision to enable learning.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import json


class OutcomeStatus(Enum):
    """Status of a routing outcome."""
    SUCCESS = "success"
    PARTIAL = "partial"  # e.g., slow but correct
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class RoutingOutcome:
    """
    Records what happened after a routing decision.
    
    Used to learn which providers work best for which tasks.
    """
    
    # Identity
    outcome_id: str
    decision_id: str
    task_id: str
    
    # What was routed
    provider_id: str
    model: Optional[str]
    
    # What happened
    status: OutcomeStatus
    
    # Quality metrics (0.0 - 1.0)
    quality_score: Optional[float] = None  # Human or automated rating
    correctness_score: Optional[float] = None  # Did it produce correct output?
    helpfulness_score: Optional[float] = None  # Was it helpful?
    
    # Performance metrics
    actual_cost: Optional[float] = None
    actual_latency_ms: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    
    # Comparison to estimates
    estimated_cost: Optional[float] = None
    estimated_latency_ms: Optional[int] = None
    cost_delta: Optional[float] = None  # actual - estimated
    latency_delta: Optional[int] = None  # actual - estimated
    
    # Error details (if failed)
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    
    # Context
    task_intent: Optional[str] = None
    task_complexity: Optional[str] = None  # "simple", "medium", "complex"
    
    # Timestamps
    routed_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Raw data for analysis
    raw_request: Optional[Dict] = field(default=None, repr=False)
    raw_response: Optional[Dict] = field(default=None, repr=False)
    
    def calculate_deltas(self):
        """Calculate deltas between estimated and actual."""
        if self.actual_cost is not None and self.estimated_cost is not None:
            self.cost_delta = self.actual_cost - self.estimated_cost
        
        if self.actual_latency_ms is not None and self.estimated_latency_ms is not None:
            self.latency_delta = self.actual_latency_ms - self.estimated_latency_ms
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "outcome_id": self.outcome_id,
            "decision_id": self.decision_id,
            "task_id": self.task_id,
            "provider_id": self.provider_id,
            "model": self.model,
            "status": self.status.value,
            "quality_score": self.quality_score,
            "correctness_score": self.correctness_score,
            "helpfulness_score": self.helpfulness_score,
            "actual_cost": self.actual_cost,
            "actual_latency_ms": self.actual_latency_ms,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "estimated_cost": self.estimated_cost,
            "estimated_latency_ms": self.estimated_latency_ms,
            "cost_delta": self.cost_delta,
            "latency_delta": self.latency_delta,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "task_intent": self.task_intent,
            "task_complexity": self.task_complexity,
            "routed_at": self.routed_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class OutcomeTracker:
    """
    Tracks routing outcomes for learning.
    
    Stores outcomes and provides analytics for optimization.
    """
    
    def __init__(self, store=None):
        """
        Initialize tracker.
        
        Args:
            store: Optional registry store for persistence
        """
        self.store = store
        self._outcomes: Dict[str, RoutingOutcome] = {}
        self._provider_stats: Dict[str, Dict[str, Any]] = {}
    
    def record_outcome(self, outcome: RoutingOutcome):
        """
        Record a routing outcome.
        
        Args:
            outcome: The outcome to record
        """
        outcome.calculate_deltas()
        self._outcomes[outcome.outcome_id] = outcome
        
        # Update provider stats
        self._update_provider_stats(outcome)
        
        # Persist if store available
        if self.store:
            # TODO: Implement persistence
            pass
    
    def _update_provider_stats(self, outcome: RoutingOutcome):
        """Update running statistics for a provider."""
        provider_id = outcome.provider_id
        
        if provider_id not in self._provider_stats:
            self._provider_stats[provider_id] = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_cost": 0.0,
                "total_latency_ms": 0,
                "quality_scores": [],
                "task_intents": {},
            }
        
        stats = self._provider_stats[provider_id]
        stats["total_requests"] += 1
        
        if outcome.status == OutcomeStatus.SUCCESS:
            stats["successful_requests"] += 1
        elif outcome.status in (OutcomeStatus.FAILURE, OutcomeStatus.ERROR, OutcomeStatus.TIMEOUT):
            stats["failed_requests"] += 1
        
        if outcome.actual_cost:
            stats["total_cost"] += outcome.actual_cost
        
        if outcome.actual_latency_ms:
            stats["total_latency_ms"] += outcome.actual_latency_ms
        
        if outcome.quality_score:
            stats["quality_scores"].append(outcome.quality_score)
        
        # Track by intent
        intent = outcome.task_intent or "unknown"
        if intent not in stats["task_intents"]:
            stats["task_intents"][intent] = {"count": 0, "success": 0}
        stats["task_intents"][intent]["count"] += 1
        if outcome.status == OutcomeStatus.SUCCESS:
            stats["task_intents"][intent]["success"] += 1
    
    def get_provider_performance(
        self,
        provider_id: str,
        days: int = 7,
        task_intent: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get performance statistics for a provider.
        
        Args:
            provider_id: Provider to analyze
            days: Number of days to look back
            task_intent: Filter by specific intent
            
        Returns:
            Performance statistics
        """
        stats = self._provider_stats.get(provider_id)
        if not stats:
            return None
        
        total = stats["total_requests"]
        if total == 0:
            return None
        
        result = {
            "provider_id": provider_id,
            "total_requests": total,
            "success_rate": stats["successful_requests"] / total,
            "error_rate": stats["failed_requests"] / total,
            "avg_cost": stats["total_cost"] / total if total > 0 else 0,
            "avg_latency_ms": stats["total_latency_ms"] / total if total > 0 else 0,
        }
        
        # Add quality if available
        quality_scores = stats["quality_scores"]
        if quality_scores:
            result["avg_quality_score"] = sum(quality_scores) / len(quality_scores)
        
        # Add intent-specific stats
        if task_intent and task_intent in stats["task_intents"]:
            intent_stats = stats["task_intents"][task_intent]
            result["intent_success_rate"] = (
                intent_stats["success"] / intent_stats["count"]
                if intent_stats["count"] > 0 else 0
            )
        
        return result
    
    def get_best_provider_for_intent(
        self,
        intent: str,
        min_samples: int = 5,
    ) -> Optional[str]:
        """
        Find the best performing provider for a given intent.
        
        Args:
            intent: Task intent to optimize for
            min_samples: Minimum samples required
            
        Returns:
            Best provider ID or None
        """
        candidates = []
        
        for provider_id, stats in self._provider_stats.items():
            intent_stats = stats["task_intents"].get(intent)
            if not intent_stats:
                continue
            
            if intent_stats["count"] < min_samples:
                continue
            
            success_rate = intent_stats["success"] / intent_stats["count"]
            candidates.append((provider_id, success_rate))
        
        if not candidates:
            return None
        
        # Sort by success rate
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get summary statistics for all providers."""
        return {
            "total_outcomes": len(self._outcomes),
            "providers": {
                pid: self.get_provider_performance(pid)
                for pid in self._provider_stats.keys()
            },
        }
    
    def export_to_json(self, filepath: str):
        """Export all outcomes to JSON file."""
        data = [o.to_dict() for o in self._outcomes.values()]
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
