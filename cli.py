# import typer
# import subprocess
# from rich.console import Console
# from rich.panel import Panel
# from rich.table import Table
# from rich.prompt import Confirm, Prompt
# import context, scanner, snapshot, agent
# from google.genai.errors import ServerError, ClientError, APIError

# app = typer.Typer()
# console = Console()

# @app.command()
# def run(prompt: str):
#     """Analyze and execute a Git command safely."""
#     if not context.is_git_repository():
#         console.print("[bold red]Not a Git repository.[/bold red]")
#         raise typer.Exit(1)

#     state = context.get_git_state()
#     secrets = scanner.scan_working_tree_for_secrets()

#     if secrets:
#         console.print(Panel(
#             f"[bold yellow]Found {len(secrets)} potential secrets![/bold yellow]\n" + 
#             "\n".join([f"- {s['type']} in {s['source']}" for s in secrets]),
#             title="SECURITY ALERT", border_style="red"
#         ))
#         if Confirm.ask("Quarantine these files (add to .gitignore)?"):
#             for s in secrets:
#                 if s['source'] != "Diff/Staged":
#                     scanner.quarantine_file(s['source'])
#             console.print("[green]Files quarantined.[/green]")

#     with console.status("[bold blue]AI analyzing blast radius..."):
#         try:
#             plan = agent.analyze_and_plan(prompt, state, secrets)
#         except ServerError:
#             console.print("\n[bold yellow]⚠️  Upstream Gemini Service Busy[/bold yellow]")
#             console.print("[dim]Google's model servers are temporarily overloaded. Please retry in a few seconds.[/dim]\n")
#             raise typer.Exit(code=1)
#         except ClientError as e:
#             console.print(f"\n[bold red]❌ Gemini API Request Rejected[/bold red]")
#             console.print(f"[dim]Reason: {e.message}[/dim]\n")
#             raise typer.Exit(code=1)
#         except NameError as e:
#             # Catches undefined variables like 'config'
#             console.print("\n[bold red]🔧 Internal Configuration Error[/bold red]")
#             console.print(f"[yellow]A required setting or variable is missing in the agent engine: {e}[/yellow]")
#             console.print("[dim]Check agent.py to verify all parameters and models are properly declared.[/dim]\n")
#             raise typer.Exit(code=1)
#         except Exception as e:
#             console.print("\n[bold red]❌ Execution Pipeline Failure[/bold red]")
#             console.print(f"[red]Error Detail:[/red] {type(e).__name__}: {str(e)}")
#             # Optional: enable with a --debug flag or print subtle traceback for developers
#             console.print("[dim]Run with your code editor open or inspect agent.py for stack details.[/dim]\n")
#             raise typer.Exit(code=1)

#     # UI Rendering
#     risk_color = {"SAFE": "green", "CAUTION": "yellow", "CRITICAL_HAZARD": "red"}[plan.risk_level]
    
#     table = Table(title="Blast Radius Analysis")
#     table.add_column("Property", style="cyan")
#     table.add_column("Details")
#     table.add_row("Risk Level", f"[{risk_color}]{plan.risk_level}[/{risk_color}]")
#     table.add_row("Command", f"[bold]{plan.command}[/bold]")
#     table.add_row("Scope", plan.blast_radius_summary)
#     table.add_row("Impacted", ", ".join(plan.files_at_risk) or "None")
    
#     console.print(table)
#     console.print(f"\n[italic]{plan.explanation}[/italic]\n")

#     if Confirm.ask("Execute this plan?"):
#         if plan.risk_level in ["CAUTION", "CRITICAL_HAZARD"]:
#             sha = snapshot.create_shadow_snapshot()
#             console.print(f"[dim]Shadow snapshot created: {sha}[/dim]")

#         res = subprocess.run(plan.command, shell=True, capture_output=True, text=True)
#         if res.returncode == 0:
#             console.print("[bold green]Success.[/bold green]")
#             if res.stdout: console.print(res.stdout)
#         else:
#             console.print(f"[bold red]Error:[/bold red] {res.stderr}")

