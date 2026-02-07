"""
Debate/Consensus pattern for multi-perspective analysis.

Multiple agents debate an issue, then a synthesizer reconciles their views.
"""

import asyncio
from dataclasses import dataclass
from typing import List, Callable, Optional
from enum import Enum


class Stance(Enum):
    """Stance in a debate."""
    THESIS = "thesis"           # For
    ANTITHESIS = "antithesis"   # Against
    SYNTHESIS = "synthesis"     # Reconciliation


@dataclass
class DebateArgument:
    """A single argument in the debate."""
    agent: str
    stance: Stance
    content: str
    confidence: float = 1.0


@dataclass
class DebateResult:
    """Result of a debate."""
    thesis: DebateArgument
    antithesis: DebateArgument
    synthesis: DebateArgument
    resolution: str
    confidence: float


class DebatePattern:
    """
    Debate pattern for dialectical analysis.
    
    Three agents:
    - Thesis: Argues for the proposition
    - Antithesis: Argues against
    - Synthesis: Reconciles both views
    
    Example:
        debate = DebatePattern()
        
        result = await debate.execute(
            topic="Should we use microservices?",
            thesis_agent=claude,
            antithesis_agent=kimi,
            synthesis_agent=codex,
        )
    """
    
    async def execute(
        self,
        topic: str,
        thesis_agent: Callable[[str], str],
        antithesis_agent: Callable[[str], str],
        synthesis_agent: Callable[[str, str, str], str],
        context: Optional[str] = None,
    ) -> DebateResult:
        """
        Execute debate pattern.
        
        Args:
            topic: The issue to debate
            thesis_agent: Agent arguing for
            antithesis_agent: Agent arguing against
            synthesis_agent: Agent reconciling views
            context: Optional background context
            
        Returns:
            DebateResult with all arguments and synthesis
        """
        # Prepare prompts
        base_prompt = f"Topic: {topic}"
        if context:
            base_prompt = f"Context: {context}\n\n{base_prompt}"
        
        # Execute in parallel where possible
        thesis_task = self._call_agent(
            thesis_agent,
            f"{base_prompt}\n\nArgue FOR this position. Provide strongest arguments, evidence, and benefits.",
        )
        
        antithesis_task = self._call_agent(
            antithesis_agent,
            f"{base_prompt}\n\nArgue AGAINST this position. Provide strongest counter-arguments, risks, and drawbacks.",
        )
        
        # Run thesis and antithesis in parallel
        thesis_content, antithesis_content = await asyncio.gather(
            thesis_task,
            antithesis_task,
        )
        
        thesis = DebateArgument(
            agent="thesis",
            stance=Stance.THESIS,
            content=thesis_content,
        )
        
        antithesis = DebateArgument(
            agent="antithesis",
            stance=Stance.ANTITHESIS,
            content=antithesis_content,
        )
        
        # Synthesis depends on both arguments
        synthesis_prompt = f"""Topic: {topic}

ARGUMENTS FOR:
{thesis_content}

ARGUMENTS AGAINST:
{antithesis_content}

Reconcile these views. Identify common ground, trade-offs, and provide a nuanced conclusion.
"""
        
        synthesis_content = await self._call_agent(
            synthesis_agent,
            synthesis_prompt,
        )
        
        synthesis = DebateArgument(
            agent="synthesis",
            stance=Stance.SYNTHESIS,
            content=synthesis_content,
        )
        
        # Extract resolution and confidence
        resolution = self._extract_resolution(synthesis_content)
        confidence = self._estimate_confidence(thesis, antithesis, synthesis)
        
        return DebateResult(
            thesis=thesis,
            antithesis=antithesis,
            synthesis=synthesis,
            resolution=resolution,
            confidence=confidence,
        )
    
    async def _call_agent(self, agent: Callable[[str], str], prompt: str) -> str:
        """Call an agent function."""
        if asyncio.iscoroutinefunction(agent):
            return await agent(prompt)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, agent, prompt)
    
    def _extract_resolution(self, synthesis_content: str) -> str:
        """Extract final resolution from synthesis."""
        # Simple extraction - could be more sophisticated
        lines = synthesis_content.strip().split('\n')
        
        # Look for conclusion
        for line in lines:
            lower = line.lower()
            if any(word in lower for word in ['conclusion', 'resolution', 'recommendation', 'therefore']):
                return line.strip()
        
        # Return last paragraph if no explicit conclusion
        paragraphs = synthesis_content.strip().split('\n\n')
        return paragraphs[-1][:200] if paragraphs else synthesis_content[:200]
    
    def _estimate_confidence(
        self,
        thesis: DebateArgument,
        antithesis: DebateArgument,
        synthesis: DebateArgument,
    ) -> float:
        """Estimate confidence in the synthesis."""
        # Simple heuristic - could use more sophisticated analysis
        thesis_length = len(thesis.content)
        antithesis_length = len(antithesis.content)
        synthesis_length = len(synthesis.content)
        
        # Confidence higher when synthesis addresses both sides thoroughly
        avg_input_length = (thesis_length + antithesis_length) / 2
        
        if synthesis_length < avg_input_length * 0.5:
            return 0.6  # Synthesis may be too brief
        elif synthesis_length > avg_input_length * 2:
            return 0.8  # Thorough synthesis
        else:
            return 0.75


class ConsensusBuilder:
    """Build consensus among multiple agents."""
    
    def __init__(self, agents: List[Callable[[str], str]]):
        """
        Initialize with multiple agents.
        
        Args:
            agents: List of agent functions that take a prompt and return a response
        """
        self.agents = agents
    
    async def reach_consensus(
        self,
        topic: str,
        rounds: int = 2,
    ) -> str:
        """
        Have agents discuss until consensus emerges.
        
        Args:
            topic: Topic to discuss
            rounds: Number of discussion rounds
            
        Returns:
            Final consensus statement
        """
        current_discussion = f"Topic: {topic}\n\nInitial thoughts:\n"
        
        for round_num in range(rounds):
            round_responses = []
            
            for i, agent in enumerate(self.agents):
                prompt = f"""Round {round_num + 1}

Discussion so far:
{current_discussion}

Your turn to contribute. Consider previous points and refine your position.
"""
                response = await self._call_agent(agent, prompt)
                round_responses.append(f"Agent {i + 1}: {response}")
            
            current_discussion += "\n\n".join(round_responses)
        
        # Final consensus
        final_prompt = f"""Final Round - Consensus

Full discussion:
{current_discussion}

Based on this discussion, provide a final consensus statement that all parties could agree with.
"""
        
        # Use first agent for final synthesis
        consensus = await self._call_agent(self.agents[0], final_prompt)
        
        return consensus
    
    async def _call_agent(self, agent: Callable[[str], str], prompt: str) -> str:
        """Call an agent function."""
        if asyncio.iscoroutinefunction(agent):
            return await agent(prompt)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, agent, prompt)
