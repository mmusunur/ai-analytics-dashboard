"""
Run Agents — Main entry point for the agent system.
Starts the Orchestrator which coordinates all sub-agents.
"""

import sys
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "agents"))
load_dotenv(ROOT_DIR / ".env")

console = Console()


def check_env():
    """Validate required environment variables."""
    issues = []
    if not os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY") == "your_anthropic_api_key_here":
        issues.append("ANTHROPIC_API_KEY not set")
    return issues


def main():
    console.print(Panel.fit(
        "[bold magenta]🤖 AI Analytics Dashboard — Agent System[/bold magenta]\n"
        "[dim]Starting all agents...[/dim]",
        border_style="magenta"
    ))

    # Environment check
    issues = check_env()
    if issues:
        console.print("[yellow]⚠️  Configuration issues:[/yellow]")
        for issue in issues:
            console.print(f"  [red]• {issue}[/red]")
        console.print("\n[dim]Please run: python scripts/setup.py[/dim]")
        if "ANTHROPIC_API_KEY not set" in issues:
            console.print("[yellow]Agents require ANTHROPIC_API_KEY to run.[/yellow]")
            sys.exit(1)

    # Import and run orchestrator
    from orchestrator_agent import OrchestratorAgent
    agent = OrchestratorAgent()
    agent.supervise_fleet(poll_interval=30)


if __name__ == "__main__":
    main()
