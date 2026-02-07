"""
Provider management commands.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich import box

from ..registry.loader import RegistryLoader
from ..registry.store import create_store

app = typer.Typer(help="Manage model providers")
console = Console()


def _get_loader(config_path: Optional[Path] = None) -> RegistryLoader:
    """Get configured registry loader."""
    path = config_path or Path("config")
    return RegistryLoader(path)


@app.command(name="list")
def list_providers(
    config_path: Optional[Path] = typer.Option(None, "--config", "-c"),
    show_all: bool = typer.Option(False, "--all", "-a", help="Include disabled providers"),
):
    """List all configured providers."""
    loader = _get_loader(config_path)
    
    try:
        providers = loader.load_directory()
    except FileNotFoundError:
        console.print("[yellow]Warning:[/yellow] No providers configured")
        console.print(f"Run: federation init")
        raise typer.Exit(1)
    
    table = Table(
        title="Federation Providers",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold blue",
    )
    
    table.add_column("Provider", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Models", justify="right")
    table.add_column("Latency", justify="right")
    table.add_column("Cost/Mtok", justify="right")
    table.add_column("Quality", justify="right")
    
    for provider in providers.values():
        if not show_all and not provider.enabled:
            continue
        
        # Status indicator
        if not provider.enabled:
            status = "[dim]disabled[/dim]"
        elif provider.health.is_available():
            status = "[green]●[/green]"
        else:
            status = "[red]✗[/red]"
        
        # Format values
        latency = provider.capabilities.typical_latency_ms
        latency_str = f"{latency}ms" if latency else "-"
        
        cost = provider.cost
        cost_str = f"${cost.input_per_1m:.2f}"
        
        quality = provider.quality_score
        quality_str = f"{quality:.0%}" if quality else "-"
        
        table.add_row(
            f"{provider.emoji} {provider.name}",
            status,
            str(len(provider.models)),
            latency_str,
            cost_str,
            quality_str,
        )
    
    console.print(table)
    console.print(f"\n[dim]Total: {len(providers)} providers[/dim]")


@app.command()
def show(
    provider_id: str = typer.Argument(..., help="Provider ID to show"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c"),
):
    """Show detailed information about a provider."""
    loader = _get_loader(config_path)
    
    try:
        providers = loader.load_directory()
    except FileNotFoundError:
        console.print("[red]Error:[/red] No providers configured")
        raise typer.Exit(1)
    
    if provider_id not in providers:
        console.print(f"[red]Error:[/red] Provider '{provider_id}' not found")
        raise typer.Exit(1)
    
    provider = providers[provider_id]
    
    console.print(f"\n[bold blue]{provider.emoji} {provider.name}[/bold blue]")
    console.print(f"[dim]ID:[/dim] {provider.id}")
    console.print(f"[dim]Tier:[/dim] {provider.tier.value}")
    console.print(f"[dim]API Base:[/dim] {provider.api_base}")
    
    console.print(f"\n[bold]Capabilities:[/bold]")
    caps = provider.capabilities
    console.print(f"  Max Context: {caps.max_context:,} tokens")
    console.print(f"  Features: ", end="")
    features = []
    if caps.supports_functions:
        features.append("functions")
    if caps.supports_vision:
        features.append("vision")
    if caps.supports_streaming:
        features.append("streaming")
    console.print(", ".join(features) if features else "basic")
    
    console.print(f"\n[bold]Pricing:[/bold]")
    cost = provider.cost
    console.print(f"  Input: ${cost.input_per_1m:.2f} per 1M tokens")
    console.print(f"  Output: ${cost.output_per_1m:.2f} per 1M tokens")
    
    console.print(f"\n[bold]Models:[/bold]")
    for model in provider.models:
        console.print(f"  • {model}")


@app.command()
def test(
    provider_id: str = typer.Argument(..., help="Provider ID to test"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c"),
    timeout: int = typer.Option(30, "--timeout", "-t", help="Timeout in seconds"),
):
    """Test connectivity to a provider."""
    import httpx
    
    console.print(f"Testing {provider_id}...")
    
    loader = _get_loader(config_path)
    
    try:
        providers = loader.load_directory()
    except FileNotFoundError:
        console.print("[red]Error:[/red] No providers configured")
        raise typer.Exit(1)
    
    if provider_id not in providers:
        console.print(f"[red]Error:[/red] Provider '{provider_id}' not found")
        raise typer.Exit(1)
    
    provider = providers[provider_id]
    
    # Simple connectivity test
    try:
        response = httpx.get(
            provider.api_base,
            timeout=timeout,
            follow_redirects=True,
        )
        
        if response.status_code < 500:
            console.print(f"[green]✓[/green] {provider.name} is reachable")
            console.print(f"  Status: {response.status_code}")
            console.print(f"  Latency: {response.elapsed.total_seconds()*1000:.0f}ms")
        else:
            console.print(f"[yellow]⚠[/yellow] {provider.name} returned {response.status_code}")
            
    except httpx.ConnectError as e:
        console.print(f"[red]✗[/red] Connection failed: {e}")
        raise typer.Exit(1)
    except httpx.TimeoutException:
        console.print(f"[red]✗[/red] Connection timed out after {timeout}s")
        raise typer.Exit(1)


@app.command()
def enable(
    provider_id: str = typer.Argument(..., help="Provider ID to enable"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c"),
):
    """Enable a provider."""
    console.print(f"Enabling {provider_id}...")
    # TODO: Implement enable/disable
    console.print("[yellow]Not yet implemented[/yellow]")


@app.command()
def disable(
    provider_id: str = typer.Argument(..., help="Provider ID to disable"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c"),
):
    """Disable a provider."""
    console.print(f"Disabling {provider_id}...")
    # TODO: Implement enable/disable
    console.print("[yellow]Not yet implemented[/yellow]")
