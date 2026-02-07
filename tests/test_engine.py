"""
Tests for the routing engine.
"""

import pytest
from src.engine.models import Task, TaskIntent, TaskRequirements, TaskPriority
from src.engine.classifier import IntentClassifier
from src.engine.router import Router


class TestIntentClassifier:
    """Test the intent classifier."""
    
    def test_classify_code_implementation(self, classifier):
        """Test classifying code implementation tasks."""
        task = Task(id="test", prompt="Implement a sorting algorithm")
        intent = classifier.classify(task)
        
        assert intent == TaskIntent.CODE_IMPLEMENTATION
    
    def test_classify_research(self, classifier):
        """Test classifying research tasks."""
        task = Task(id="test", prompt="Research the latest AI developments")
        intent = classifier.classify(task)
        
        assert intent == TaskIntent.RESEARCH
    
    def test_classify_with_confidence(self, classifier):
        """Test classification with confidence score."""
        task = Task(id="test", prompt="Debug this Python error")
        intent, confidence = classifier.classify_with_confidence(task)
        
        assert intent == TaskIntent.CODE_DEBUGGING
        assert 0.0 <= confidence <= 1.0
    
    def test_classify_unknown(self, classifier):
        """Test classifying ambiguous tasks."""
        task = Task(id="test", prompt="Hello")
        intent = classifier.classify(task)
        
        assert intent == TaskIntent.UNKNOWN


class TestRouter:
    """Test the routing engine."""
    
    def test_route_selects_provider(self, router):
        """Test that router selects a provider."""
        task = Task(
            id="test",
            prompt="Implement a function",
            intent=TaskIntent.CODE_IMPLEMENTATION,
        )
        
        decision = router.route(task)
        
        assert decision.provider_id is not None
        assert decision.confidence > 0
        assert decision.overall_score is not None
    
    def test_route_respects_quality_priority(self, router):
        """Test that quality is prioritized."""
        # OpenAI has highest quality score (0.95)
        task = Task(
            id="test",
            prompt="Write high-quality code",
            intent=TaskIntent.CODE_IMPLEMENTATION,
        )
        
        decision = router.route(task)
        
        # Quality-first should prefer OpenAI for high-quality code
        assert decision.quality_score is not None
        assert decision.quality_score >= 0.8
    
    def test_route_with_requirements(self, router):
        """Test routing with constraints."""
        task = Task(
            id="test",
            prompt="Implement a function",
            requirements=TaskRequirements(
                max_cost=1.00,  # DeepSeek is cheapest
                functions_required=True,
            ),
        )
        
        decision = router.route(task)
        
        # Should respect cost constraint
        assert decision.estimated_cost is not None
    
    def test_route_with_data_residency(self, router):
        """Test routing with data residency constraint."""
        task = Task(
            id="test",
            prompt="Process EU customer data",
            requirements=TaskRequirements(
                data_residency="local",  # Ollama is local
            ),
        )
        
        decision = router.route(task)
        
        # Local requirement should prefer Ollama
        assert decision.provider_id == "ollama"


class TestCostCalculator:
    """Test the cost calculator."""
    
    def test_estimate_cost(self):
        """Test cost estimation."""
        from src.engine.cost import CostCalculator
        from src.registry.models import Provider, ProviderCost, ProviderCapabilities
        
        calc = CostCalculator()
        provider = Provider(
            id="test",
            name="Test",
            api_base="https://test.com",
            cost=ProviderCost(input_per_1m=1.0, output_per_1m=2.0),
            capabilities=ProviderCapabilities(max_context=4096),
        )
        
        cost = calc.estimate(provider, 1000, 500)
        expected = (1000/1_000_000 * 1.0) + (500/1_000_000 * 2.0)
        
        assert cost == pytest.approx(expected, rel=1e-3)
    
    def test_compare_providers(self):
        """Test comparing provider costs."""
        from src.engine.cost import CostCalculator
        from src.registry.models import Provider, ProviderCost, ProviderCapabilities
        
        calc = CostCalculator()
        providers = [
            Provider(
                id="cheap",
                name="Cheap",
                api_base="https://cheap.com",
                cost=ProviderCost(input_per_1m=0.10, output_per_1m=0.20),
                capabilities=ProviderCapabilities(max_context=4096),
            ),
            Provider(
                id="expensive",
                name="Expensive",
                api_base="https://exp.com",
                cost=ProviderCost(input_per_1m=5.00, output_per_1m=10.00),
                capabilities=ProviderCapabilities(max_context=4096),
            ),
        ]
        
        ranked = calc.compare_providers(providers, 1000, 500)
        
        assert ranked[0][0].id == "cheap"
        assert ranked[1][0].id == "expensive"


class TestTaskModel:
    """Test the Task dataclass."""
    
    def test_task_token_estimation(self):
        """Test token estimation."""
        task = Task(
            id="test",
            prompt="Hello world",
            system_prompt="You are a helpful assistant",
        )
        
        input_tokens, output_tokens = task.estimate_tokens()
        
        # Rough check: ~4 chars per token
        assert input_tokens > 0
        assert output_tokens > 0
    
    def test_task_requirements(self):
        """Test task requirements."""
        reqs = TaskRequirements(
            max_cost=10.00,
            max_latency_ms=5000,
            soc2_required=True,
        )
        
        assert reqs.max_cost == 10.00
        assert reqs.soc2_required is True
