"""
Status and health commands.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich import box

from ..registry.loader import RegistryLoader
from ..registry.store import create_store

app = typer.Typer(help="Check federation status")
console = Console()


@app.command()
def health(
    config_path: Optional[Path] = typer.Option(None, "--config", "-c"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Check specific provider"),
):
    """Check health status of providers."""
    loader = RegistryLoader(config_path or Path("config"))
    
    try:
        providers = loader.load_directory()
    except FileNotFoundError:
        console.print("[yellow]Warning:[/yellow] No providers configured")
        raise typer.Exit(1)
    
    if provider:
        if provider not in providers:
            console.print(f"[red]Error:[/red] Provider '{provider}' not found")
            raise typer.Exit(1)
        providers = {provider: providers[provider]}
    
    table = Table(
        title="Provider Health",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold blue",
    )
    
    table.add_column("Provider")
    table.add_column("Status", justify="center")
    table.add_column("Latency", justify="right")
    table.add_column("Error Rate", justify="right")
    table.add_column("Available", justify="center")
    
    for pid, p in providers.items():
        health = p.health
        
        status_color = {
            "HEALTHY": "green",
            "DEGRADED": "yellow",
            "UNHEALTHY": "red",
            "UNKNOWN": "dim",
        }.get(health.status.name, "dim")
        
        table.add_row(
            f"{p.emoji} {p.name}",
            f"[{status_color}]{health.status.name}[/{status_color}]",
            f"{health.avg_latency_ms:.0f}ms" if health.avg_latency_ms else "-",
            f"{health.error_rate_24h:.1%}" if health.error_rate_24h else "-",
            "✓" if health.is_available() else "✗",
        )
    
    console.print(table)


@app.command()
def stats(
    days: int = typer.Option(7, "--days", "-d", help="Number of days to show"),
):
    """Show federation usage statistics."""
    console.print(f"Statistics for last {days} days")
    console.print("\n[yellow]Not yet implemented[/yellow]")


@app.command()
def dashboard(
    port: int = typer.Option(8080, "--port", "-p", help="Port to run dashboard on"),
):
    """Launch the web dashboard."""
    console.print(f"Starting dashboard on port {port}...")
    console.print("\n[yellow]Not yet implemented[/yellow]")
    console.print("[dim]Planned: Streamlit or FastAPI + React dashboard[/dim]")
