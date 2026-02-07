"""
Routing optimizer with A/B testing and multi-armed bandit.

Improves routing decisions based on historical outcomes.
"""

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from ..registry.models import Provider
from ..engine.models import Task, TaskIntent
from .outcomes import OutcomeTracker, OutcomeStatus


@dataclass
class ProviderScore:
    """Score for a provider on a specific intent."""
    provider_id: str
    intent: str
    
    # Multi-armed bandit parameters
    trials: int = 0
    successes: int = 0
    
    # Derived scores
    win_rate: float = 0.0
    ucb_score: float = 0.0  # Upper Confidence Bound
    
    def update(self, success: bool):
        """Update with new outcome."""
        self.trials += 1
        if success:
            self.successes += 1
        self.win_rate = self.successes / self.trials if self.trials > 0 else 0.0
    
    def calculate_ucb(self, total_trials: int, exploration_factor: float = 1.414):
        """
        Calculate Upper Confidence Bound for multi-armed bandit.
        
        Higher UCB = more exploration potential.
        """
        if self.trials == 0:
            return float('inf')  # Always try untested providers
        
        exploitation = self.win_rate
        exploration = exploration_factor * (
            (2 * (total_trials ** 0.5)) / (self.trials ** 0.5)
        )
        
        self.ucb_score = exploitation + exploration
        return self.ucb_score


class RoutingOptimizer:
    """
    Optimizes routing using multi-armed bandit algorithm.
    
    Balances exploration (trying new providers) with
    exploitation (using known good providers).
    """
    
    def __init__(
        self,
        outcome_tracker: OutcomeTracker,
        exploration_rate: float = 0.05,
        min_samples_before_exploit: int = 10,
    ):
        """
        Initialize optimizer.
        
        Args:
            outcome_tracker: Source of historical outcomes
            exploration_rate: Base probability of exploration
            min_samples_before_exploit: Min samples before favoring best
        """
        self.outcome_tracker = outcome_tracker
        self.exploration_rate = exploration_rate
        self.min_samples_before_exploit = min_samples_before_exploit
        
        # Cache of provider scores by intent
        self._scores: Dict[Tuple[str, str], ProviderScore] = {}
        self._last_update: Optional[datetime] = None
    
    def select_provider(
        self,
        candidates: List[Provider],
        task: Task,
        base_scores: Dict[str, float],
    ) -> Tuple[Provider, str]:
        """
        Select provider using optimized strategy.
        
        Args:
            candidates: Available providers
            task: The task to route
            base_scores: Base routing scores from Router
            
        Returns:
            Tuple of (selected provider, reason)
        """
        intent = task.intent.value if task.intent else "unknown"
        
        # Update scores from recent outcomes
        self._refresh_scores(candidates, intent)
        
        # Check if we have enough data to optimize
        total_trials = sum(
            s.trials for s in self._scores.values()
            if s.intent == intent
        )
        
        if total_trials < self.min_samples_before_exploit:
            # Not enough data, use base router scores
            best = max(candidates, key=lambda p: base_scores.get(p.id, 0))
            return best, "insufficient_data_for_optimization"
        
        # Multi-armed bandit selection
        # With probability exploration_rate, pick randomly
        # Otherwise, use UCB to balance exploration/exploitation
        
        if random.random() < self.exploration_rate:
            # Pure exploration: pick randomly
            selected = random.choice(candidates)
            return selected, "exploration"
        
        # UCB-based selection
        intent_scores = [
            self._scores.get((p.id, intent))
            for p in candidates
            if (p.id, intent) in self._scores
        ]
        
        if not intent_scores:
            # No scores yet, pick by base score
            best = max(candidates, key=lambda p: base_scores.get(p.id, 0))
            return best, "no_optimization_scores"
        
        # Calculate UCB for each
        for score in intent_scores:
            score.calculate_ucb(total_trials)
        
        # Pick highest UCB
        best_score = max(intent_scores, key=lambda s: s.ucb_score)
        best_provider = next(
            p for p in candidates if p.id == best_score.provider_id
        )
        
        reason = f"ucb_optimization (trials={best_score.trials}, win_rate={best_score.win_rate:.2f})"
        return best_provider, reason
    
    def _refresh_scores(self, candidates: List[Provider], intent: str):
        """Refresh scores from outcome tracker."""
        # Only refresh every 5 minutes
        if self._last_update and (
            datetime.utcnow() - self._last_update < timedelta(minutes=5)
        ):
            return
        
        for provider in candidates:
            key = (provider.id, intent)
            
            if key not in self._scores:
                self._scores[key] = ProviderScore(
                    provider_id=provider.id,
                    intent=intent,
                )
            
            # Update from outcome tracker stats
            stats = self.outcome_tracker.get_provider_performance(
                provider.id,
                task_intent=intent,
            )
            
            if stats:
                score = self._scores[key]
                # Estimate trials/successes from stats
                total = stats.get("total_requests", 0)
                success_rate = stats.get("success_rate", 0)
                
                if total > score.trials:
                    # Update with new data
                    new_trials = total - score.trials
                    new_successes = int(new_trials * success_rate)
                    
                    score.trials = total
                    score.successes = int(total * success_rate)
                    score.win_rate = success_rate
        
        self._last_update = datetime.utcnow()
    
    def record_feedback(
        self,
        provider_id: str,
        intent: str,
        success: bool,
    ):
        """
        Record explicit feedback for learning.
        
        Args:
            provider_id: Provider that was used
            intent: Task intent
            success: Whether the routing was successful
        """
        key = (provider_id, intent)
        
        if key not in self._scores:
            self._scores[key] = ProviderScore(
                provider_id=provider_id,
                intent=intent,
            )
        
        self._scores[key].update(success)
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        stats = {
            "total_score_entries": len(self._scores),
            "exploration_rate": self.exploration_rate,
            "min_samples": self.min_samples_before_exploit,
            "by_intent": {},
        }
        
        # Group by intent
        by_intent: Dict[str, List[ProviderScore]] = {}
        for score in self._scores.values():
            if score.intent not in by_intent:
                by_intent[score.intent] = []
            by_intent[score.intent].append(score)
        
        for intent, scores in by_intent.items():
            stats["by_intent"][intent] = {
                "providers": len(scores),
                "total_trials": sum(s.trials for s in scores),
                "best_provider": max(scores, key=lambda s: s.win_rate).provider_id
                if scores else None,
            }
        
        return stats
    
    def recommend_experiments(self) -> List[Dict[str, str]]:
        """
        Recommend A/B test experiments.
        
        Returns:
            List of experiment recommendations
        """
        recommendations = []
        
        # Find intents with few trials
        for key, score in self._scores.items():
            if score.trials < 5:
                recommendations.append({
                    "type": "exploration",
                    "provider": score.provider_id,
                    "intent": score.intent,
                    "reason": f"Only {score.trials} trials, needs more data",
                })
        
        return recommendations