# @app.command()
# def panic():
#     """Recover files from the last shadow snapshot."""
#     success, msg = snapshot.execute_panic_revert()
#     if success:
#         console.print(Panel(msg, title="Disaster Recovery", border_style="green"))
#     else:
#         console.print(f"[bold red]{msg}[/bold red]")

# @app.command()
# def scan():
#     """Standalone secret scan."""
#     secrets = scanner.scan_working_tree_for_secrets()
#     if not secrets:
#         console.print("[bold green]No secrets found.[/bold green]")
#     else:
#         for s in secrets:
#             console.print(f"[red]![/red] {s['type']} -> {s['source']} ({s['sample']})")

# if __name__ == "__main__":
#     app()


import os
import sys
import subprocess
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
import context
import scanner
import snapshot
import agent
import hooks
import resolver
from config import save_config, get_config, set_global_api_key, get_repo_root
from google.genai.errors import ServerError, ClientError, APIError

app = typer.Typer(help="Git-Sentry 🛡️ Autonomous Safety Proxy & Recovery CLI")
console = Console()

def run_shell_command(command: str):
    """Executes commands safely with explicit UTF-8 encoding across platforms."""
    if sys.platform == "win32":
        command = f"chcp 65001 >nul && {command}"

    return subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

@app.command()
def configure(gui: bool = typer.Option(False, "--gui", help="Open configuration in a graphical dialog window")):
    """Configure your global Gemini API key, snapshot path, and preferred AI model."""
    current_cfg = get_config()

    if gui:
        try:
            import tkinter as tk
            from tkinter import simpledialog, filedialog, messagebox

            root = tk.Tk()
            root.withdraw()

            api_key = simpledialog.askstring("Git-Sentry", "Gemini API Key:", show="*")
            if not api_key:
                console.print("[yellow]GUI Configuration cancelled.[/yellow]")
                return

            chosen_dir = filedialog.askdirectory(title="Select Snapshot & Config Directory (Optional)")
            save_config(
                api_key=api_key,
                storage_dir=chosen_dir if chosen_dir else None,
                model=current_cfg.get("model", "gemini-3.8-flash")
            )
            messagebox.showinfo("Git-Sentry", "Configuration successfully saved!")
            console.print("[bold green]✓ Configuration saved via GUI dialog.[/bold green]")
            return
        except Exception as e:
            console.print(f"[red]GUI failed to open: {e}. Falling back to CLI mode.[/red]")

    console.print(Panel("[bold cyan]Git-Sentry Setup Wizard[/bold cyan]", expand=False))
    key = Prompt.ask("[cyan]Enter Gemini API Key[/cyan]", password=True)
    if not key.strip():
        console.print("[yellow]No key entered. Configuration aborted.[/yellow]")
        return

    default_dir = current_cfg.get("storage_dir", str(os.path.expanduser("~/.git-sentry")))
    storage_dir = Prompt.ask("[cyan]Snapshot directory[/cyan]", default=default_dir)

    model = Prompt.ask(
        "[cyan]Default Model[/cyan]",
        choices=["gemini-3.8-flash"],
        default=current_cfg.get("model", "gemini-3.8-flash")
    )

    save_config(api_key=key, storage_dir=storage_dir, model=model)
    console.print("\n[bold green]✓ Configuration saved globally in ~/.git-sentry/config.json[/bold green]")

