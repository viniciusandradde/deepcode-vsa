---
name: vsa-cli-patterns
description: CLI patterns for VSA using Typer and Rich. Use when implementing CLI commands, progress indicators, formatted tables, markdown output, or dashboard displays.
---

# VSA CLI Patterns

## CLI Structure with Typer

```python
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from enum import Enum

app = typer.Typer(
    name="vsa-deepcode",
    help="DeepCode VSA - Intelligent IT Management Agent"
)
console = Console()

class MethodologyOption(str, Enum):
    itil = "itil"
    gut = "gut"
    rca = "rca"
    w5h2 = "5w2h"

class OutputFormat(str, Enum):
    text = "text"
    json = "json"
    markdown = "markdown"
```

---

## Command: analyze

```python
@app.command()
def analyze(
    query: str = typer.Argument(..., help="What to analyze"),
    method: MethodologyOption = typer.Option(
        MethodologyOption.gut, "--method", "-m",
        help="Methodology to use"
    ),
    linear: bool = typer.Option(False, "--linear", help="Create Linear issue"),
    output: OutputFormat = typer.Option(
        OutputFormat.text, "--output", "-o",
        help="Output format"
    )
):
    """Analyze data with IT management methodologies."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"📊 Analyzing with {method.value}...", total=None)
        
        # Run analysis
        result = asyncio.run(run_analysis(query, method.value))
        
        progress.update(task, completed=True)
    
    # Display results
    if output == OutputFormat.json:
        console.print_json(data=result)
    elif output == OutputFormat.markdown:
        console.print(Markdown(format_as_markdown(result)))
    else:
        display_analysis_table(result)
```

---

## Command: diagnose (RCA)

```python
@app.command()
def diagnose(
    problem: str = typer.Argument(..., help="Problem to diagnose"),
    method: MethodologyOption = typer.Option(
        MethodologyOption.rca, "--method", "-m"
    ),
    linear: bool = typer.Option(False, "--linear", help="Create Linear issue"),
    execute: bool = typer.Option(False, "--execute", "-e", help="Execute fixes")
):
    """Diagnose problems with root cause analysis."""
    console.print(Panel(
        f"[bold cyan]🔍 Diagnosing:[/] {problem}",
        title="VSA DeepCode",
        border_style="cyan"
    ))
    
    with console.status("[bold green]Performing 5 Whys analysis..."):
        result = asyncio.run(run_rca(problem))
    
    # Display RCA chain
    for i, why in enumerate(result.whys, 1):
        console.print(f"\n[bold yellow]WHY {i}:[/] {why.question}")
        console.print(f"→ {why.answer}")
    
    # Root cause panel
    console.print(Panel(
        f"[bold red]{result.root_cause}[/]",
        title="🎯 ROOT CAUSE",
        border_style="red"
    ))
    
    # Actions
    console.print("\n[bold green]✅ RECOMMENDED ACTIONS:[/]")
    for i, action in enumerate(result.preventive_actions, 1):
        console.print(f"  {i}. {action}")
```

---

## Command: code (OpenCode-style)

```python
@app.command()
def code(
    task: str = typer.Argument(..., help="Coding task to perform"),
    dry_run: bool = typer.Option(True, "--dry-run/--execute", help="Dry run mode")
):
    """Execute coding tasks with AI agent."""
    console.print(Panel(
        f"[bold cyan]💻 Task:[/] {task}",
        title="VSA DeepCode - Code Mode",
        border_style="cyan"
    ))
    
    dry_run_text = "[yellow]DRY RUN[/]" if dry_run else "[green]EXECUTING[/]"
    console.print(f"Mode: {dry_run_text}\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        agent_task = progress.add_task("🤖 Agent working...", total=None)
        
        result = asyncio.run(run_code_task(task, dry_run=dry_run))
        
        progress.update(agent_task, completed=True)
    
    # Display execution summary
    display_execution_summary(result)
```

---

## Command: shell (Safe bash)

