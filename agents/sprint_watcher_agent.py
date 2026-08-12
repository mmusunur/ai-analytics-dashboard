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
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "agents"))
import utf8_fix
load_dotenv(ROOT_DIR / ".env")
console = Console(force_terminal=True)

from plane_agent import get_or_create_project, list_projects, list_tasks, get_single_task, update_task_status, add_comment
from memory_manager import (
    update_agent_status, set_agent_working, log_task_result, load_state, save_state,
    set_pipeline_status, sync_pending_tasks, set_queue_active,
    complete_queue_task, fail_queue_task, get_task_queue,
    mark_pipeline_step_complete, reset_pipeline_steps, rewind_pipeline_to_step,
    clear_build_progress, clear_test_progress,
)
from sprint_watcher_helpers import render_sprint_table, IN_PROGRESS_GROUPS, quality_gate_action

STATE_TODO    = "unstarted"   # Plane group: unstarted (To Do)
STATE_INPROG  = "started"    # Plane group: started  (In Progress)
STATE_DONE    = "completed"  # Plane group: completed (Done)
# NOTE: STATE_FAILED is intentionally removed — cancelling is a HUMAN-ONLY action.
# The agent must NEVER auto-cancel tasks.

# Groups that are safe for the agent to auto-pick up for processing.
AGENT_PICKUP_GROUPS = {"unstarted", "todo", "triaged"}
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
        self._verify_close_attempts: dict[str, float] = {}
        self.verify_close_cooldown = int(os.getenv("SPRINT_VERIFY_CLOSE_COOLDOWN", "45"))
        self._active_poll_interval = int(os.getenv("SPRINT_ACTIVE_POLL_INTERVAL", "15"))

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

    def _run_builder(
        self,
        task_id: str,
        task_title: str,
        description: str,
        priority: str,
        attempt: int = 1,
        test_failure_output: str = "",
    ) -> tuple[bool, str]:
        console.print(f"[cyan]🔨 Invoking Builder Agent for: {task_title} (attempt {attempt})[/cyan]")
        retry_context_file = ""
        if test_failure_output:
            ctx_path = ROOT_DIR / "memory" / f".retry_context_{task_id[:8]}.txt"
            try:
                ctx_path.write_text(test_failure_output, encoding="utf-8")
                retry_context_file = str(ctx_path)
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not write retry context: {e}[/yellow]")
        try:
            cmd = [
                sys.executable,
                str(ROOT_DIR / "agents" / "builder_agent.py"),
                "--task-id", task_id,
                "--task-title", task_title,
                "--description", description or task_title,
                "--priority", priority,
                "--attempt", str(attempt),
            ]
            if retry_context_file:
                cmd.extend(["--retry-context-file", retry_context_file])
            result = subprocess.run(
                cmd, cwd=str(ROOT_DIR), capture_output=True,
                encoding="utf-8", errors="replace", timeout=300,
                env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
            )
            output = ((result.stdout or "") + (result.stderr or ""))[:800]
            if result.returncode == 0:
                console.print(f"[green]✅ Builder completed: {task_title}[/green]")
                return True, output
            console.print(f"[red]❌ Builder failed:\n{output[:300]}[/red]")
            return False, output or "Builder agent returned non-zero exit code"
        except Exception as e:
            msg = f"Builder exception: {e}"
            console.print(f"[red]❌ {msg}[/red]")
            return False, msg

    def _run_tests(
        self,
        task_id: str = "",
        task_title: str = "",
        description: str = "",
        project_name: str = "",
        mode: str = "full",
    ) -> tuple[bool, str]:
        """Run quality gate via Tester Agent (full after Build; fast for verify-close)."""
        fast = mode == "fast"
        label = "Fast quality gate (unit + smoke + sprint cases)" if fast else "Full test suite (unit + browser + sprint)"
        console.print(f"[cyan]🧪 Running {label} via Tester Agent...[/cyan]")
        update_agent_status("tester", "running", "Fast quality gate" if fast else "Full test suite")

        sys.path.insert(0, str(ROOT_DIR / "scripts"))
        wait_seconds = 10 if fast else 25
        try:
            from server_health import ensure_servers_running, servers_healthy
            if not servers_healthy()["healthy"]:
                console.print("[yellow]⚠️ Servers not up — auto-starting backend & frontend before tests...[/yellow]")
            if not ensure_servers_running(wait_seconds=wait_seconds):
                return False, "Quality gate aborted: backend (:8000) or frontend (:5173) not reachable."
        except Exception as e:
            console.print(f"[yellow]⚠️ Server health pre-check warning: {e}[/yellow]")

        try:
            cmd = [sys.executable, str(ROOT_DIR / "agents" / "tester_agent.py"), "--mode", mode]
            if task_id:
                cmd.extend(["--task-id", task_id])
            if task_title:
                cmd.extend(["--task-title", task_title])
            if description:
                cmd.extend(["--description", description])
            if project_name:
                cmd.extend(["--project-name", project_name])
            timeout = 300 if fast else 900
            res = subprocess.run(
                cmd, cwd=str(ROOT_DIR), capture_output=True,
                encoding="utf-8", errors="replace", timeout=timeout,
                env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
            )
            output = ((res.stdout or "") + (res.stderr or ""))[:800]
            passed = res.returncode == 0
            if passed:
                console.print(f"[green]✅ {'Fast' if fast else 'Full'} test gate PASSED[/green]")
            else:
                console.print(f"[red]❌ Test gate FAILED:\n{output[:400]}[/red]")
            return passed, output
        except Exception as e:
            return False, f"Test error: {e}"
        finally:
            update_agent_status("tester", "idle", "Idle")

    def _run_git_commit(self, task_id: str, task_title: str) -> bool:
        """Stage meaningful repo files and commit/push after task close. Always runs (incl. verify-close)."""
        console.print("[cyan]📦 Running Git gate for completed task...[/cyan]")
        update_agent_status("git_agent", "running", f"Commit: {task_title[:40]}")
        try:
            from git_agent import commit_and_push_for_task
            result = commit_and_push_for_task(task_title, task_id)
            if result["ok"]:
                if result.get("files"):
                    console.print(
                        f"[green]✅ Git gate passed — {len(result['files'])} file(s) committed/pushed[/green]"
                    )
                else:
                    console.print("[green]✅ Git gate passed — working tree clean[/green]")
                update_agent_status("git_agent", "idle", "Idle")
                return True
            console.print(f"[red]❌ Git gate failed: {result.get('message')}[/red]")
            update_agent_status("git_agent", "idle", f"Git failed: {result.get('message', '')[:60]}")
            return False
        except Exception as e:
            console.print(f"[yellow]⚠️ Git commit error: {e}[/yellow]")
            update_agent_status("git_agent", "idle", "Git error")
            return False

    def _sweep_pending_git(self) -> None:
        """Retry git for any meaningful uncommitted files left from prior closes."""
        try:
            from git_agent import get_meaningful_changed_files, commit_and_push_for_task
            pending = get_meaningful_changed_files()
            if not pending:
                return
            console.print(
                f"[yellow]↻ Git sweep: {len(pending)} uncommitted meaningful file(s) — committing...[/yellow]"
            )
            commit_and_push_for_task("Pending repo sync", "git-sweep")
        except Exception as e:
            console.print(f"[dim]Git sweep skipped: {e}[/dim]")

    def _max_retry_attempts(self) -> int:
        return max(1, int(os.getenv("SPRINT_MAX_RETRY_ATTEMPTS", "10")))

    def _max_outer_cycles(self) -> int:
        """Task 37 — full pickup→build→test cycles before marking permanently failed."""
        return max(1, int(os.getenv("SPRINT_MAX_OUTER_CYCLES", "50")))

    def _prepare_auto_repick_cycle(
        self,
        project_id: str,
        task_id: str,
        task_title: str,
        test_output: str,
        outer: int,
        outer_max: int,
    ) -> None:
        """Move task To Do → wait → ready for automatic re-pick (zero human steps)."""
        msg = f"Outer cycle {outer}/{outer_max} failed — auto moving To Do and re-picking"
        set_pipeline_status("pickup", task_id, task_title, "sprint_watcher", msg)
        self._processed_task_ids.discard(task_id)
        _save_processed_ids(self._processed_task_ids)
        try:
            update_task_status(project_id, task_id, STATE_TODO, self.workspace_slug)
            add_comment(
                project_id, task_id,
                f"🤖 Sprint Watcher (Task 37): Inner retries exhausted on outer cycle {outer}/{outer_max}.\n"
                f"Agent auto-moving to To Do and re-picking — no manual action required.\n\n"
                f"{test_output[:300]}",
                self.workspace_slug,
            )
        except Exception as e:
            console.print(f"[yellow]⚠️ Auto-repick Plane update warning: {e}[/yellow]")
        console.print(f"[cyan]↻ Auto re-pick scheduled — outer cycle {outer + 1}/{outer_max}[/cyan]")
        time.sleep(3)

    def _claim_task_in_progress(self, project_id: str, task_id: str, task_title: str, task: dict) -> bool:
        """Move Plane task to In Progress and mark processed."""
        priority = task.get("priority", "medium")
        set_pipeline_status("pickup", task_id, task_title, "sprint_watcher", "Task picked up from Plane sprint board")
        set_queue_active(task_id, task_title, task.get("project_name", ""), priority)
        try:
            result = update_task_status(project_id, task_id, STATE_INPROG, self.workspace_slug)
            if result:
                console.print(f"[green]✅ Plane: Task moved to In Progress[/green]")
                self._processed_task_ids.add(task_id)
                _save_processed_ids(self._processed_task_ids)
                return True
            console.print("[yellow]⚠️ Plane: Could not update to In Progress — will retry next cycle.[/yellow]")
        except Exception as e:
            console.print(f"[yellow]⚠️ Plane status update error: {e}[/yellow]")
        return False

    def _execute_full_pipeline_until_pass(self, task: dict, *, claim_on_plane: bool = True) -> bool:
        """
        Task 37 — Run build→test inner loop; on failure auto To Do + re-pick until tests pass.
        No human must move tasks on Plane between cycles.
        """
        task_id = task["id"]
        task_title = task.get("name", "Unknown Task")
        priority = task.get("priority", "medium")
        desc = task.get("description", "") or ""
        project_name = task.get("project_name", "")
        project_id = self._resolve_project_id(task)
        if not project_id:
            console.print(f"[red]✗ Skipping '{task_title}' — no project_id[/red]")
            return False

        outer_max = self._max_outer_cycles()
        update_agent_status("sprint_watcher", "running", f"ACTIVE: [{task_id[:8]}] {task_title}")

        for outer in range(1, outer_max + 1):
            if outer == 1 and claim_on_plane:
                if not self._verify_task_still_pickupable(project_id, task_id):
                    return False
                if not self._claim_task_in_progress(project_id, task_id, task_title, task):
                    return False
            else:
                self._processed_task_ids.discard(task_id)
                _save_processed_ids(self._processed_task_ids)
                set_pipeline_status(
                    "pickup", task_id, task_title, "sprint_watcher",
                    f"Auto re-pick outer cycle {outer}/{outer_max} — no manual To Do move needed",
                )
                set_queue_active(task_id, task_title, project_name, priority)
                try:
                    update_task_status(project_id, task_id, STATE_INPROG, self.workspace_slug)
                except Exception:
                    pass
                self._processed_task_ids.add(task_id)
                _save_processed_ids(self._processed_task_ids)

            test_success, test_output, build_success, duration = self._run_build_test_loop(
                project_id, task_id, task_title, desc, priority, project_name,
            )

            if test_success:
                self._finalize_task(project_id, task_id, task_title, True, test_output, duration, build_success)
                return True

            if outer >= outer_max:
                self._finalize_task(project_id, task_id, task_title, False, test_output, duration, build_success)
                return False

            self._prepare_auto_repick_cycle(project_id, task_id, task_title, test_output, outer, outer_max)

        return False

    def _run_build_test_loop(
        self,
        project_id: str,
        task_id: str,
        task_title: str,
        desc: str,
        priority: str,
        project_name: str = "",
    ) -> tuple[bool, str, bool, float]:
        """
        Task 37 — Mandatory step gates: Build MUST pass before Test runs.
        On step failure, retry THE SAME STEP (do not skip ahead).
        """
        max_attempts = self._max_retry_attempts()
        loop_start = time.time()
        failure_context = ""
        any_builder_ran = False
        reset_pipeline_steps(task_id, task_title)
        mark_pipeline_step_complete("pickup")

        for cycle in range(1, max_attempts + 1):
            try:
                # agent_working only during Build (file changes) — UI stays live during Test
                build_ok = False
                build_log = failure_context
                for build_try in range(1, max_attempts + 1):
                    if build_try == 1:
                        set_pipeline_status(
                            "building", task_id, task_title, "builder",
                            "Step 2/6 Build — classifying intent & applying code (see sub-phases below)",
                        )
                    else:
                        set_pipeline_status(
                            "retry", task_id, task_title, "builder",
                            f"Build step failed — retry {build_try}/{max_attempts} (same step, NOT skipping to Test)",
                        )
                    set_agent_working(True, task_title)
                    try:
                        build_ok, build_log = self._run_builder(
                            task_id, task_title, desc, priority, build_try, failure_context,
                        )
                    finally:
                        set_agent_working(False)
                    any_builder_ran = any_builder_ran or build_ok
                    if build_ok:
                        mark_pipeline_step_complete("building")
                        pl = (load_state().get("pipeline") or {})
                        outcome = pl.get("build_outcome", "code_changed")
                        dur = pl.get("build_duration_seconds", 0)
                        files = pl.get("build_files_modified") or []
                        if outcome == "verify_only":
                            msg = (
                                f"Build ✓ verify-only ({dur}s) — requirements already in code; "
                                f"starting full Test gate"
                            )
                        else:
                            msg = (
                                f"Build ✓ {len(files)} file(s) changed ({dur}s) — starting Test gate"
                            )
                        set_pipeline_status("building", task_id, task_title, "builder", msg)
                        clear_build_progress()
                        break
                    console.print(
                        f"[red]⛔ Build gate blocked — attempt {build_try}/{max_attempts} failed. "
                        f"Staying on Build step.[/red]"
                    )
                    failure_context = build_log
                    if build_try < max_attempts:
                        time.sleep(1)

                if not build_ok:
                    console.print("[red]⛔ Build step never passed — Test step will NOT run.[/red]")
                    return False, build_log, any_builder_ran, round(time.time() - loop_start, 2)

                # ── GATE 3: TEST — only after Build passed ───────────────────
                set_pipeline_status(
                    "testing", task_id, task_title, "tester",
                    f"Step 3/6 Test — running quality gate (cycle {cycle}/{max_attempts})",
                )
                set_agent_working(False)
                test_ok, test_output = self._run_tests(
                    task_id, task_title, desc, project_name, mode="full",
                )
                clear_build_progress()
                clear_test_progress()

                if test_ok:
                    mark_pipeline_step_complete("testing")
                    console.print(f"[green]✅ Test gate passed on cycle {cycle}/{max_attempts}[/green]")
                    return True, test_output, any_builder_ran, round(time.time() - loop_start, 2)

                failure_context = test_output
                console.print(
                    f"[red]⛔ Test gate failed cycle {cycle}/{max_attempts} — "
                    f"returning to Build step to fix (not advancing to Close).[/red]"
                )
                rewind_pipeline_to_step("pickup")
                set_pipeline_status(
                    "retry", task_id, task_title, "builder",
                    f"Test failed — fixing via Build step (cycle {cycle + 1 if cycle < max_attempts else cycle})",
                )
                if cycle < max_attempts:
                    time.sleep(1)
            finally:
                set_agent_working(False)

        return False, failure_context, any_builder_ran, round(time.time() - loop_start, 2)

    def _reconcile_processed_ids(self, tasks: List[Dict], _get_group) -> None:
        """Drop processed IDs when Plane shows task is still To Do (incomplete run) or sync completed."""
        changed = False
        for tid in list(self._processed_task_ids):
            task = next((t for t in tasks if t.get("id") == tid), None)
            if not task:
                continue
            grp = _get_group(task)
            if grp in {"completed", "done"}:
                complete_queue_task(tid, task.get("name", "Task"))
                continue
            if grp in AGENT_PICKUP_GROUPS:
                self._processed_task_ids.discard(tid)
                changed = True
                console.print(f"[dim]↻ Task {tid[:8]} back in To Do — removed from processed (will re-pick)[/dim]")
        if changed:
            _save_processed_ids(self._processed_task_ids)

    def _finalize_task(self, project_id: str, task_id: str, task_title: str, success: bool, output: str, duration: float, builder_ran: bool = True):
        """
        Finalize task state in Plane (Task 34 + Task 37):
        - Tests PASS → STATE_DONE (completed)
        - Tests FAIL after auto-retry loop → failed UI + To Do on Plane + auto re-pickup next cycle
        """
        target_pid = project_id or self.project_id
        max_attempts = self._max_retry_attempts()
        action = quality_gate_action(success, builder_ran)
        try:
            if action == "leave_in_progress":
                reason = output[:200] or "Tests failed after auto-retry attempts"
                set_pipeline_status(
                    "failed", task_id, task_title, "tester",
                    f"All {max_attempts} inner × {self._max_outer_cycles()} outer attempts exhausted",
                )
                fail_queue_task(task_id, task_title, reason, max_attempts, max_attempts)
                self._processed_task_ids.discard(task_id)
                _save_processed_ids(self._processed_task_ids)
                update_task_status(target_pid, task_id, STATE_TODO, self.workspace_slug)
                add_comment(
                    target_pid, task_id,
                    f"🤖 Sprint Watcher (Task 37): All auto-retry cycles exhausted ({duration}s).\n"
                    f"Task in To Do — watcher will auto-pick up again on next poll.\n\n"
                    f"Test output:\n{output[:400]}",
                    self.workspace_slug,
                )
                console.print(f"[red]❌ All auto-retry cycles exhausted — will re-pick on next watcher poll: {task_title}[/red]")
            elif action == "complete":
                close_note = (
                    "Implementation COMPLETE ✅"
                    if builder_ran
                    else "Verify-only close: requirements already satisfied — all sprint tests PASSED ✅"
                )
                set_pipeline_status("closing", task_id, task_title, "plane_agent", "Marking task completed on Plane")
                result = update_task_status(target_pid, task_id, STATE_DONE, self.workspace_slug)
                if result:
                    add_comment(
                        target_pid, task_id,
                        f"🤖 Sprint Watcher: {close_note} ({duration}s). Tests PASSED.\n{output[:300]}",
                        self.workspace_slug
                    )
                    console.print(f"[green]✅ Task marked Done on Plane: {task_title}[/green]")
                    mark_pipeline_step_complete("closing")
                else:
                    console.print(f"[yellow]⚠️ Tests passed but Plane close failed — will retry close next cycle[/yellow]")
                    self._processed_task_ids.discard(task_id)
                    _save_processed_ids(self._processed_task_ids)
                    fail_queue_task(task_id, task_title, "Tests passed but Plane status update failed")
                    return
                set_pipeline_status("git_push", task_id, task_title, "git_agent", "Committing meaningful repo files")
                git_ok = self._run_git_commit(task_id, task_title)
                if git_ok:
                    mark_pipeline_step_complete("git_push")
                    set_pipeline_status("done", task_id, task_title, "", f"Task completed — Plane closed + Git synced ({duration}s)")
                else:
                    set_pipeline_status(
                        "git_push", task_id, task_title, "git_agent",
                        "Git gate failed — uncommitted files remain; sweep retries each poll",
                    )
                    add_comment(
                        target_pid, task_id,
                        "🤖 Git Agent: Task closed on Plane but commit/push failed. "
                        "Watcher will retry git sweep on next poll.",
                        self.workspace_slug,
                    )
                complete_queue_task(task_id, task_title, duration)
                from memory_manager import clear_build_progress, clear_test_progress
                clear_build_progress()
                clear_test_progress()
                set_agent_working(False)
                set_pipeline_status(
                    "idle", "", "", "",
                    f"Monitoring — '{task_title}' completed; waiting for next Plane task",
                )
            else:
                reason = output[:200] or "Tests failed after auto-retry attempts"
                set_pipeline_status(
                    "failed", task_id, task_title, "tester",
                    f"All {max_attempts} inner × {self._max_outer_cycles()} outer attempts exhausted",
                )
                fail_queue_task(task_id, task_title, reason, max_attempts, max_attempts)
                self._processed_task_ids.discard(task_id)
                update_task_status(target_pid, task_id, STATE_TODO, self.workspace_slug)
                add_comment(
                    target_pid, task_id,
                    f"🤖 Sprint Watcher (Task 37): All auto-retry cycles exhausted ({duration}s).\n"
                    f"Task in To Do — watcher will auto-pick up again on next poll.\n\n"
                    f"Test output:\n{output[:400]}",
                    self.workspace_slug,
                )
                console.print(f"[red]❌ All auto-retry cycles exhausted — will re-pick on next watcher poll: {task_title}[/red]")
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not finalize task status: {e}[/yellow]")

        log_task_result(task_id, task_title, "SprintWatcherAgent", "completed" if success else "failed", output, duration)
        update_agent_status("sprint_watcher", "idle", "Sprint Watcher Agent Active (Monitoring)")

        if action != "complete":
            self._processed_task_ids.discard(task_id)
            _save_processed_ids(self._processed_task_ids)

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
        console.print(Panel(
            f"[bold]New Task Picked Up![/bold]\n"
            f"Title:    {task_title}\n"
            f"ID:       {task_id}\n"
            f"Priority: {priority.upper()}\n"
            f"Project:  {task.get('project_name', task.get('project_id', ''))}",
            border_style="cyan"
        ))
        return self._execute_full_pipeline_until_pass(task, claim_on_plane=True)

    def _handle_in_progress_retry(self, task: dict) -> bool:
        """
        Retry a task already in 'started' state that was never fully processed
        (e.g. builder crashed, or agent moved to In Progress but pipeline failed).
        Skips the Plane status update step since task is already In Progress.
        """
        task_id = task["id"]
        task_title = task.get("name", "Unknown Task")
        priority = task.get("priority", "medium")
        desc = task.get("description", "") or ""
        project_id = self._resolve_project_id(task)
        if not project_id:
            return False

        console.print(Panel(
            f"[bold yellow]Retrying In-Progress Task[/bold yellow]\n"
            f"Title:    {task_title}\n"
            f"ID:       {task_id}\n"
            f"Reason:   Auto-resume — Task 37 full pipeline until tests pass",
            border_style="yellow"
        ))
        self._processed_task_ids.discard(task_id)
        _save_processed_ids(self._processed_task_ids)
        return self._execute_full_pipeline_until_pass(task, claim_on_plane=False)

    def _verify_close_in_progress_task(self, task: dict) -> bool:
        """
        Task 34 + Task 37: Re-run tests and close ONLY if Build gate already passed.
        If Build never completed, run full pipeline (Build → Test) instead.
        """
        task_id = task["id"]
        task_title = task.get("name", "Unknown Task")
        project_id = self._resolve_project_id(task)
        if not project_id:
            return False

        from memory_manager import get_pipeline_status
        pipeline = get_pipeline_status()
        completed = set(pipeline.get("completed_steps") or [])
        build_gate_passed = (
            pipeline.get("task_id") == task_id and "building" in completed
        )

        if not build_gate_passed:
            console.print(
                f"[yellow]⛔ Verify-close skipped for '{task_title}' — "
                f"Build gate not passed. Running full Build → Test pipeline.[/yellow]"
            )
            self._processed_task_ids.discard(task_id)
            _save_processed_ids(self._processed_task_ids)
            return self._handle_in_progress_retry(task)

        now = time.time()
        last = self._verify_close_attempts.get(task_id, 0)
        if now - last < self.verify_close_cooldown:
            return False

        self._verify_close_attempts[task_id] = now
        console.print(Panel(
            f"[bold cyan]Verify-Close (Build already passed)[/bold cyan]\n"
            f"Title: {task_title}\n"
            f"Rule: Re-run tests only — if PASS → mark Completed on Plane",
            border_style="cyan"
        ))

        start_time = time.time()
        test_success = False
        test_output = ""
        set_pipeline_status("testing", task_id, task_title, "tester", "Verify-close: starting quality gate")
        set_agent_working(False)
        try:
            test_success, test_output = self._run_tests(
                task_id,
                task_title,
                task.get("description", "") or "",
                task.get("project_name", ""),
                mode="fast",
            )
        finally:
            from memory_manager import clear_test_progress
            clear_test_progress()

        duration = round(time.time() - start_time, 2)
        if test_success:
            self._finalize_task(project_id, task_id, task_title, True, test_output, duration, builder_ran=False)
            self._processed_task_ids.add(task_id)
            _save_processed_ids(self._processed_task_ids)
            return True

        console.print(f"[dim]Verify-close: tests not passing yet for '{task_title}' — stays In Progress[/dim]")
        cooldown_min = max(1, int(self.verify_close_cooldown / 60))
        set_pipeline_status(
            "idle",
            task_id,
            task_title,
            "sprint_watcher",
            f"Verify-close failed — re-test in ~{cooldown_min} min (unit/browser gate)",
        )
        return False


    def watch(self, max_cycles: Optional[int] = None):
        if not self._init_project():
            return

        from memory_manager import get_previous_day_context
        recall = get_previous_day_context()
        console.print(f"[dim]📅 Task 40 memory recall: {recall.get('summary', '')}[/dim]")

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

            self._reconcile_processed_ids(tasks, _get_group)
            sync_pending_tasks(actionable)

            for task in actionable:
                grp = _get_group(task)
                console.print(f"[cyan]→ Picking up [{grp.upper()}] task: {task.get('name')} (priority: {task.get('priority', 'medium')})[/cyan]")
                self._handle_new_task(task)
                time.sleep(1.0)

            failed_ids = {
                t.get("id") for t in get_task_queue().get("failed", []) if t.get("id")
            }
            in_progress_tasks = [
                t for t in tasks
                if _get_group(t) in IN_PROGRESS_GROUPS
            ]
            # Task 37: auto-resume tasks that failed but are still In Progress on Plane
            for task in in_progress_tasks:
                if task.get("id") in failed_ids:
                    console.print(f"[cyan]→ Auto-resuming failed In-Progress task: {task.get('name')}[/cyan]")
                    self._processed_task_ids.discard(task.get("id"))
                    _save_processed_ids(self._processed_task_ids)
                    self._handle_in_progress_retry(task)
                    time.sleep(1.0)

            stale_unprocessed = [
                t for t in in_progress_tasks
                if t.get("id") not in self._processed_task_ids
                and t.get("id") not in failed_ids
            ]
            stuck_processed = [
                t for t in in_progress_tasks
                if t.get("id") in self._processed_task_ids
                and t.get("id") not in failed_ids
            ]

            for task in stale_unprocessed:
                console.print(f"[yellow]→ Retrying stale In-Progress task: {task.get('name')}[/yellow]")
                self._handle_in_progress_retry(task)
                time.sleep(1.0)

            for task in stuck_processed:
                if _get_group(task) in {"completed", "done"}:
                    continue
                self._verify_close_in_progress_task(task)
                time.sleep(1.0)

            if not actionable and not in_progress_tasks:
                set_pipeline_status("idle", "", "", "", f"Monitoring — {len(tasks)} tasks on board, queue ready")
                self._sweep_pending_git()

            poll_sleep = (
                min(self.poll_interval, self._active_poll_interval)
                if (actionable or in_progress_tasks)
                else self.poll_interval
            )

            if max_cycles and cycle >= max_cycles:
                break

            time.sleep(poll_sleep)


if __name__ == "__main__":
    watcher = SprintWatcherAgent(poll_interval_seconds=15)
    watcher.watch(max_cycles=1)
