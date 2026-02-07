"""
Task routing commands.
"""

from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.panel import Panel

from ..registry.loader import RegistryLoader
from ..registry.store import create_store
from ..engine.router import Router
from ..engine.models import Task, TaskRequirements, TaskPriority

app = typer.Typer(help="Route tasks to providers")
console = Console()


def _get_router(config_path: Optional[Path] = None) -> Router:
    """Get configured router."""
    path = config_path or Path("config")
    loader = RegistryLoader(path)
    store = create_store("sqlite")
    
    # Load default providers into store
    providers = loader.load_defaults()
    for provider in providers.values():
        store.save_provider(provider)
    
    return Router(store)


@app.command()
def task(
    prompt: str = typer.Argument(..., help="The task to route"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show routing without executing"),
    max_cost: Optional[float] = typer.Option(None, "--max-cost", help="Maximum cost in USD"),
    max_latency: Optional[int] = typer.Option(None, "--max-latency", help="Maximum latency in ms"),
    require_functions: bool = typer.Option(False, "--functions", help="Require function calling"),
    data_residency: Optional[str] = typer.Option(None, "--data-residency", help="Data residency (us, eu, local)"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    """Route a single task."""
    router = _get_router(config_path)
    
    # Build task
    requirements = TaskRequirements(
        max_cost=max_cost,
        max_latency_ms=max_latency,
        functions_required=require_functions,
        data_residency=data_residency,
    )
    
    task_obj = Task(
        id="cli-task",
        prompt=prompt,
        requirements=requirements,
        priority=TaskPriority.NORMAL,
    )
    
    # Route
    decision = router.route(task_obj)
    
    # Display results
    if dry_run:
        console.print("[dim]Dry run - no execution[/dim]\n")
    
    console.print(Panel(
        f"[bold cyan]{decision.provider_id}[/bold cyan]\n\n"
        f"[dim]Confidence:[/dim] {decision.confidence:.0%}\n"
        f"[dim]Est. Cost:[/dim] ${decision.estimated_cost:.4f}\n"
        f"[dim]Est. Latency:[/dim] {decision.estimated_latency_ms}ms",
        title="Routing Decision",
        border_style="green",
    ))
    
    if verbose:
        console.print(f"\n[bold]Reasoning:[/bold]")
        console.print(decision.reasoning)
        
        if decision.alternatives:
            console.print(f"\n[bold]Alternatives:[/bold]")
            for alt in decision.alternatives[:3]:
                console.print(f"  • {alt['provider_id']}: {alt['overall']:.2f}")
    
    if not dry_run:
        console.print("\n[yellow]Note:[/yellow] Execution not yet implemented")


@app.command()
def benchmark(
    prompt: str = typer.Argument(..., help="Task to benchmark"),
    iterations: int = typer.Option(10, "--iterations", "-n", help="Number of iterations"),
    providers: Optional[List[str]] = typer.Option(None, "--provider", "-p", help="Specific providers to test"),
):
    """Benchmark routing across providers."""
    console.print(f"Benchmarking: {prompt}")
    console.print(f"Iterations: {iterations}")
    console.print("\n[yellow]Not yet implemented[/yellow]")


@app.command()
def explain(
    prompt: str = typer.Argument(..., help="Task to explain routing for"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c"),
):
    """Explain why a task was routed to a specific provider."""
    router = _get_router(config_path)
    
    task_obj = Task(
        id="explain-task",
        prompt=prompt,
    )
    
    decision = router.route(task_obj)
    
    console.print(Panel(
        decision.reasoning,
        title=f"Why {decision.provider_id}?",
        border_style="blue",
    ))
    
    console.print("\n[bold]Score Breakdown:[/bold]")
    console.print(f"  Quality:      {decision.quality_score:.0%}")
    console.print(f"  Speed:        {decision.speed_score:.0%}")
    console.print(f"  Cost:         {decision.cost_score:.0%}")
    console.print(f"  Reliability:  {decision.reliability_score:.0%}")
    console.print(f"  ─────────────────────")
    console.print(f"  Overall:      {decision.overall_score:.0%}")
