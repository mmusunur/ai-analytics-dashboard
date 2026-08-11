"""
Sprint Watcher Agent — Continuously monitors Plane sprint activity across projects.
Lightweight & Modularized (< 250 lines).
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "agents"))
import utf8_fix
load_dotenv(ROOT_DIR / ".env")
console = Console(force_terminal=True)

from plane_agent import get_or_create_project, list_projects, list_tasks, get_single_task, update_task_status, add_comment
from memory_manager import update_agent_status, set_agent_working, log_task_result, load_state, save_state
from sprint_watcher_helpers import render_sprint_table

STATE_TODO    = "unstarted"   # Plane group: unstarted (To Do)
STATE_INPROG  = "started"    # Plane group: started  (In Progress)
STATE_DONE    = "completed"  # Plane group: completed (Done)
# NOTE: STATE_FAILED is intentionally removed — cancelling is a HUMAN-ONLY action.
# The agent must NEVER auto-cancel tasks.

# Groups that are safe for the agent to auto-pick up for processing.
# 'backlog' is included because Plane sometimes returns 'backlog' for new unstarted tasks.
AGENT_PICKUP_GROUPS = {"unstarted", "todo", "triaged", "backlog"}
# Groups that mean a task is already being worked on / closed — NEVER auto-pick
AGENT_SKIP_GROUPS   = {"started", "in_progress", "completed", "done", "cancelled", "wont_fix", "rejected"}

# Persistent processed-task file — survives across watcher instances so re-spawned
# watchers don't re-pick tasks that were already handled this session.
_PROCESSED_IDS_FILE = ROOT_DIR / "memory" / ".processed_task_ids.json"


import json
from datetime import datetime, timedelta


def _load_processed_ids() -> set:
    """Load persisted processed task IDs. IDs older than 24 hours are auto-expired."""
    try:
        if _PROCESSED_IDS_FILE.exists():
            data = json.loads(_PROCESSED_IDS_FILE.read_text(encoding="utf-8"))
            cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
            # New format: {"entries": [{"id": ..., "at": ISO_TIMESTAMP}, ...]}
            entries = data.get("entries", [])
            if entries:
                valid = [e for e in entries if isinstance(e, dict) and e.get("at", "") >= cutoff]
                return set(e["id"] for e in valid)
            # Legacy format: {"ids": [...]}
            return set(data.get("ids", []))
    except Exception:
        pass
    return set()


def _save_processed_ids(ids: set) -> None:
    """Persist processed task IDs with timestamps so they auto-expire after 24 hours."""
    try:
        _PROCESSED_IDS_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Preserve existing timestamps; add new ones for IDs we haven't seen before
        existing = {}
        if _PROCESSED_IDS_FILE.exists():
            try:
                data = json.loads(_PROCESSED_IDS_FILE.read_text(encoding="utf-8"))
                for e in data.get("entries", []):
                    if isinstance(e, dict):
                        existing[e["id"]] = e.get("at", datetime.now().isoformat())
            except Exception:
                pass
        now = datetime.now().isoformat()
        entries = [{"id": tid, "at": existing.get(tid, now)} for tid in ids]
        _PROCESSED_IDS_FILE.write_text(
            json.dumps({"entries": entries}, indent=2), encoding="utf-8"
        )
    except Exception:
        pass


def _clear_processed_ids() -> int:
    """Delete persisted processed task IDs entirely. Returns count cleared."""
    try:
        if _PROCESSED_IDS_FILE.exists():
            data = json.loads(_PROCESSED_IDS_FILE.read_text(encoding="utf-8"))
            count = len(data.get("entries", data.get("ids", [])))
            _PROCESSED_IDS_FILE.unlink()
            return count
    except Exception:
        pass
    return 0


class SprintWatcherAgent:
    """Watches active Plane sprint across workspace projects: Backlog/Todo → In Progress → Tests → Done."""

    def __init__(self, poll_interval_seconds: int = 15):
        self.poll_interval = poll_interval_seconds
        self.project_id: Optional[str] = None
        self.workspace_slug: str = "agentbuilder"
        self.state = load_state()
        # Task deduplication: persisted across instances to prevent re-pickup of already-handled tasks.
        self._processed_task_ids: set = _load_processed_ids()

    def _init_project(self) -> bool:
        self.workspace_slug = self.state.get("plane_workspace_slug") or "agentbuilder"
        self.project_id = self.state.get("plane_project_id") or "all"
        return True

    def _fetch_sprint_tasks(self) -> List[Dict]:
        try:
            ws = self.workspace_slug
            pid = self.project_id
            if not pid or pid == "all":
                all_projects = list_projects(ws)
                all_tasks = []
                for p in all_projects:
                    p_id = p.get("id")
                    if p_id:
                        p_tasks = list_tasks(p_id, ws)
                        for t in p_tasks:
                            t["project_id"] = p_id
                            t["project_name"] = p.get("name", "Project")
                            all_tasks.append(t)
                return all_tasks
            else:
                p_tasks = list_tasks(pid, ws)
                for t in p_tasks:
                    t["project_id"] = pid
                return p_tasks
        except Exception as e:
            console.print(f"[yellow]⚠️ Failed to fetch tasks: {e}[/yellow]")
            return []

    def _run_builder(self, task_id: str, task_title: str, description: str, priority: str) -> bool:
        console.print(f"[cyan]🔨 Invoking Builder Agent for: {task_title}[/cyan]")
        try:
            cmd = [
                sys.executable,
                str(ROOT_DIR / "agents" / "builder_agent.py"),
                "--task-id", task_id,
                "--task-title", task_title,
                "--description", description or task_title,
                "--priority", priority,
            ]
            result = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, encoding="utf-8", errors="replace", timeout=120)
            if result.returncode == 0:
                console.print(f"[green]✅ Builder completed: {task_title}[/green]")
                return True
            else:
                console.print(f"[red]❌ Builder failed:\n{result.stderr[:300]}[/red]")
                return False
        except Exception as e:
            console.print(f"[red]❌ Builder exception: {e}[/red]")
            return False

    def _run_tests(self) -> tuple[bool, str]:
        console.print("[cyan]🧪 Running Core Unit Tests...[/cyan]")
        try:
            cmd = [sys.executable, "-m", "pytest", "tests/unit/", "-v", "--tb=short", "-q"]
            res = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, encoding="utf-8", errors="replace", timeout=120)
            passed = (res.returncode == 0)
            output = res.stdout[:500] if passed else res.stderr[:500]
            if passed:
                console.print("[green]✅ Unit Tests PASSED[/green]")
            else:
                console.print(f"[red]❌ Unit Tests FAILED:\n{output}[/red]")
            return passed, output
        except Exception as e:
            return False, f"Test error: {e}"

    def _finalize_task(self, project_id: str, task_id: str, task_title: str, success: bool, output: str, duration: float, builder_ran: bool = True):
        """
        Finalize task state in Plane:
        - Builder made real changes AND tests PASS  → STATE_DONE (completed)
        - Builder made NO code changes              → leave In Progress, add comment for manual review
        - Tests FAIL after builder ran              → move back to STATE_TODO (unstarted/To Do)
                                                      NOT cancelled — cancelled is a human-only action
        """
        target_pid = project_id or self.project_id
        try:
            if not builder_ran:
                # Builder found no actionable code changes — leave In Progress, flag for manual review
                add_comment(
                    target_pid, task_id,
                    f"🤖 Sprint Watcher: Builder found no actionable code changes for this task ({duration}s).\n"
                    f"Task left In Progress — manual developer review required.\nTask: {task_title}",
                    self.workspace_slug
                )
                console.print(f"[yellow]⚠️ Task left In Progress (no code changes made): {task_title}[/yellow]")
            elif success:
                # Tests PASSED — mark as Done in Plane
                update_task_status(target_pid, task_id, STATE_DONE, self.workspace_slug)
                add_comment(
                    target_pid, task_id,
                    f"🤖 Sprint Watcher: Implementation COMPLETE ✅ ({duration}s). Tests PASSED.\n{output[:300]}",
                    self.workspace_slug
                )
                console.print(f"[green]✅ Task marked Done: {task_title}[/green]")
            else:
                # Tests FAILED — move back to To Do (NOT cancelled)
                # Remove from processed set so it can be retried after developer review
                self._processed_task_ids.discard(task_id)
                update_task_status(target_pid, task_id, STATE_TODO, self.workspace_slug)
                add_comment(
                    target_pid, task_id,
                    f"🤖 Sprint Watcher: Tests FAILED ❌ ({duration}s). Code changes rolled back. "
                    f"Task returned to To Do for developer review.\n\nTest output:\n{output[:400]}",
                    self.workspace_slug
                )
                console.print(f"[red]❌ Tests failed. Task moved back to To Do: {task_title}[/red]")
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not finalize task status: {e}[/yellow]")

        log_task_result(task_id, task_title, "SprintWatcherAgent", "completed" if success else "failed", output, duration)
        update_agent_status("sprint_watcher", "idle", "Sprint Watcher Agent Active (Monitoring)")

    def _resolve_project_id(self, task: dict) -> Optional[str]:
        """
        Resolve the REAL Plane project ID for a task.
        Never returns 'all' — always returns an actual UUID.
        Priority: task['project_id'] → state['plane_project_id'] → first project from API
        """
        pid = task.get("project_id") or ""
        if pid and pid != "all" and len(pid) > 10:
            return pid
        # Try state
        state_pid = (self.state or {}).get("plane_project_id") or ""
        if state_pid and state_pid != "all" and len(state_pid) > 10:
            return state_pid
        # Last resort: scan workspace projects for first real project ID
        try:
            projects = list_projects(self.workspace_slug)
            if projects:
                real_pid = projects[0].get("id")
                console.print(f"[dim]→ project_id resolved from workspace scan: {real_pid[:8]}...[/dim]")
                return real_pid
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not resolve project_id: {e}[/yellow]")
        return None

    def _verify_task_still_pickupable(self, project_id: str, task_id: str) -> bool:
        """
        Re-fetch the task's LIVE state from Plane API right before processing.
        Returns True only if the task is still in a pickupable state (unstarted/todo/triaged/backlog).
        CRITICAL: project_id must be a real UUID — never 'all'. Use _resolve_project_id() first.
        """
        if not project_id or project_id == "all":
            console.print(f"[yellow]⚠️ project_id is '{project_id}' for task {task_id[:8]} — skipping live verify, proceeding optimistically.[/yellow]")
            return True  # BUG FIX: was returning False, permanently blocking pickup. Now optimistic.

        live_task = get_single_task(project_id, task_id, self.workspace_slug)
        if live_task is None:
            # Plane API failed — do NOT silently block pickup; proceed optimistically
            # (better to try than to permanently skip a task due to a transient API error)
            console.print(f"[yellow]⚠️ Could not re-verify live state for {task_id[:8]} (API error) — proceeding optimistically.[/yellow]")
            return True

        live_group = (
            (live_task.get("state_detail") or {}).get("group")
            or live_task.get("state_group")
            or "backlog"
        ).lower()

        console.print(f"[dim]  Live state check: task {task_id[:8]} → group='{live_group}'[/dim]")

        if live_group in AGENT_SKIP_GROUPS:
            console.print(
                f"[yellow]⚠️ Task {task_id[:8]} is '{live_group}' in Plane — "
                f"skipping (already In Progress / Done / Cancelled by user or agent).[/yellow]"
            )
            return False

        if live_group not in AGENT_PICKUP_GROUPS:
            console.print(f"[yellow]⚠️ Task {task_id[:8]} has group '{live_group}' which is not in pickup groups — skipping.[/yellow]")
            return False

        console.print(f"[green]✅ Task {task_id[:8]} confirmed pickupable (live group: '{live_group}')[/green]")
        return True

    def _handle_new_task(self, task: dict) -> bool:
        task_id = task["id"]
        task_title = task.get("name", "Unknown Task")
        priority = task.get("priority", "medium")
        desc = task.get("description", "") or ""

        # ── CRITICAL: resolve a real project UUID — never "all" ────────────────
        project_id = self._resolve_project_id(task)
        if not project_id:
            console.print(f"[red]✗ Skipping '{task_title}' — could not resolve a real project_id (got 'all' or None).[/red]")
            return False

        # ── Live state verification guard ──────────────────────────────────────
        # Re-fetch from Plane API to prevent race: user moved task to In Progress
        # while watcher's list_tasks call still had it as 'unstarted'.
        if not self._verify_task_still_pickupable(project_id, task_id):
            # Do NOT add to processed IDs here — the task might become pickupable later
            return False

        start_time = time.time()
        console.print(Panel(
            f"[bold]New Task Picked Up![/bold]\n"
            f"Title:    {task_title}\n"
            f"ID:       {task_id}\n"
            f"Priority: {priority.upper()}\n"
            f"Project:  {task.get('project_name', project_id)}",
            border_style="cyan"
        ))

        # Step 1: Move task to In Progress in Plane
        # BUG FIX: Only mark as processed AFTER successful status update.
        # Previously, tasks were added to processed IDs BEFORE this step,
        # meaning a failed status update would permanently blacklist the task for 24h.
        status_updated = False
        try:
            result = update_task_status(project_id, task_id, STATE_INPROG, self.workspace_slug)
            if result:
                console.print(f"[green]✅ Plane: Task moved to In Progress[/green]")
                status_updated = True
            else:
                console.print(f"[yellow]⚠️ Plane: Could not update to In Progress (state not found). Will retry next cycle.[/yellow]")
        except Exception as e:
            console.print(f"[yellow]⚠️ Plane status update error: {e}. Will retry next cycle.[/yellow]")

        if not status_updated:
            # Status update failed — do NOT mark as processed so we retry next cycle
            console.print(f"[yellow]↩️ Task '{task_title}' NOT marked processed — will retry on next watcher cycle.[/yellow]")
            return False

        # Mark as processed only now that we've successfully claimed the task in Plane
        self._processed_task_ids.add(task_id)
        _save_processed_ids(self._processed_task_ids)

        update_agent_status("sprint_watcher", "running", f"ACTIVE TASK: [{task_id[:8]}] {task_title}")

        # ── Step 2+3: Build + Test — set agent_working=True so frontend PAUSES polling ──
        # This prevents the UI from breaking/going unresponsive while the builder
        # modifies files and uvicorn hot-reloads the backend.
        build_success = False
        test_success = False
        test_output = ""
        try:
            set_agent_working(True, task_title)
            console.print(f"[magenta]🔒 Agent working flag SET — frontend polling paused during code changes[/magenta]")

            # Step 2: Run builder (LLM code generation)
            build_success = self._run_builder(task_id, task_title, desc, priority)

            # Step 3: Run tests only if builder succeeded
            test_success, test_output = (
                self._run_tests() if build_success
                else (False, "Builder made no code changes or failed")
            )
        finally:
            set_agent_working(False)
            console.print(f"[magenta]🔓 Agent working flag CLEARED — frontend polling resumed[/magenta]")

        duration = round(time.time() - start_time, 2)
        self._finalize_task(project_id, task_id, task_title, test_success, test_output, duration, build_success)
        return test_success


    def watch(self, max_cycles: Optional[int] = None):
        if not self._init_project():
            return

        console.print(Panel.fit("Sprint Watcher Agent — Running Across Workspace Projects", border_style="magenta"))
        cycle = 0

        while True:
            cycle += 1
            tasks = self._fetch_sprint_tasks()
            render_sprint_table(tasks, cycle, datetime.now().strftime("%H:%M:%S"))

            priority_weights = {"urgent": 4, "high": 3, "medium": 2, "low": 1}

            def _get_group(t: dict) -> str:
                return (t.get("state_detail", {}).get("group") or t.get("state_group") or "backlog").lower()

            # Only pick tasks explicitly in a pickupable state.
            # AGENT_PICKUP_GROUPS = {"unstarted", "todo", "triaged", "backlog"}
            # "started"   = already In Progress — could be a human working on it, NEVER re-pick
            # "cancelled" = closed by human — NEVER auto-pick
            # "completed" = already done — NEVER re-pick
            actionable = [
                t for t in tasks
                if _get_group(t) in AGENT_PICKUP_GROUPS
                and t.get("id") not in self._processed_task_ids
                and not t.get("completed_at")
            ]

            # Log detailed skip reasons for every non-actionable task for debugging
            skipped_details = []
            for t in tasks:
                tid = t.get("id", "?")
                grp = _get_group(t)
                if grp not in AGENT_PICKUP_GROUPS:
                    skipped_details.append(f"  ↷ [{tid[:8]}] '{t.get('name','?')[:40]}' — group='{grp}' (not pickupable)")
                elif tid in self._processed_task_ids:
                    skipped_details.append(f"  ↷ [{tid[:8]}] '{t.get('name','?')[:40]}' — already processed this session")
                elif t.get("completed_at"):
                    skipped_details.append(f"  ↷ [{tid[:8]}] '{t.get('name','?')[:40]}' — has completed_at timestamp")

            console.print(f"[dim]Cycle {cycle}: {len(tasks)} total tasks | {len(actionable)} ready for pickup | {len(self._processed_task_ids)} already processed this session[/dim]")
            if skipped_details:
                for line in skipped_details:
                    console.print(f"[dim]{line}[/dim]")
            if not actionable:
                console.print(f"[dim]  → No actionable tasks found. Sleeping {self.poll_interval}s...[/dim]")

            # Sort so URGENT / HIGH priority items are processed first
            actionable.sort(key=lambda t: priority_weights.get((t.get("priority") or "medium").lower(), 2), reverse=True)

            for task in actionable:
                grp = _get_group(task)
                console.print(f"[cyan]→ Picking up [{grp.upper()}] task: {task.get('name')} (priority: {task.get('priority', 'medium')})[/cyan]")
                self._handle_new_task(task)
                time.sleep(1.0)

            if max_cycles and cycle >= max_cycles:
                break

            time.sleep(self.poll_interval)


if __name__ == "__main__":
    watcher = SprintWatcherAgent(poll_interval_seconds=15)
    watcher.watch(max_cycles=1)