@app.command()
def run(prompt: str):
    """Analyze intent, calculate blast radius, and execute Git commands safely."""
    if not context.is_git_repository():
        console.print("[bold red]Not a Git repository.[/bold red]")
        raise typer.Exit(1)

    state = context.get_git_state()
    secrets = scanner.scan_working_tree_for_secrets()
    secrets_quarantined = True

    if secrets:
        console.print(Panel(
            f"[bold yellow]Found {len(secrets)} potential secrets![/bold yellow]\n" +
            "\n".join([f"- {s['type']} in {s['source']}" for s in secrets]),
            title="SECURITY ALERT", border_style="red"
        ))
        if Confirm.ask("Quarantine these files (add to .gitignore)?"):
            for s in secrets:
                if s["source"] != "Diff/Staged":
                    scanner.quarantine_file(s["source"])
            console.print("[green]Files quarantined in .gitignore.[/green]")
            secrets = scanner.scan_working_tree_for_secrets()
        else:
            secrets_quarantined = False

    with console.status("[bold blue]AI analyzing blast radius...[/bold blue]"):
        try:
            plan = agent.analyze_and_plan(prompt, state, secrets)
        except ServerError:
            console.print("\n[bold yellow]⚠️  Upstream Gemini Service Busy[/bold yellow]")
            console.print("[dim]Google's model servers are temporarily overloaded. Please retry in a few seconds.[/dim]\n")
            raise typer.Exit(code=1)
        except ClientError as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                console.print("\n[bold yellow]⏳ Gemini API Free Tier Quota Exceeded[/bold yellow]")
                console.print("[dim]You've hit Google's per-minute rate limit. Wait ~30 seconds or create a new key at aistudio.google.com.[/dim]\n")
            else:
                console.print(f"\n[bold red]❌ Gemini API Request Rejected[/bold red]")
                console.print(f"[dim]Reason: {e.message}[/dim]\n")
            raise typer.Exit(code=1)
        except NameError as e:
            console.print("\n[bold red]🔧 Internal Configuration Error[/bold red]")
            console.print(f"[yellow]A required setting or variable is missing in the agent engine: {e}[/yellow]")
            console.print("[dim]Check agent.py to verify all parameters and models are properly declared.[/dim]\n")
            raise typer.Exit(code=1)
        except Exception as e:
            console.print("\n[bold red]❌ Execution Pipeline Failure[/bold red]")
            console.print(f"[red]Error Detail:[/red] {type(e).__name__}: {str(e)}")
            raise typer.Exit(code=1)

    # Security Guard: Block staging/committing/pushing unquarantined secrets
    staging_keywords = ["add", "stage", "commit", "push"]
    is_staging_action = any(k in plan.command.lower().split() for k in staging_keywords)
    if secrets and not secrets_quarantined and is_staging_action:
        console.print(Panel(
            "[bold red]⛔ EXECUTION BLOCKED[/bold red]\n"
            "Unquarantined credentials detected. Git-Sentry will not commit or push exposed secrets.",
            border_style="red"
        ))
        raise typer.Exit(code=1)

    # UI Rendering
    risk_color = {"SAFE": "green", "CAUTION": "yellow", "CRITICAL_HAZARD": "red"}.get(plan.risk_level, "white")

    table = Table(title="Blast Radius Analysis")
    table.add_column("Property", style="cyan")
    table.add_column("Details")
    table.add_row("Risk Level", f"[{risk_color} bold]{plan.risk_level}[/{risk_color} bold]")
    table.add_row("Command", f"[bold]{plan.command}[/bold]")
    table.add_row("Scope", plan.blast_radius_summary)
    table.add_row("Impacted", ", ".join(plan.files_at_risk) or "None")

    console.print(table)
    console.print(f"\n[italic]{plan.explanation}[/italic]\n")

    # Autonomy Decision
    should_execute = False

    if plan.risk_level == "SAFE":
        console.print("[bold green]⚡ Safe operation detected. Executing autonomously...[/bold green]\n")
        should_execute = True
    else:
        warning_msg = (
            "[bold red]🚨 Critical hazard: this action will modify or delete data. Execute?[/bold red]"
            if plan.risk_level == "CRITICAL_HAZARD"
            else "[bold yellow]Execute this plan?[/bold yellow]"
        )
        should_execute = Confirm.ask(warning_msg, default=False)

    if should_execute:
        if plan.risk_level in ["CAUTION", "CRITICAL_HAZARD"]:
            sha = snapshot.create_shadow_snapshot()
            if sha:
                console.print(f"[dim]Shadow snapshot created: {sha[:8]}[/dim]")

        res = run_shell_command(plan.command)
        if res.returncode == 0:
            console.print("[bold green]Success.[/bold green]")
            if res.stdout:
                console.print(res.stdout)
        else:
            console.print(f"[bold red]Error:[/bold red] {res.stderr}")
            if plan.risk_level == "CRITICAL_HAZARD":
                console.print("[yellow]To restore modified or deleted files, run: git-sentry panic[/yellow]")
    else:
        console.print("[dim]Operation aborted by user.[/dim]")

