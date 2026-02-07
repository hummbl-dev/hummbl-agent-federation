"""
Core data models for the routing engine.

Defines Task, RoutingDecision, and related structures.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Any


class TaskIntent(Enum):
    """Classification of task intent for routing decisions."""
    # Code tasks
    CODE_IMPLEMENTATION = "code_implementation"
    CODE_REVIEW = "code_review"
    CODE_DEBUGGING = "code_debugging"
    CODE_DOCUMENTATION = "code_documentation"
    
    # Analysis tasks
    RESEARCH = "research"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    
    # Writing tasks
    DOCUMENTATION = "documentation"
    CREATIVE_WRITING = "creative_writing"
    TECHNICAL_WRITING = "technical_writing"
    
    # Reasoning tasks
    PROBLEM_SOLVING = "problem_solving"
    PLANNING = "planning"
    DECISION_SUPPORT = "decision_support"
    
    # Multi-modal
    IMAGE_GENERATION = "image_generation"
    VISION_ANALYSIS = "vision_analysis"
    
    # Utility
    QUESTION_ANSWERING = "question_answering"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    
    # Unknown/fallback
    UNKNOWN = "unknown"


class TaskPriority(Enum):
    """Task priority for queue management."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class TaskRequirements:
    """
    Constraints and requirements for task execution.
    
    Used by the router to filter and score providers.
    """
    # Cost constraints
    max_cost: Optional[float] = None          # Maximum USD cost
    budget_tier: Optional[str] = None          # "free", "low", "medium", "premium"
    
    # Latency constraints
    max_latency_ms: Optional[int] = None      # Maximum acceptable latency
    streaming_required: bool = False           # Must support streaming
    
    # Quality constraints
    min_quality_score: Optional[float] = None  # 0.0 - 1.0
    specialties_required: List[str] = field(default_factory=list)
    
    # Context constraints
    min_context: Optional[int] = None         # Minimum context window
    
    # Compliance constraints
    data_residency: Optional[str] = None      # "us", "eu", "apac", "local"
    soc2_required: bool = False
    gdpr_required: bool = False
    hipaa_required: bool = False
    pii_handling: Optional[str] = None        # "exclude", "encrypt", "standard"
    
    # Feature requirements
    functions_required: bool = False
    vision_required: bool = False
    json_mode_required: bool = False
    
    # Governance
    governance_policy: Optional[str] = None    # Policy ID to enforce


@dataclass
class Task:
    """
    A task to be routed to a provider.
    
    This is the primary input to the routing engine.
    """
    # Identification
    id: str                                    # Unique task ID
    session_id: Optional[str] = None          # Grouping ID for related tasks
    
    # Content
    prompt: str = ""                          # The actual task content
    system_prompt: Optional[str] = None       # System context
    
    # Classification (filled by classifier)
    intent: TaskIntent = TaskIntent.UNKNOWN
    estimated_input_tokens: Optional[int] = None
    estimated_output_tokens: Optional[int] = None
    
    # Requirements (user-specified constraints)
    requirements: TaskRequirements = field(default_factory=TaskRequirements)
    priority: TaskPriority = TaskPriority.NORMAL
    
    # Metadata
    tenant_id: Optional[str] = None           # For multi-tenant deployments
    user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    
    # Context for routing
    context: Dict[str, Any] = field(default_factory=dict)
    
    def estimate_tokens(self) -> tuple[int, int]:
        """Estimate input/output tokens if not provided."""
        if self.estimated_input_tokens and self.estimated_output_tokens:
            return (self.estimated_input_tokens, self.estimated_output_tokens)
        
        # Rough heuristic: 1 token ≈ 4 characters for English
        input_chars = len(self.prompt) + len(self.system_prompt or "")
        estimated_input = input_chars // 4
        
        # Estimate output based on intent
        output_multipliers = {
            TaskIntent.CODE_IMPLEMENTATION: 3.0,
            TaskIntent.RESEARCH: 4.0,
            TaskIntent.DOCUMENTATION: 3.0,
            TaskIntent.SUMMARIZATION: 0.5,
            TaskIntent.QUESTION_ANSWERING: 1.0,
        }
        multiplier = output_multipliers.get(self.intent, 2.0)
        estimated_output = int(estimated_input * multiplier)
        
        return (estimated_input, estimated_output)


@dataclass
class RoutingDecision:
    """
    The output of the routing engine.
    
    Contains the selected provider and metadata about the decision.
    """
    # Selected provider
    provider_id: str
    model: Optional[str] = None
    
    # Decision metadata
    confidence: float = 0.0                    # 0.0 - 1.0
    reasoning: str = ""                        # Human-readable explanation
    
    # Scores that led to decision
    quality_score: Optional[float] = None
    speed_score: Optional[float] = None
    cost_score: Optional[float] = None
    reliability_score: Optional[float] = None
    overall_score: Optional[float] = None
    
    # Alternative providers considered
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    
    # Cost estimation
    estimated_cost: Optional[float] = None
    estimated_latency_ms: Optional[int] = None
    
    # Execution metadata
    decision_time_ms: Optional[int] = None
    routed_at: datetime = field(default_factory=datetime.utcnow)
    
    # Tracking
    task_id: Optional[str] = None
    executed: bool = False
    outcome_recorded: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "provider_id": self.provider_id,
            "model": self.model,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "estimated_cost": self.estimated_cost,
            "estimated_latency_ms": self.estimated_latency_ms,
            "overall_score": self.overall_score,
            "alternatives": self.alternatives,
            "routed_at": self.routed_at.isoformat(),
        }
