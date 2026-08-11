"""
Orchestrator Agent — Master coordinator for the AI Analytics Dashboard.
Reads state, assigns tasks to sub-agents, and manages sprint progress (< 220 lines).
"""

import os
import json
import time
import sys
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
if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))

from memory_manager import load_state, save_state, update_agent_status, log_task_result
from plane_agent import get_or_create_project, list_tasks, update_task_status, add_comment
from git_agent import init_repo, setup_git_config

load_dotenv()
console = Console()
AGENT_CONFIG_FILE = ROOT_DIR / "config" / "agent_config.json"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


def load_agent_config() -> dict:
    if AGENT_CONFIG_FILE.exists():
        with open(AGENT_CONFIG_FILE) as f:
            return json.load(f)
    return {"orchestrator": {"model": "claude-opus-4-5", "max_tokens": 2048, "system_prompt": "You are master orchestrator."}}


class OrchestratorAgent:
    """Master agent coordinating daily sessions and agent workflow."""

    def __init__(self):
        self.config = load_agent_config().get("orchestrator", {})
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
        self.state = load_state()
        self.messages = []
        self.project_id: Optional[str] = None

    def _print_status(self):
        table = Table(title="🚀 AI Analytics Dashboard — Agent Status", style="bold")
        table.add_column("Agent", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Task", style="white")

        agents = self.state.get("agents", {})
        for name, info in agents.items():
            status = info.get("status", "idle")
            task = info.get("current_task", "Idle")
            color = {"idle": "dim", "running": "yellow", "completed": "green"}.get(status, "dim")
            table.add_row(name.title(), f"[{color}]{status}[/{color}]", task[:40])

        console.print(table)

    def run_daily_session(self):
        console.print(Panel.fit(
            "[bold magenta]🤖 Orchestrator Agent Starting...[/bold magenta]\n"
            f"[dim]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
            border_style="magenta"
        ))

        update_agent_status("orchestrator", "running", "Daily session")
        self._print_status()

        if not self.state.get("plane_project_id") and os.getenv("PLANE_API_TOKEN"):
            try:
                self.project_id = get_or_create_project()
                self.state["plane_project_id"] = self.project_id
                save_state(self.state)
            except Exception as e:
                console.print(f"[yellow]⚠️  Plane setup skipped: {e}[/yellow]")
        else:
            self.project_id = self.state.get("plane_project_id")

        init_repo()
        setup_git_config()
        update_agent_status("orchestrator", "idle", "Daily session completed")
        console.print("[bold green]✅ Orchestrator session complete![/bold green]")
        return "Session Complete"

    def mark_task_done(self, task_id: str, task_title: str):
        if self.project_id:
            try:
                update_task_status(self.project_id, task_id, "completed")
                add_comment(self.project_id, task_id, f"✅ Completed by AI Agent at {datetime.now().strftime('%H:%M')}")
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not update Plane: {e}[/yellow]")

        log_task_result(task_id, task_title, "orchestrator", "completed", f"Task completed successfully at {datetime.now().isoformat()}")


if __name__ == "__main__":
    agent = OrchestratorAgent()
    agent.run_daily_session()
