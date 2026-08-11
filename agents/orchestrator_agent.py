"""
Orchestrator Agent — Master coordinator for the AI Analytics Dashboard.
Runs fleet supervision loop: keeps idle/stopped background agents alive (Task 8.3).
"""

import os
import json
import time
import sys
import argparse
from pathlib import Path
from typing import Optional
from datetime import datetime
import anthropic
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
AGENTS_DIR = Path(__file__).parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import utf8_fix  # noqa: E402 — Windows console encoding

from memory_manager import load_state, save_state, update_agent_status, log_task_result, get_dynamic_agent_statuses
from plane_agent import get_or_create_project
from git_agent import init_repo, setup_git_config
from fleet_health import ensure_fleet_running, fleet_snapshot
from server_health import ensure_servers_running

load_dotenv()
console = Console()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

from agent_config_loader import load_agent_config, get_fleet_config


class OrchestratorAgent:
    """Master agent — daily bootstrap + continuous fleet supervision."""

    def __init__(self):
        self.config = load_agent_config().get("orchestrator", {})
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
        self.state = load_state()
        self.project_id: Optional[str] = None

    def _print_status(self):
        table = Table(title="AI Analytics Dashboard — Agent Status", style="bold")
        table.add_column("Agent", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Task", style="white")

        for name, info in get_dynamic_agent_statuses().items():
            status = info.get("status", "idle")
            task = info.get("current_task", "Idle")
            color = {"idle": "dim", "running": "yellow", "completed": "green"}.get(status, "dim")
            table.add_row(name.title(), f"[{color}]{status}[/{color}]", (task or "Idle")[:48])

        console.print(table)

    def run_daily_session(self):
        console.print(Panel.fit(
            "[bold magenta]Orchestrator Agent — bootstrap[/bold magenta]\n"
            f"[dim]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
            border_style="magenta"
        ))

        update_agent_status("orchestrator", "running", "Bootstrap session")
        self._print_status()

        if not self.state.get("plane_project_id") and os.getenv("PLANE_API_TOKEN"):
            try:
                self.project_id = get_or_create_project()
                self.state["plane_project_id"] = self.project_id
                save_state(self.state)
            except Exception as e:
                console.print(f"[yellow]Plane setup skipped: {e}[/yellow]")
        else:
            self.project_id = self.state.get("plane_project_id")

        try:
            init_repo()
            setup_git_config()
        except Exception as e:
            console.print(f"[yellow]Git bootstrap skipped: {e}[/yellow]")
        console.print("[bold green]Bootstrap complete — entering fleet supervision[/bold green]")

    def supervise_fleet(self, poll_interval: int | None = None):
        """Keep servers and background agents running; restart any that stopped."""
        self.run_daily_session()
        fleet = get_fleet_config()
        interval = poll_interval or fleet["orchestrator_poll_interval_seconds"]

        while True:
            snap = fleet_snapshot()
            down = [n for n, up in snap.items() if not up]
            task_msg = "Fleet supervisor — all agents online" if not down else f"Restarting: {', '.join(down)}"

            update_agent_status("orchestrator", "running", task_msg)

            ensure_servers_running(wait_seconds=8)
            restarted = ensure_fleet_running(include_orchestrator=False)

            if restarted:
                console.print(f"[cyan][orchestrator] Restarted: {', '.join(restarted)}[/cyan]")
            elif down:
                console.print(f"[yellow][orchestrator] Waiting for agents to come up: {', '.join(down)}[/yellow]")

            time.sleep(interval)

    def mark_task_done(self, task_id: str, task_title: str):
        from plane_agent import update_task_status, add_comment
        if self.project_id:
            try:
                update_task_status(self.project_id, task_id, "completed")
                add_comment(self.project_id, task_id, f"Completed by AI Agent at {datetime.now().strftime('%H:%M')}")
            except Exception as e:
                console.print(f"[yellow]Could not update Plane: {e}[/yellow]")

        log_task_result(task_id, task_title, "orchestrator", "completed", f"Task completed at {datetime.now().isoformat()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orchestrator Agent")
    parser.add_argument("--supervise", action="store_true", help="Run continuous fleet supervisor (default)")
    parser.add_argument("--once", action="store_true", help="Run bootstrap only, then exit")
    parser.add_argument("--interval", type=int, default=30, help="Supervisor poll interval seconds")
    args = parser.parse_args()

    agent = OrchestratorAgent()
    if args.once:
        agent.run_daily_session()
        update_agent_status("orchestrator", "idle", "Bootstrap completed")
    else:
        fleet = get_fleet_config()
        agent.supervise_fleet(poll_interval=args.interval or fleet["orchestrator_poll_interval_seconds"])
