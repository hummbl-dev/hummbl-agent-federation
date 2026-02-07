"""
Federation CLI - Main entry point.

Provides commands for:
- Managing providers
- Routing tasks
- Monitoring health
- Configuration
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..registry.loader import RegistryLoader
from ..registry.store import create_store
from ..engine.router import Router
from ..engine.models import Task, TaskRequirements

app = typer.Typer(
    name="federation",
    help="Universal Model Router for Governance-as-a-Service",
    no_args_is_help=True,
)
console = Console()

# Subcommands
from . import providers, route, status

app.add_typer(providers.app, name="provider", help="Manage model providers")
app.add_typer(route.app, name="route", help="Route tasks to providers")
app.add_typer(status.app, name="status", help="Check federation status")


@app.callback()
def main(
    config_path: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to configuration directory"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
):
    """
    Federation - Intelligent routing across 50+ model providers.
    
    Quality-first routing with governance and cost optimization.
    """
    typer.echo(f"Federation CLI v0.1.0")
    if verbose:
        typer.echo(f"Config path: {config_path or 'default'}")


@app.command()
def version():
    """Show version information."""
    console.print("[bold blue]Federation[/bold blue] v0.1.0")
    console.print("Universal Model Router for GaaS")
    console.print("\n[dim]Built with:[/dim]")
    console.print("  • Python 3.11+")
    console.print("  • Pydantic v2")
    console.print("  • Typer + Rich")


@app.command()
def init(
    path: Path = typer.Argument(Path("."), help="Directory to initialize"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing config"),
):
    """Initialize a new federation project."""
    config_dir = path / "config"
    
    if config_dir.exists() and not force:
        console.print(f"[red]Error:[/red] Config already exists at {config_dir}")
        console.print("Use --force to overwrite")
        raise typer.Exit(1)
    
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Create default providers.yaml
    loader = RegistryLoader()
    providers = loader.load_defaults()
    loader.save_yaml(providers, config_dir / "providers.yaml")
    
    console.print(f"[green]✓[/green] Initialized federation at {path}")
    console.print(f"  Created: {config_dir}/providers.yaml")
    console.print(f"\n[dim]Next steps:[/dim]")
    console.print(f"  1. Edit {config_dir}/providers.yaml")
    console.print(f"  2. Run: federation provider test <name>")
    console.print(f"  3. Route your first task: federation route \"Hello world\"")


if __name__ == "__main__":
    app()
