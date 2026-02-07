"""
Core routing engine for the federation.

Routes tasks to optimal providers based on quality, speed, cost, and reliability.
"""

import time
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any

from ..registry.models import Provider, ProviderStatus
from ..registry.store import RegistryStore
from .models import Task, TaskIntent, TaskRequirements, RoutingDecision
from .classifier import IntentClassifier
from .cost import CostCalculator


@dataclass
class ScoredProvider:
    """Internal structure for ranking providers."""
    provider: Provider
    quality_score: float
    speed_score: float
    cost_score: float
    reliability_score: float
    overall_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider_id": self.provider.id,
            "quality": round(self.quality_score, 3),
            "speed": round(self.speed_score, 3),
            "cost": round(self.cost_score, 3),
            "reliability": round(self.reliability_score, 3),
            "overall": round(self.overall_score, 3),
        }


class Router:
    """
    Federation routing engine.
    
    Implements quality-first routing with configurable weights:
    - Quality (0.5): Output quality, correctness
    - Speed (0.3): Latency, throughput
    - Cost (0.1): Price per token
    - Reliability (0.1): Uptime, error rates
    """
    
    # Weights as specified by Reuben: Quality > Speed > Cost > Reliability
    WEIGHT_QUALITY = 0.50
    WEIGHT_SPEED = 0.30
    WEIGHT_COST = 0.10
    WEIGHT_RELIABILITY = 0.10
    
    # A/B testing: percentage of traffic to explore
    EXPLORATION_RATE = 0.05  # 5% for enterprise stability
    
    def __init__(
        self,
        store: RegistryStore,
        classifier: Optional[IntentClassifier] = None,
        cost_calculator: Optional[CostCalculator] = None,
    ):
        """
        Initialize router.
        
        Args:
            store: Provider registry store
            classifier: Intent classifier (default: rule-based)
            cost_calculator: Cost calculator (default: standard)
        """
        self.store = store
        self.classifier = classifier or IntentClassifier()
        self.cost_calc = cost_calculator or CostCalculator()
    
    def route(self, task: Task) -> RoutingDecision:
        """
        Route a task to the optimal provider.
        
        Args:
            task: The task to route
            
        Returns:
            RoutingDecision with selected provider and metadata
        """
        start_time = time.time()
        
        # Step 1: Classify intent if not already done
        if task.intent is None or task.intent.value == "unknown":
            task.intent, confidence = self.classifier.classify_with_confidence(task)
        
        # Step 2: Get candidate providers
        candidates = self._get_candidates(task)
        
        if not candidates:
            return self._create_fallback_decision(task, "No providers available")
        
        # Step 3: Score candidates
        scored = self._score_providers(candidates, task)
        
        # Step 4: Select provider
        selected = self._select_provider(scored, task)
        
        # Step 5: Build decision
        decision_time_ms = int((time.time() - start_time) * 1000)
        decision = self._build_decision(selected, scored, task, decision_time_ms)
        
        return decision
    
    def _get_candidates(self, task: Task) -> List[Provider]:
        """
        Filter providers based on task requirements.
        
        Args:
            task: The task to route
            
        Returns:
            List of eligible providers
        """
        all_providers = self.store.get_all_providers()
        candidates = []
        
        for provider in all_providers.values():
            # Basic health check
            if not provider.is_healthy:
                continue
            
            # Check requirements
            if not self._meets_requirements(provider, task.requirements):
                continue
            
            # Check governance policy
            if task.requirements.governance_policy:
                if not self._check_governance(provider, task.requirements.governance_policy):
                    continue
            
            candidates.append(provider)
        
        return candidates
    
    def _meets_requirements(self, provider: Provider, reqs: TaskRequirements) -> bool:
        """Check if provider meets task requirements."""
        caps = provider.capabilities
        
        # Context window
        if reqs.min_context and caps.max_context < reqs.min_context:
            return False
        
        # Features
        if reqs.functions_required and not caps.supports_functions:
            return False
        if reqs.vision_required and not caps.supports_vision:
            return False
        if reqs.json_mode_required and not caps.supports_json_mode:
            return False
        if reqs.streaming_required and not caps.supports_streaming:
            return False
        
        # Compliance
        if reqs.soc2_required and not caps.soc2_compliant:
            return False
        if reqs.gdpr_required and not caps.gdpr_compliant:
            return False
        if reqs.hipaa_required and not caps.hipaa_compliant:
            return False
        
        # Data residency
        if reqs.data_residency:
            if reqs.data_residency not in caps.data_residency:
                # Special case: "local" means any local/self-hosted
                if reqs.data_residency == "local" and caps.data_residency == {"local"}:
                    pass
                else:
                    return False
        
        # Specialties
        if reqs.specialties_required:
            if not any(s in caps.specialties for s in reqs.specialties_required):
                return False
        
        return True
    
    def _check_governance(self, provider: Provider, policy_id: str) -> bool:
        """Check if provider complies with governance policy."""
        # TODO: Integrate with governance policy engine
        # For now, basic compliance checks
        return True
    
    def _score_providers(
        self, 
        providers: List[Provider], 
        task: Task
    ) -> List[ScoredProvider]:
        """
        Score providers across quality, speed, cost, reliability.
        
        Args:
            providers: List of candidate providers
            task: The task being routed
            
        Returns:
            List of scored providers
        """
        scored = []
        
        for provider in providers:
            # Quality score (0-1)
            quality = self._calc_quality_score(provider, task)
            
            # Speed score (0-1)
            speed = self._calc_speed_score(provider, task)
            
            # Cost score (0-1, higher = more cost-efficient)
            cost = self._calc_cost_score(provider, task)
            
            # Reliability score (0-1)
            reliability = self._calc_reliability_score(provider)
            
            # Weighted overall score
            overall = (
                quality * self.WEIGHT_QUALITY +
                speed * self.WEIGHT_SPEED +
                cost * self.WEIGHT_COST +
                reliability * self.WEIGHT_RELIABILITY
            )
            
            scored.append(ScoredProvider(
                provider=provider,
                quality_score=quality,
                speed_score=speed,
                cost_score=cost,
                reliability_score=reliability,
                overall_score=overall,
            ))
        
        # Sort by overall score
        scored.sort(key=lambda x: x.overall_score, reverse=True)
        
        return scored
    
    def _calc_quality_score(self, provider: Provider, task: Task) -> float:
        """Calculate quality score for provider-task match."""
        # Base quality from provider config
        base = provider.quality_score or 0.8
        
        # Intent-specialty match
        caps = provider.capabilities
        intent_specialty_map = {
            TaskIntent.CODE_IMPLEMENTATION: "code",
            TaskIntent.CODE_REVIEW: "code",
            TaskIntent.RESEARCH: "reasoning",
            TaskIntent.ANALYSIS: "reasoning",
            TaskIntent.DOCUMENTATION: "documentation",
        }
        
        expected_specialty = intent_specialty_map.get(task.intent)
        if expected_specialty and expected_specialty in caps.specialties:
            base += 0.05
        
        # Cap at 1.0
        return min(1.0, base)
    
    def _calc_speed_score(self, provider: Provider, task: Task) -> float:
        """Calculate speed score based on latency."""
        caps = provider.capabilities
        
        if caps.typical_latency_ms:
            # Normalize: <300ms = 1.0, >5000ms = 0.0
            latency = caps.typical_latency_ms
            if latency < 300:
                return 1.0
            elif latency > 5000:
                return 0.3
            else:
                # Linear interpolation
                return 1.0 - (latency - 300) / 4700
        
        # Default: assume average
        return 0.6
    
    def _calc_cost_score(self, provider: Provider, task: Task) -> float:
        """Calculate cost efficiency score."""
        cost = provider.cost
        
        if cost.input_per_1m == 0:
            # Free (ollama/local)
            return 1.0
        
        # Normalize against typical range ($0.10 - $10.00 per 1M tokens)
        avg_cost = (cost.input_per_1m + cost.output_per_1m) / 2
        
        if avg_cost < 0.50:
            return 1.0
        elif avg_cost > 10.0:
            return 0.2
        else:
            # Log scale for better differentiation
            import math
            return 1.0 - (math.log10(avg_cost) - math.log10(0.5)) / 2
    
    def _calc_reliability_score(self, provider: Provider) -> float:
        """Calculate reliability score based on health metrics."""
        # Configured reliability
        base = provider.reliability_score or 0.95
        
        # Adjust based on recent health
        health = provider.health
        if health.error_rate_24h:
            base -= health.error_rate_24h
        
        if health.status == ProviderStatus.DEGRADED:
            base -= 0.1
        elif health.status == ProviderStatus.UNHEALTHY:
            base = 0.0
        
        return max(0.0, min(1.0, base))
    
    def _select_provider(
        self, 
        scored: List[ScoredProvider], 
        task: Task
    ) -> ScoredProvider:
        """
        Select provider from scored list.
        
        With EXPLORATION_RATE probability, pick a non-top provider
        to gather learning data.
        """
        if not scored:
            raise ValueError("No scored providers")
        
        # Always pick best if only one option
        if len(scored) == 1:
            return scored[0]
        
        # Exploration: occasionally try alternatives
        if random.random() < self.EXPLORATION_RATE and len(scored) > 1:
            # Pick randomly from top 3 (not just the best)
            top_n = min(3, len(scored))
            return random.choice(scored[:top_n])
        
        # Exploitation: pick the best
        return scored[0]
    
    def _build_decision(
        self,
        selected: ScoredProvider,
        all_scored: List[ScoredProvider],
        task: Task,
        decision_time_ms: int,
    ) -> RoutingDecision:
        """Build routing decision from selection."""
        # Estimate cost and latency
        input_tokens, output_tokens = task.estimate_tokens()
        estimated_cost = selected.provider.cost.estimate(input_tokens, output_tokens)
        estimated_latency = selected.provider.capabilities.typical_latency_ms or 1500
        
        # Build alternatives list (top 3, excluding selected)
        alternatives = [
            s.to_dict() for s in all_scored 
            if s.provider.id != selected.provider.id
        ][:3]
        
        # Generate reasoning
        reasoning = self._generate_reasoning(selected, task)
        
        return RoutingDecision(
            provider_id=selected.provider.id,
            model=selected.provider.models[0] if selected.provider.models else None,
            confidence=selected.overall_score,
            reasoning=reasoning,
            quality_score=selected.quality_score,
            speed_score=selected.speed_score,
            cost_score=selected.cost_score,
            reliability_score=selected.reliability_score,
            overall_score=selected.overall_score,
            alternatives=alternatives,
            estimated_cost=estimated_cost,
            estimated_latency_ms=estimated_latency,
            decision_time_ms=decision_time_ms,
            task_id=task.id,
        )
    
    def _generate_reasoning(self, selected: ScoredProvider, task: Task) -> str:
        """Generate human-readable explanation."""
        provider = selected.provider
        reasons = []
        
        if selected.quality_score > 0.9:
            reasons.append("highest quality output")
        if selected.speed_score > 0.8:
            reasons.append("low latency")
        if selected.cost_score > 0.9:
            reasons.append("cost efficiency")
        if selected.reliability_score > 0.95:
            reasons.append("high reliability")
        
        if task.intent.value != "unknown":
            reasons.append(f"specialization in {task.intent.value}")
        
        if not reasons:
            reasons.append("best overall match")
        
        return (
            f"Selected {provider.name} ({provider.emoji}) for "
            f"{', '.join(reasons)}. "
            f"Quality: {selected.quality_score:.0%}, "
            f"Speed: {selected.speed_score:.0%}, "
            f"Cost: {selected.cost_score:.0%}"
        )
    
    def _create_fallback_decision(
        self, 
        task: Task, 
        reason: str
    ) -> RoutingDecision:
        """Create a fallback decision when routing fails."""
        return RoutingDecision(
            provider_id="ollama",  # Default to local
            confidence=0.0,
            reasoning=f"Fallback to local provider. {reason}",
            estimated_cost=0.0,
            estimated_latency_ms=100,
            task_id=task.id,
        )
