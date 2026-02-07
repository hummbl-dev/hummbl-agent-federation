"""
Cost calculation and optimization for the federation.

Tracks spending, estimates costs, and optimizes for budget constraints.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..registry.models import Provider


@dataclass
class BudgetAlert:
    """Alert when spending thresholds are breached."""
    level: str  # "warning", "critical"
    message: str
    current_spend: float
    threshold: float
    period: str  # "daily", "monthly"


class CostCalculator:
    """
    Calculates and tracks costs across the federation.
    
    Features:
    - Token-based cost estimation
    - Budget tracking and alerts
    - Cost optimization recommendations
    """
    
    def __init__(self):
        """Initialize cost calculator."""
        self._spending_cache: Dict[str, Dict[str, float]] = {}
    
    def estimate(
        self,
        provider: Provider,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """
        Estimate cost for a request.
        
        Args:
            provider: The provider to use
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        return provider.cost.estimate(input_tokens, output_tokens)
    
    def estimate_task(
        self,
        provider: Provider,
        input_text: str,
        output_text: Optional[str] = None,
    ) -> Tuple[float, int, int]:
        """
        Estimate cost from text (auto-tokenize).
        
        Returns:
            Tuple of (cost, input_tokens, output_tokens)
        """
        # Rough tokenization: 1 token ≈ 4 characters
        input_tokens = len(input_text) // 4
        
        if output_text:
            output_tokens = len(output_text) // 4
        else:
            # Estimate output as 2x input if not provided
            output_tokens = input_tokens * 2
        
        cost = self.estimate(provider, input_tokens, output_tokens)
        
        return (cost, input_tokens, output_tokens)
    
    def compare_providers(
        self,
        providers: List[Provider],
        input_tokens: int,
        output_tokens: int,
    ) -> List[Tuple[Provider, float]]:
        """
        Compare costs across multiple providers.
        
        Returns:
            List of (provider, cost) sorted by cost ascending
        """
        comparisons = []
        for provider in providers:
            cost = self.estimate(provider, input_tokens, output_tokens)
            comparisons.append((provider, cost))
        
        # Sort by cost
        comparisons.sort(key=lambda x: x[1])
        
        return comparisons
    
    def get_cheapest(
        self,
        providers: List[Provider],
        input_tokens: int,
        output_tokens: int,
    ) -> Optional[Tuple[Provider, float]]:
        """Get the cheapest provider for a given token count."""
        comparisons = self.compare_providers(providers, input_tokens, output_tokens)
        return comparisons[0] if comparisons else None
    
    def calculate_savings(
        self,
        actual_cost: float,
        baseline_cost: float,
    ) -> Dict[str, float]:
        """
        Calculate cost savings vs baseline (e.g., always using GPT-4).
        
        Returns:
            Dictionary with savings metrics
        """
        absolute_savings = baseline_cost - actual_cost
        percentage_savings = (absolute_savings / baseline_cost * 100) if baseline_cost > 0 else 0
        
        return {
            "actual_cost": round(actual_cost, 4),
            "baseline_cost": round(baseline_cost, 4),
            "absolute_savings": round(absolute_savings, 4),
            "percentage_savings": round(percentage_savings, 2),
        }
    
    def track_spend(
        self,
        tenant_id: str,
        provider_id: str,
        cost: float,
        timestamp: Optional[datetime] = None,
    ):
        """
        Track spending for budget monitoring.
        
        Args:
            tenant_id: The tenant/org making the request
            provider_id: The provider used
            cost: The actual cost incurred
            timestamp: When the spend occurred
        """
        timestamp = timestamp or datetime.utcnow()
        
        # Initialize tenant tracking
        if tenant_id not in self._spending_cache:
            self._spending_cache[tenant_id] = {
                "daily": {},
                "monthly": {},
            }
        
        tenant_cache = self._spending_cache[tenant_id]
        
        # Track by day
        day_key = timestamp.strftime("%Y-%m-%d")
        if day_key not in tenant_cache["daily"]:
            tenant_cache["daily"][day_key] = 0.0
        tenant_cache["daily"][day_key] += cost
        
        # Track by month
        month_key = timestamp.strftime("%Y-%m")
        if month_key not in tenant_cache["monthly"]:
            tenant_cache["monthly"][month_key] = 0.0
        tenant_cache["monthly"][month_key] += cost
    
    def get_spend(
        self,
        tenant_id: str,
        period: str = "daily",
        date: Optional[str] = None,
    ) -> float:
        """
        Get spending for a tenant in a period.
        
        Args:
            tenant_id: The tenant to check
            period: "daily" or "monthly"
            date: Specific date (default: today/this month)
            
        Returns:
            Total spend for the period
        """
        if tenant_id not in self._spending_cache:
            return 0.0
        
        tenant_cache = self._spending_cache[tenant_id]
        
        if date is None:
            if period == "daily":
                date = datetime.utcnow().strftime("%Y-%m-%d")
            else:
                date = datetime.utcnow().strftime("%Y-%m")
        
        return tenant_cache.get(period, {}).get(date, 0.0)
    
    def check_budget(
        self,
        tenant_id: str,
        daily_limit: Optional[float] = None,
        monthly_limit: Optional[float] = None,
    ) -> List[BudgetAlert]:
        """
        Check if spending is approaching or exceeding limits.
        
        Returns:
            List of budget alerts (empty if all good)
        """
        alerts = []
        
        # Check daily limit
        if daily_limit:
            daily_spend = self.get_spend(tenant_id, "daily")
            daily_pct = (daily_spend / daily_limit) * 100
            
            if daily_spend >= daily_limit:
                alerts.append(BudgetAlert(
                    level="critical",
                    message=f"Daily budget exceeded: ${daily_spend:.2f} / ${daily_limit:.2f}",
                    current_spend=daily_spend,
                    threshold=daily_limit,
                    period="daily",
                ))
            elif daily_pct >= 80:
                alerts.append(BudgetAlert(
                    level="warning",
                    message=f"Daily budget at {daily_pct:.0f}%: ${daily_spend:.2f} / ${daily_limit:.2f}",
                    current_spend=daily_spend,
                    threshold=daily_limit,
                    period="daily",
                ))
        
        # Check monthly limit
        if monthly_limit:
            monthly_spend = self.get_spend(tenant_id, "monthly")
            monthly_pct = (monthly_spend / monthly_limit) * 100
            
            if monthly_spend >= monthly_limit:
                alerts.append(BudgetAlert(
                    level="critical",
                    message=f"Monthly budget exceeded: ${monthly_spend:.2f} / ${monthly_limit:.2f}",
                    current_spend=monthly_spend,
                    threshold=monthly_limit,
                    period="monthly",
                ))
            elif monthly_pct >= 80:
                alerts.append(BudgetAlert(
                    level="warning",
                    message=f"Monthly budget at {monthly_pct:.0f}%: ${monthly_spend:.2f} / ${monthly_limit:.2f}",
                    current_spend=monthly_spend,
                    threshold=monthly_limit,
                    period="monthly",
                ))
        
        return alerts
    
    def recommend_optimization(
        self,
        providers: List[Provider],
        input_tokens: int,
        output_tokens: int,
        min_quality: float = 0.7,
    ) -> Dict[str, any]:
        """
        Recommend cost optimization strategies.
        
        Returns:
            Dictionary with recommendations
        """
        # Get cost ranking
        ranked = self.compare_providers(providers, input_tokens, output_tokens)
        
        # Filter by quality
        quality_providers = [
            (p, c) for p, c in ranked 
            if (p.quality_score or 0.8) >= min_quality
        ]
        
        if not quality_providers:
            return {
                "recommendation": "No providers meet quality threshold",
                "best_quality": ranked[0][0].id if ranked else None,
            }
        
        cheapest = quality_providers[0]
        premium = ranked[-1]  # Most expensive
        
        savings = self.calculate_savings(
            cheapest[1],
            premium[1] if premium else cheapest[1],
        )
        
        return {
            "cheapest_provider": cheapest[0].id,
            "cheapest_cost": round(cheapest[1], 4),
            "premium_provider": premium[0].id if premium else None,
            "premium_cost": round(premium[1], 4) if premium else None,
            "savings": savings,
            "recommendation": f"Use {cheapest[0].name} to save {savings['percentage_savings']:.0f}%",
        }