```python
@app.command()
def shell(
    command: str = typer.Argument(..., help="Shell command"),
    execute: bool = typer.Option(False, "--execute", "-e", help="Execute command"),
    cwd: str = typer.Option(".", "--cwd", "-c", help="Working directory")
):
    """Execute shell commands with safety checks."""
    console.print(f"[bold cyan]🔧 Command:[/] {command}")
    
    # Safety check
    checker = SafetyChecker()
    safety = checker.check(command)
    
    if not safety.is_safe:
        console.print(f"[bold red]❌ Safety check failed:[/] {safety.reason}")
        raise typer.Exit(1)
    
    console.print("[bold green]✅ Safety check passed[/]")
    
    if not execute:
        console.print("[yellow]Use --execute to run[/]")
        return
    
    result = asyncio.run(bash_tool(BashInput(
        command=command,
        cwd=cwd,
        dry_run=False
    )))
    
    if result.success:
        console.print(f"[bold green]✅ Success[/]\n")
        console.print(result.stdout)
    else:
        console.print(f"[bold red]❌ Failed[/]\n")
        console.print(result.stderr)
```

---

## Command: dashboard

```python
@app.command()
def dashboard():
    """Display real-time dashboard."""
    from rich.live import Live
    from rich.layout import Layout
    
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )
    
    layout["main"].split_row(
        Layout(name="left"),
        Layout(name="right")
    )
    
    with Live(layout, refresh_per_second=1, console=console) as live:
        while True:
            # Update header
            layout["header"].update(Panel(
                "[bold cyan]VSA DeepCode Dashboard[/]",
                style="cyan"
            ))
            
            # Update left panel (GLPI)
            glpi_data = get_glpi_summary()
            layout["left"].update(Panel(
                create_glpi_table(glpi_data),
                title="GLPI Tickets"
            ))
            
            # Update right panel (Zabbix)
            zabbix_data = get_zabbix_summary()
            layout["right"].update(Panel(
                create_zabbix_table(zabbix_data),
                title="Zabbix Alerts"
            ))
            
            # Update footer
            layout["footer"].update(Panel(
                f"Last update: {datetime.now().strftime('%H:%M:%S')} | Press Ctrl+C to exit"
            ))
            
            time.sleep(5)
```

---

## Display Helpers

### GUT Priority Table

```python
def display_gut_table(items: list[dict]):
    """Display GUT-prioritized items."""
    table = Table(
        title="📊 GUT Matrix Prioritization",
        show_header=True,
        header_style="bold magenta"
    )
    
    table.add_column("Rank", style="cyan", width=6)
    table.add_column("GUT", style="bold", width=8)
    table.add_column("Priority", width=10)
    table.add_column("Description", style="dim")
    
    for i, item in enumerate(items, 1):
        priority_color = {
            "CRITICAL": "red",
            "HIGH": "yellow",
            "MEDIUM": "blue",
            "LOW": "green"
        }.get(item["priority"], "white")
        
        table.add_row(
            str(i),
            f"[bold]{item['gut_score']}[/]",
            f"[{priority_color}]{item['priority']}[/]",
            item["description"][:50] + "..."
        )
    
    console.print(table)
```

### Execution Summary

```python
def display_execution_summary(result: dict):
    """Display execution summary."""
    success = result.get("success", False)
    status = "[bold green]✅ Success[/]" if success else "[bold red]❌ Failed[/]"
    
    table = Table(title="📊 Execution Summary", show_header=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value")
    
    table.add_row("Status", status)
    table.add_row("Steps", str(result.get("steps_completed", 0)))
    table.add_row("Dry Run", "Yes" if result.get("dry_run") else "No")
    table.add_row("Duration", f"{result.get('duration', 0):.2f}s")
    
    console.print(table)
    
    # Files modified
    if result.get("files_created"):
        console.print("\n[bold cyan]💾 Files created:[/]")
        for f in result["files_created"]:
            console.print(f"  - {f}")
```

---

## Error Handling

```python
@app.callback()
def main_callback(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    debug: bool = typer.Option(False, "--debug", help="Debug mode")
):
    """VSA DeepCode - Intelligent IT Management Agent"""
    if debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)

def handle_error(func):
    """Decorator for error handling."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/]")
            raise typer.Exit(130)
        except Exception as e:
            console.print(f"[bold red]Error:[/] {e}")
            if os.getenv("VSA_DEBUG"):
                console.print_exception()
            raise typer.Exit(1)
    return wrapper
```
