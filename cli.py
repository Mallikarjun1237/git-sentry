import typer
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm, Prompt
import context, scanner, snapshot, agent
from google.genai.errors import ServerError, ClientError, APIError

app = typer.Typer()
console = Console()

@app.command()
def run(prompt: str):
    """Analyze and execute a Git command safely."""
    if not context.is_git_repository():
        console.print("[bold red]Not a Git repository.[/bold red]")
        raise typer.Exit(1)

    state = context.get_git_state()
    secrets = scanner.scan_working_tree_for_secrets()

    if secrets:
        console.print(Panel(
            f"[bold yellow]Found {len(secrets)} potential secrets![/bold yellow]\n" + 
            "\n".join([f"- {s['type']} in {s['source']}" for s in secrets]),
            title="SECURITY ALERT", border_style="red"
        ))
        if Confirm.ask("Quarantine these files (add to .gitignore)?"):
            for s in secrets:
                if s['source'] != "Diff/Staged":
                    scanner.quarantine_file(s['source'])
            console.print("[green]Files quarantined.[/green]")

    with console.status("[bold blue]AI analyzing blast radius..."):
        try:
            plan = agent.analyze_and_plan(prompt, state, secrets)
        except ServerError:
            console.print("\n[bold yellow]⚠️  Upstream Gemini Service Busy[/bold yellow]")
            console.print("[dim]Google's model servers are temporarily overloaded. Please retry in a few seconds.[/dim]\n")
            raise typer.Exit(code=1)
        except ClientError as e:
            console.print(f"\n[bold red]❌ Gemini API Request Rejected[/bold red]")
            console.print(f"[dim]Reason: {e.message}[/dim]\n")
            raise typer.Exit(code=1)
        except NameError as e:
            # Catches undefined variables like 'config'
            console.print("\n[bold red]🔧 Internal Configuration Error[/bold red]")
            console.print(f"[yellow]A required setting or variable is missing in the agent engine: {e}[/yellow]")
            console.print("[dim]Check agent.py to verify all parameters and models are properly declared.[/dim]\n")
            raise typer.Exit(code=1)
        except Exception as e:
            console.print("\n[bold red]❌ Execution Pipeline Failure[/bold red]")
            console.print(f"[red]Error Detail:[/red] {type(e).__name__}: {str(e)}")
            # Optional: enable with a --debug flag or print subtle traceback for developers
            console.print("[dim]Run with your code editor open or inspect agent.py for stack details.[/dim]\n")
            raise typer.Exit(code=1)

    # UI Rendering
    risk_color = {"SAFE": "green", "CAUTION": "yellow", "CRITICAL_HAZARD": "red"}[plan.risk_level]
    
    table = Table(title="Blast Radius Analysis")
    table.add_column("Property", style="cyan")
    table.add_column("Details")
    table.add_row("Risk Level", f"[{risk_color}]{plan.risk_level}[/{risk_color}]")
    table.add_row("Command", f"[bold]{plan.command}[/bold]")
    table.add_row("Scope", plan.blast_radius_summary)
    table.add_row("Impacted", ", ".join(plan.files_at_risk) or "None")
    
    console.print(table)
    console.print(f"\n[italic]{plan.explanation}[/italic]\n")

    if Confirm.ask("Execute this plan?"):
        if plan.risk_level in ["CAUTION", "CRITICAL_HAZARD"]:
            sha = snapshot.create_shadow_snapshot()
            console.print(f"[dim]Shadow snapshot created: {sha}[/dim]")

        res = subprocess.run(plan.command, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            console.print("[bold green]Success.[/bold green]")
            if res.stdout: console.print(res.stdout)
        else:
            console.print(f"[bold red]Error:[/bold red] {res.stderr}")

@app.command()
def panic():
    """Recover files from the last shadow snapshot."""
    success, msg = snapshot.execute_panic_revert()
    if success:
        console.print(Panel(msg, title="Disaster Recovery", border_style="green"))
    else:
        console.print(f"[bold red]{msg}[/bold red]")

@app.command()
def scan():
    """Standalone secret scan."""
    secrets = scanner.scan_working_tree_for_secrets()
    if not secrets:
        console.print("[bold green]No secrets found.[/bold green]")
    else:
        for s in secrets:
            console.print(f"[red]![/red] {s['type']} -> {s['source']} ({s['sample']})")

if __name__ == "__main__":
    app()