class ABBTestRunner:
    """
    Runs A/B tests between routing strategies.
    """
    
    def __init__(self, outcome_tracker: OutcomeTracker):
        self.outcome_tracker = outcome_tracker
        self._active_tests: Dict[str, Dict] = {}
    
    def start_test(
        self,
        test_id: str,
        provider_a: str,
        provider_b: str,
        traffic_split: float = 0.5,
        min_samples: int = 100,
    ):
        """
        Start an A/B test between two providers.
        
        Args:
            test_id: Unique test identifier
            provider_a: Control provider
            provider_b: Treatment provider
            traffic_split: Percentage to route to B (0.0-1.0)
            min_samples: Minimum samples before concluding
        """
        self._active_tests[test_id] = {
            "provider_a": provider_a,
            "provider_b": provider_b,
            "traffic_split": traffic_split,
            "min_samples": min_samples,
            "started_at": datetime.utcnow(),
            "samples_a": 0,
            "samples_b": 0,
        }
    
    def get_variant(self, test_id: str) -> Optional[str]:
        """
        Get which variant to use for a request.
        
        Returns:
            "a" or "b", or None if test not found
        """
        if test_id not in self._active_tests:
            return None
        
        test = self._active_tests[test_id]
        
        # Simple random assignment
        return "b" if random.random() < test["traffic_split"] else "a"
    
    def record_sample(self, test_id: str, variant: str):
        """Record that a sample was assigned to a variant."""
        if test_id in self._active_tests:
            if variant == "a":
                self._active_tests[test_id]["samples_a"] += 1
            else:
                self._active_tests[test_id]["samples_b"] += 1
    
    def analyze_test(self, test_id: str) -> Optional[Dict]:
        """
        Analyze A/B test results.
        
        Returns:
            Analysis results or None if insufficient data
        """
        if test_id not in self._active_tests:
            return None
        
        test = self._active_tests[test_id]
        
        # Check if we have enough samples
        if (test["samples_a"] + test["samples_b"]) < test["min_samples"]:
            return {
                "status": "running",
                "samples_a": test["samples_a"],
                "samples_b": test["samples_b"],
                "needed": test["min_samples"],
            }
        
        # Get performance for both providers
        perf_a = self.outcome_tracker.get_provider_performance(test["provider_a"])
        perf_b = self.outcome_tracker.get_provider_performance(test["provider_b"])
        
        return {
            "status": "complete",
            "provider_a": test["provider_a"],
            "provider_b": test["provider_b"],
            "performance_a": perf_a,
            "performance_b": perf_b,
            "winner": test["provider_b"] if (perf_b and perf_a and 
                perf_b.get("success_rate", 0) > perf_a.get("success_rate", 0))
                else test["provider_a"],
        }
