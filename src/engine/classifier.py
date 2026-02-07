"""
Intent classification for tasks.

Rule-based v1 implementation. Future: ML-based classifier.
"""

import re
from typing import Dict, List, Optional, Tuple

from .models import Task, TaskIntent


class IntentClassifier:
    """
    Classifies task intent based on prompt content.
    
    Uses keyword matching and pattern recognition.
    Future: Replace with fine-tuned BERT model.
    """
    
    # Intent keyword mappings
    INTENT_PATTERNS: Dict[TaskIntent, List[str]] = {
        TaskIntent.CODE_IMPLEMENTATION: [
            "implement", "write code", "create function", "build",
            "develop", "code", "script", "program",
        ],
        TaskIntent.CODE_REVIEW: [
            "review code", "code review", "refactor", "improve code",
            "optimize", "clean up code",
        ],
        TaskIntent.CODE_DEBUGGING: [
            "debug", "fix bug", "error", "exception", "traceback",
            "not working", "broken", "fails",
        ],
        TaskIntent.CODE_DOCUMENTATION: [
            "document code", "add docstring", "code comments",
            "api documentation", "inline docs",
        ],
        TaskIntent.RESEARCH: [
            "research", "investigate", "study", "analyze",
            "deep dive", "explore", "survey",
        ],
        TaskIntent.ANALYSIS: [
            "analyze", "examine", "assess", "evaluate",
            "compare", "contrast", "break down",
        ],
        TaskIntent.SYNTHESIS: [
            "synthesize", "combine", "integrate", "unify",
            "merge insights", "holistic view",
        ],
        TaskIntent.DOCUMENTATION: [
            "document", "write docs", "readme", "guide",
            "manual", "specification", "technical writing",
        ],
        TaskIntent.CREATIVE_WRITING: [
            "write story", "creative", "fiction", "poem",
            "narrative", "blog post", "article",
        ],
        TaskIntent.TECHNICAL_WRITING: [
            "technical writing", "whitepaper", "spec",
            "design doc", "architecture document",
        ],
        TaskIntent.PROBLEM_SOLVING: [
            "solve", "solution", "approach", "strategy",
            "how to", "what's the best way",
        ],
        TaskIntent.PLANNING: [
            "plan", "roadmap", "schedule", "timeline",
            "milestone", "project plan", "sprint",
        ],
        TaskIntent.DECISION_SUPPORT: [
            "decide", "choose", "select", "recommend",
            "which is better", "tradeoff", "option",
        ],
        TaskIntent.IMAGE_GENERATION: [
            "generate image", "create image", "draw",
            "image of", "picture", "illustration",
        ],
        TaskIntent.VISION_ANALYSIS: [
            "describe image", "analyze image", "what's in",
            "image analysis", "visual", "screenshot",
        ],
        TaskIntent.QUESTION_ANSWERING: [
            "what is", "how does", "why is", "explain",
            "what are", "how do", "question",
        ],
        TaskIntent.SUMMARIZATION: [
            "summarize", "tl;dr", "summary", "condense",
            "key points", "main ideas",
        ],
        TaskIntent.TRANSLATION: [
            "translate", "in spanish", "in french", "in german",
            "in chinese", "convert to",
        ],
    }
    
    def __init__(self):
        """Initialize classifier with compiled patterns."""
        self._compiled_patterns: Dict[TaskIntent, List[re.Pattern]] = {}
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        for intent, keywords in self.INTENT_PATTERNS.items():
            self._compiled_patterns[intent] = [
                re.compile(rf'\b{re.escape(kw)}\b', re.IGNORECASE)
                for kw in keywords
            ]
    
    def classify(self, task: Task) -> TaskIntent:
        """
        Classify the intent of a task.
        
        Args:
            task: The task to classify
            
        Returns:
            Classified intent
        """
        text = f"{task.system_prompt or ''} {task.prompt}".lower()
        
        # Score each intent
        scores: Dict[TaskIntent, int] = {}
        for intent, patterns in self._compiled_patterns.items():
            score = sum(1 for p in patterns if p.search(text))
            if score > 0:
                scores[intent] = score
        
        # Return highest scoring intent
        if scores:
            return max(scores, key=scores.get)
        
        return TaskIntent.UNKNOWN
    
    def classify_with_confidence(self, task: Task) -> Tuple[TaskIntent, float]:
        """
        Classify with confidence score.
        
        Returns:
            Tuple of (intent, confidence)
        """
        text = f"{task.system_prompt or ''} {task.prompt}".lower()
        
        scores: Dict[TaskIntent, int] = {}
        for intent, patterns in self._compiled_patterns.items():
            score = sum(1 for p in patterns if p.search(text))
            if score > 0:
                scores[intent] = score
        
        if not scores:
            return TaskIntent.UNKNOWN, 0.0
        
        # Calculate confidence
        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]
        total_score = sum(scores.values())
        
        confidence = best_score / total_score if total_score > 0 else 0.0
        
        # Boost confidence if score is significantly higher
        if len(scores) > 1:
            second_best = sorted(scores.values(), reverse=True)[1]
            if best_score > second_best * 2:
                confidence = min(1.0, confidence * 1.2)
        
        return best_intent, round(confidence, 2)
    
    def batch_classify(self, tasks: List[Task]) -> Dict[str, TaskIntent]:
        """
        Classify multiple tasks efficiently.
        
        Returns:
            Dictionary mapping task ID to intent
        """
        return {task.id: self.classify(task) for task in tasks}
    
    def get_explanation(self, task: Task) -> str:
        """
        Get human-readable explanation of classification.
        
        Returns:
            Explanation string
        """
        intent, confidence = self.classify_with_confidence(task)
        
        if intent == TaskIntent.UNKNOWN:
            return "Could not determine intent from prompt. Using default routing."
        
        # Find matching keywords
        text = f"{task.system_prompt or ''} {task.prompt}".lower()
        matching_keywords = []
        
        for pattern in self._compiled_patterns.get(intent, []):
            match = pattern.search(text)
            if match:
                matching_keywords.append(match.group(0))
        
        keywords_str = ", ".join(set(matching_keywords[:3]))
        
        return (
            f"Detected intent: {intent.value} "
            f"(confidence: {confidence:.0%}). "
            f"Keywords matched: {keywords_str}"
        )
