"""
MapReduce pattern for parallel task execution.

Splits a large task into subtasks, executes in parallel, then aggregates results.
"""

import asyncio
from dataclasses import dataclass
from typing import Callable, List, TypeVar, Generic, Any
from concurrent.futures import ThreadPoolExecutor

T = TypeVar('T')
R = TypeVar('R')


@dataclass
class MapReduceResult:
    """Result of a MapReduce operation."""
    results: List[Any]
    errors: List[Exception]
    total_time_ms: int
    subtasks_completed: int
    subtasks_failed: int


class MapReducePattern:
    """
    MapReduce pattern for parallel LLM operations.
    
    Example:
        # Analyze 10 documents in parallel
        pattern = MapReducePattern(max_workers=5)
        
        def map_fn(doc):
            return llm.summarize(doc)
        
        def reduce_fn(summaries):
            return llm.synthesize(summaries)
        
        result = await pattern.execute(
            items=documents,
            map_fn=map_fn,
            reduce_fn=reduce_fn,
        )
    """
    
    def __init__(self, max_workers: int = 5):
        """
        Initialize MapReduce pattern.
        
        Args:
            max_workers: Maximum parallel subtasks
        """
        self.max_workers = max_workers
    
    async def execute(
        self,
        items: List[T],
        map_fn: Callable[[T], R],
        reduce_fn: Optional[Callable[[List[R]], Any]] = None,
    ) -> MapReduceResult:
        """
        Execute MapReduce pattern.
        
        Args:
            items: Items to process
            map_fn: Function to apply to each item
            reduce_fn: Optional function to aggregate results
            
        Returns:
            MapReduceResult with results and metadata
        """
        import time
        start_time = time.time()
        
        # Map phase: Process items in parallel
        tasks = [self._safe_map(map_fn, item) for item in items]
        
        # Execute with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def run_with_limit(task):
            async with semaphore:
                return await task
        
        results = await asyncio.gather(
            *[run_with_limit(task) for task in tasks],
            return_exceptions=True
        )
        
        # Separate successes and failures
        successes = []
        errors = []
        
        for result in results:
            if isinstance(result, Exception):
                errors.append(result)
            else:
                successes.append(result)
        
        # Reduce phase: Aggregate if reduce_fn provided
        final_result = successes
        if reduce_fn and successes:
            try:
                final_result = reduce_fn(successes)
            except Exception as e:
                errors.append(e)
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        return MapReduceResult(
            results=final_result if not isinstance(final_result, list) else final_result,
            errors=errors,
            total_time_ms=elapsed_ms,
            subtasks_completed=len(successes),
            subtasks_failed=len(errors),
        )
    
    async def _safe_map(self, map_fn: Callable[[T], R], item: T):
        """Execute map function with error handling."""
        try:
            if asyncio.iscoroutinefunction(map_fn):
                return await map_fn(item)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, map_fn, item)
        except Exception as e:
            return e


class BatchProcessor:
    """Helper for batch processing with MapReduce."""
    
    def __init__(self, pattern: MapReducePattern, batch_size: int = 10):
        self.pattern = pattern
        self.batch_size = batch_size
    
    async def process(
        self,
        items: List[T],
        process_fn: Callable[[List[T]], List[R]],
    ) -> MapReduceResult:
        """
        Process items in batches.
        
        Args:
            items: Items to process
            process_fn: Function that processes a batch
            
        Returns:
            Combined results
        """
        # Split into batches
        batches = [
            items[i:i + self.batch_size]
            for i in range(0, len(items), self.batch_size)
        ]
        
        # Process each batch
        return await self.pattern.execute(
            items=batches,
            map_fn=process_fn,
            reduce_fn=lambda results: [item for batch in results for item in batch],
        )
