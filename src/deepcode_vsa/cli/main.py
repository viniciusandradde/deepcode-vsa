"""DeepCode VSA CLI - Main entry point.

Reference: .claude/skills/vsa-cli-patterns/SKILL.md
"""

import asyncio
import uuid
from enum import Enum
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..agent import create_vsa_agent
from ..agent.state import create_initial_state, Methodology
from ..config import get_settings

# CLI App
app = typer.Typer(
    name="vsa",
    help="🤖 DeepCode VSA - Intelligent IT Management Agent",
    add_completion=False,
)
console = Console()


class MethodologyOption(str, Enum):
    """CLI methodology options."""
    itil = "itil"
    gut = "gut"
    rca = "rca"
    w5h2 = "5w2h"


class OutputFormat(str, Enum):
    """CLI output format options."""
    text = "text"
    json = "json"
    markdown = "markdown"


def show_banner():
    """Display VSA banner."""
    console.print(Panel(
        "[bold cyan]🤖 DeepCode VSA[/]\n"
        "[dim]Virtual Support Agent for IT Management[/]",
        border_style="cyan"
    ))


@app.command()
def analyze(
    query: str = typer.Argument(..., help="Query to analyze"),
    method: MethodologyOption = typer.Option(
        MethodologyOption.gut,
        "--method", "-m",
        help="Methodology to use"
    ),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--execute",
        help="Dry run mode (default: on)"
    ),
    output: OutputFormat = typer.Option(
        OutputFormat.text,
        "--output", "-o",
        help="Output format"
    ),
):
    """📊 Analyze IT data with methodologies (ITIL, GUT, RCA, 5W2H)."""
    show_banner()
    
    console.print(f"\n[bold]Query:[/] {query}")
    console.print(f"[bold]Methodology:[/] {method.value.upper()}")
    console.print(f"[bold]Mode:[/] {'DRY RUN' if dry_run else 'EXECUTE'}\n")
    
    asyncio.run(_run_agent(query, dry_run))


@app.command()
def diagnose(
    problem: str = typer.Argument(..., help="Problem to diagnose"),
    method: MethodologyOption = typer.Option(
        MethodologyOption.rca,
        "--method", "-m",
        help="Methodology (default: RCA)"
    ),
    dry_run: bool = typer.Option(True, "--dry-run/--execute"),
):
    """🔍 Diagnose problems with Root Cause Analysis (5 Whys)."""
    show_banner()
    
    console.print(f"\n[bold red]Problem:[/] {problem}")
    console.print(f"[bold]Methodology:[/] {method.value.upper()}\n")
    
    asyncio.run(_run_agent(problem, dry_run))


@app.command()
def query(
    question: str = typer.Argument(..., help="Question to ask"),
    dry_run: bool = typer.Option(True, "--dry-run/--execute"),
):
    """❓ Query IT systems (GLPI, Zabbix)."""
    show_banner()
    
    console.print(f"\n[bold]Question:[/] {question}\n")
    
    asyncio.run(_run_agent(question, dry_run))


@app.command()
def status():
    """📋 Show agent and integrations status."""
    show_banner()
    settings = get_settings()
    
    table = Table(title="Integration Status")
    table.add_column("Integration", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("URL")
    
    # GLPI
    glpi_status = "✅ Enabled" if settings.glpi.enabled else "❌ Disabled"
    table.add_row("GLPI", glpi_status, settings.glpi.base_url or "[dim]Not configured[/]")
    
    # Zabbix
    zabbix_status = "✅ Enabled" if settings.zabbix.enabled else "❌ Disabled"
    table.add_row("Zabbix", zabbix_status, settings.zabbix.base_url or "[dim]Not configured[/]")
    
    # LLM
    llm_configured = "✅ Configured" if settings.llm.api_key else "❌ Not configured"
    table.add_row("LLM (OpenRouter)", llm_configured, settings.llm.provider)
    
    console.print(table)
    
    # LLM Models
    console.print("\n[bold]LLM Models:[/]")
    console.print(f"  [cyan]FAST:[/] {settings.llm.fast_model}")
    console.print(f"  [cyan]SMART:[/] {settings.llm.smart_model}")
    console.print(f"  [cyan]CREATIVE:[/] {settings.llm.creative_model}")
    console.print(f"  [cyan]PREMIUM:[/] {settings.llm.premium_model}")


@app.command()
def version():
    """Show version information."""
    from .. import __version__
    console.print(f"DeepCode VSA v{__version__}")


async def _run_agent(user_request: str, dry_run: bool = True):
    """Run the VSA agent with the given request."""
    session_id = str(uuid.uuid4())[:8]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("🤖 Agent processing...", total=None)
        
        try:
            # Create agent
            agent = create_vsa_agent()
            
            # Create initial state
            initial_state = create_initial_state(
                user_request=user_request,
                session_id=session_id,
                dry_run=dry_run
            )
            
            # Run agent
            final_state = await agent.ainvoke(initial_state)
            
            progress.update(task, description="✅ Processing complete")
            
        except Exception as e:
            progress.update(task, description=f"❌ Error: {e}")
            console.print(f"\n[bold red]Error:[/] {e}")
            raise typer.Exit(1)
    
    # Display results
    _display_results(final_state)


def _display_results(state: dict):
    """Display agent execution results."""
    console.print("\n" + "=" * 60)
    
    # Messages
    messages = state.get("messages", [])
    for msg in messages:
        if hasattr(msg, "content"):
            console.print(msg.content)
    
    # Summary
    console.print("\n" + "=" * 60)
    
    table = Table(title="📊 Execution Summary", show_header=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value")
    
    # Category
    category = state.get("task_category")
    if category:
        table.add_row("Category", category.value.upper())
    
    # Priority
    priority = state.get("priority")
    if priority:
        priority_color = {
            "critical": "red",
            "high": "yellow", 
            "medium": "blue",
            "low": "green"
        }.get(priority.value, "white")
        table.add_row("Priority", f"[{priority_color}]{priority.value.upper()}[/]")
    
    # GUT Score
    gut_score = state.get("gut_score")
    if gut_score:
        table.add_row("GUT Score", str(gut_score))
    
    # Steps
    plan = state.get("plan") or []
    current_step = state.get("current_step", 0)
    table.add_row("Steps", f"{current_step}/{len(plan)}")
    
    # Dry Run
    dry_run = state.get("dry_run", True)
    table.add_row("Dry Run", "Yes" if dry_run else "No")
    
    console.print(table)


def main():
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
