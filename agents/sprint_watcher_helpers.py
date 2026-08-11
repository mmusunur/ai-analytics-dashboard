"""
Sprint Watcher Helpers — Rich table formatting and status sync helpers for Sprint Watcher Agent.
Keeps agents/sprint_watcher_agent.py lightweight (< 250 lines).
"""

from rich.console import Console
from rich.table import Table

console = Console(legacy_windows=False)


def render_sprint_table(tasks: list, poll_count: int, timestamp: str):
    """Render a clean Rich terminal table summarizing current sprint tasks."""
    table = Table(
        title=f"Sprint Status — {timestamp}",
        title_style="bold magenta",
        header_style="bold cyan",
        border_style="dim"
    )
    table.add_column("Priority", style="dim", width=10)
    table.add_column("Task", style="bold white", width=40)
    table.add_column("State", width=15)
    table.add_column("Points", justify="right", width=6)

    for t in tasks:
        prio = t.get("priority", "NONE").upper()
        state = t.get("state_group", "backlog")
        name = t.get("name", "Untitled")

        # Color coding state
        if state in ("done", "completed"):
            state_str = f"[green]DONE ({state})[/green]"
        elif state in ("started", "in_progress"):
            state_str = f"[yellow]ACTIVE ({state})[/yellow]"
        elif state == "cancelled":
            state_str = f"[red]CANCELLED ({state})[/red]"
        else:
            state_str = f"[dim]OPEN ({state})[/dim]"

        table.add_row(
            prio if prio != "NONE" else "",
            name[:38],
            state_str,
            str(t.get("estimate_point", "") or "")
        )

    console.print(table)


IN_PROGRESS_GROUPS = {"started", "in_progress"}


def quality_gate_action(test_passed: bool, builder_ran: bool) -> str:
    """
    Task 34 — Sprint close quality gate.
    Returns: 'complete' | 'revert_todo' | 'leave_in_progress'
    """
    if test_passed:
        return "complete"
    if builder_ran:
        return "revert_todo"
    return "leave_in_progress"
