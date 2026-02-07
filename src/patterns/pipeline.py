"""
Pipeline pattern for sequential agent workflows.

Chains multiple agents where output of one feeds into input of next.
"""

import asyncio
from dataclasses import dataclass
from typing import Callable, List, Optional, Any, Dict
from datetime import datetime


@dataclass
class PipelineStep:
    """A single step in a pipeline."""
    name: str
    agent: Callable[[str], str]
    input_transform: Optional[Callable[[str], str]] = None
    output_transform: Optional[Callable[[str], str]] = None
    condition: Optional[Callable[[str], bool]] = None


@dataclass
class PipelineResult:
    """Result of a pipeline execution."""
    final_output: str
    intermediate_results: Dict[str, str]
    total_time_ms: int
    steps_completed: int
    steps_failed: int


class PipelinePattern:
    """
    Pipeline pattern for chained agent workflows.
    
    Example:
        pipeline = PipelinePattern()
        
        pipeline.add_step("research", research_agent)
        pipeline.add_step("outline", outline_agent)
        pipeline.add_step("write", writer_agent)
        pipeline.add_step("edit", editor_agent)
        
        result = await pipeline.execute("Write about AI safety")
    """
    
    def __init__(self):
        """Initialize empty pipeline."""
        self.steps: List[PipelineStep] = []
    
    def add_step(
        self,
        name: str,
        agent: Callable[[str], str],
        input_transform: Optional[Callable[[str], str]] = None,
        output_transform: Optional[Callable[[str], str]] = None,
        condition: Optional[Callable[[str], bool]] = None,
    ):
        """
        Add a step to the pipeline.
        
        Args:
            name: Step identifier
            agent: Agent function
            input_transform: Optional transform of input before agent
            output_transform: Optional transform of output after agent
            condition: Optional condition to skip this step
        """
        self.steps.append(PipelineStep(
            name=name,
            agent=agent,
            input_transform=input_transform,
            output_transform=output_transform,
            condition=condition,
        ))
    
    async def execute(self, initial_input: str, context: Optional[Dict] = None) -> PipelineResult:
        """
        Execute the pipeline.
        
        Args:
            initial_input: Starting input
            context: Optional shared context across steps
            
        Returns:
            PipelineResult with final output and intermediate results
        """
        import time
        start_time = time.time()
        
        current_input = initial_input
        intermediate_results: Dict[str, str] = {}
        steps_completed = 0
        steps_failed = 0
        
        shared_context = context or {}
        
        for step in self.steps:
            try:
                # Check condition
                if step.condition and not step.condition(current_input):
                    intermediate_results[step.name] = "[skipped]"
                    continue
                
                # Apply input transform
                step_input = current_input
                if step.input_transform:
                    step_input = step.input_transform(current_input)
                
                # Add context to input
                if shared_context:
                    context_str = "\n".join(f"{k}: {v}" for k, v in shared_context.items())
                    step_input = f"Context:\n{context_str}\n\nInput:\n{step_input}"
                
                # Execute agent
                output = await self._call_agent(step.agent, step_input)
                
                # Apply output transform
                if step.output_transform:
                    output = step.output_transform(output)
                
                # Store result
                intermediate_results[step.name] = output
                current_input = output
                steps_completed += 1
                
            except Exception as e:
                intermediate_results[step.name] = f"[error: {str(e)}]"
                steps_failed += 1
                # Continue with next step using previous input
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        return PipelineResult(
            final_output=current_input,
            intermediate_results=intermediate_results,
            total_time_ms=elapsed_ms,
            steps_completed=steps_completed,
            steps_failed=steps_failed,
        )
    
    async def _call_agent(self, agent: Callable[[str], str], prompt: str) -> str:
        """Call an agent function."""
        if asyncio.iscoroutinefunction(agent):
            return await agent(prompt)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, agent, prompt)