@app.command()
def panic():
    """Recover files from the last shadow snapshot."""
    success, msg = snapshot.execute_panic_revert()
    if success:
        console.print(Panel(msg, title="Disaster Recovery", border_style="green"))
    else:
        console.print(Panel(f"[bold red]{msg}[/bold red]", title="Disaster Recovery Failed", border_style="red"))
        raise typer.Exit(code=1)

@app.command()
def scan(hook_mode: bool = typer.Option(False, "--hook-mode", help="Returns non-zero exit code if secrets are present")):
    """Standalone secret scan across diffs and untracked files."""
    secrets = scanner.scan_working_tree_for_secrets()
    if not secrets:
        if not hook_mode:
            console.print("[bold green]✓ No secrets found.[/bold green]")
        return

    table = Table(title="[bold red]Exposed Credentials Found[/bold red]")
    table.add_column("Type", style="red")
    table.add_column("Source", style="cyan")
    table.add_column("Sample", style="dim")

    for s in secrets:
        table.add_row(s["type"], s["source"], s["sample"])
    console.print(table)

    if hook_mode:
        raise typer.Exit(code=1)

@app.command()
def explain(command: str = typer.Argument(..., help="Git command to analyze")):
    """Dry-run impact explanation of any raw Git command without executing it."""
    git_state = context.get_git_state() if context.is_git_repository() else {}
    with console.status("[bold cyan]Analyzing command side effects...[/bold cyan]"):
        try:
            res = agent.explain_raw_command(command, git_state)
        except Exception as e:
            console.print(f"[bold red]Explanation failed: {e}[/bold red]")
            raise typer.Exit(code=1)

    color = "green" if res.risk_level == "SAFE" else "yellow" if res.risk_level == "CAUTION" else "red"

    table = Table(show_header=False, box=None)
    table.add_row("[bold]Analyzed Command:[/bold]", f"[cyan]{res.command}[/cyan]")
    table.add_row("[bold]Risk Assessment:[/bold]", f"[{color} bold]{res.risk_level}[/{color} bold]")
    table.add_row("[bold]Explanation:[/bold]", res.breakdown)
    table.add_row("[bold]State Changes:[/bold]", res.state_changes)
    if res.safe_alternative != "None":
        table.add_row("[bold]Safer Alternative:[/bold]", f"[bold green]{res.safe_alternative}[/bold green]")

    console.print(Panel(table, title="Command Impact Breakdown", border_style=color))

@app.command("install-hook")
def install_hook():
    """Install Git-Sentry pre-commit and pre-push hooks in the active repository."""
    success, msg = hooks.install_hooks()
    if success:
        console.print(f"[bold green]✓ {msg}[/bold green]")
    else:
        console.print(f"[bold red]✗ {msg}[/bold red]")
        raise typer.Exit(code=1)

@app.command()
def resolve():
    """Detect and resolve merge conflicts across the repository using AI."""
    conflicts = resolver.find_conflicted_files()
    if not conflicts:
        console.print("[bold green]✓ No merge conflicts detected in this repository.[/bold green]")
        return

    console.print(f"[bold yellow]Found {len(conflicts)} conflicted file(s):[/bold yellow] {', '.join(conflicts)}")

    root = get_repo_root()
    for file_path in conflicts:
        console.print(f"\n[cyan]Resolving conflict in: {file_path}...[/cyan]")
        try:
            solution = resolver.resolve_file_conflict(file_path)
            console.print(Panel(solution.explanation, title=f"AI Proposed Merge for {file_path}", border_style="cyan"))

            if Confirm.ask("Apply this resolution?"):
                full_path = (root / file_path) if root else file_path
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(solution.resolved_content)
                subprocess.run(["git", "add", file_path])
                console.print(f"[bold green]✓ Resolved and staged {file_path}[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Failed to resolve {file_path}: {e}[/bold red]")

if __name__ == "__main__":
    app()