class ConditionalPipeline:
    """Pipeline with conditional branching."""
    
    def __init__(self):
        self.steps: List[PipelineStep] = []
        self.branches: Dict[str, List[PipelineStep]] = {}
    
    def add_step(self, step: PipelineStep):
        """Add a step to the main pipeline."""
        self.steps.append(step)
    
    def add_branch(self, name: str, condition: Callable[[str], bool], steps: List[PipelineStep]):
        """
        Add a conditional branch.
        
        Args:
            name: Branch name
            condition: Function to determine if branch should execute
            steps: Steps in the branch
        """
        self.branches[name] = {"condition": condition, "steps": steps}
    
    async def execute(self, initial_input: str) -> PipelineResult:
        """Execute with conditional branching."""
        import time
        start_time = time.time()
        
        current_input = initial_input
        intermediate_results = {}
        steps_completed = 0
        
        # Execute main steps
        for step in self.steps:
            output = await self._execute_step(step, current_input)
            intermediate_results[step.name] = output
            current_input = output
            steps_completed += 1
            
            # Check branches
            for branch_name, branch in self.branches.items():
                if branch["condition"](current_input):
                    branch_result = await self._execute_branch(
                        branch["steps"], current_input
                    )
                    intermediate_results.update(branch_result)
                    if branch_result:
                        current_input = list(branch_result.values())[-1]
                        steps_completed += len(branch_result)
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        return PipelineResult(
            final_output=current_input,
            intermediate_results=intermediate_results,
            total_time_ms=elapsed_ms,
            steps_completed=steps_completed,
            steps_failed=0,
        )
    
    async def _execute_step(self, step: PipelineStep, input_data: str) -> str:
        """Execute a single step."""
        step_input = input_data
        if step.input_transform:
            step_input = step.input_transform(input_data)
        
        output = await self._call_agent(step.agent, step_input)
        
        if step.output_transform:
            output = step.output_transform(output)
        
        return output
    
    async def _execute_branch(
        self,
        steps: List[PipelineStep],
        initial_input: str,
    ) -> Dict[str, str]:
        """Execute a branch of steps."""
        results = {}
        current = initial_input
        
        for step in steps:
            output = await self._execute_step(step, current)
            results[f"branch_{step.name}"] = output
            current = output
        
        return results
    
    async def _call_agent(self, agent: Callable[[str], str], prompt: str) -> str:
        """Call an agent function."""
        if asyncio.iscoroutinefunction(agent):
            return await agent(prompt)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, agent, prompt)


class ParallelPipeline:
    """Pipeline where multiple steps execute in parallel."""
    
    def __init__(self):
        self.parallel_groups: List[List[PipelineStep]] = []
    
    def add_parallel_group(self, steps: List[PipelineStep]):
        """
        Add a group of steps that execute in parallel.
        
        Args:
            steps: Steps to execute concurrently
        """
        self.parallel_groups.append(steps)
    
    async def execute(self, initial_input: str) -> PipelineResult:
        """
        Execute parallel pipeline.
        
        Each group's steps run in parallel.
        Groups run sequentially.
        """
        import time
        start_time = time.time()
        
        current_input = initial_input
        intermediate_results = {}
        steps_completed = 0
        
        for group in self.parallel_groups:
            # Execute group in parallel
            tasks = [
                self._execute_step(step, current_input)
                for step in group
            ]
            
            outputs = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for step, output in zip(group, outputs):
                if isinstance(output, Exception):
                    intermediate_results[step.name] = f"[error: {str(output)}]"
                else:
                    intermediate_results[step.name] = output
                    steps_completed += 1
            
            # Merge outputs for next group
            current_input = "\n\n".join(
                f"{step.name}:\n{intermediate_results[step.name]}"
                for step in group
                if step.name in intermediate_results
                and not intermediate_results[step.name].startswith("[error")
            )
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        return PipelineResult(
            final_output=current_input,
            intermediate_results=intermediate_results,
            total_time_ms=elapsed_ms,
            steps_completed=steps_completed,
            steps_failed=len(intermediate_results) - steps_completed,
        )
    
    async def _execute_step(self, step: PipelineStep, input_data: str) -> str:
        """Execute a single step."""
        step_input = input_data
        if step.input_transform:
            step_input = step.input_transform(input_data)
        
        if asyncio.iscoroutinefunction(step.agent):
            output = await step.agent(step_input)
        else:
            loop = asyncio.get_event_loop()
            output = await loop.run_in_executor(None, step.agent, step_input)
        
        if step.output_transform:
            output = step.output_transform(output)
        
        return output
