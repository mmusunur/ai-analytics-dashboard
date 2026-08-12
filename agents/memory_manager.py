import sys
import json
import time
import psutil
from datetime import datetime
from pathlib import Path
from rich.console import Console
try:
    from memory_helpers import cleanup_old_memory, load_conversation
except ImportError:
    from agents.memory_helpers import cleanup_old_memory, load_conversation

console = Console(force_terminal=True)

ROOT_DIR = Path(__file__).parent.parent
MEMORY_DIR = ROOT_DIR / "memory"
STATE_FILE = MEMORY_DIR / "agent_state.json"
_PID_CACHE = {"at": 0.0, "pids": {}}
_PID_CACHE_TTL = 2.5
CONVERSATIONS_DIR = MEMORY_DIR / "conversations"
TASK_HISTORY_DIR = MEMORY_DIR / "task_history"


def _ensure_dirs():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
    TASK_HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def load_state() -> dict:
    _ensure_dirs()
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "plane_project_id": None,
        "agents": {
            "orchestrator": {"status": "idle", "current_task": "Idle", "last_updated": None},
            "builder": {"status": "idle", "current_task": "Idle", "last_updated": None},
            "tester": {"status": "idle", "current_task": "Idle", "last_updated": None},
            "sprint_watcher": {"status": "idle", "current_task": "Idle", "last_updated": None},
            "git_agent": {"status": "idle", "current_task": "Idle", "last_updated": None},
            "memory": {"status": "idle", "current_task": "Idle", "last_updated": None},
        },
        "active_sprint_id": None,
        "last_conversation_update": None
    }


def save_state(state: dict):
    _ensure_dirs()
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception as e:
        console.print(f"[yellow]⚠️ Failed to save agent state: {e}[/yellow]")


def update_agent_status(agent_name: str, status: str, current_task: str = "Idle"):
    state = load_state()
    if agent_name in state.get("agents", {}):
        state["agents"][agent_name] = {
            "status": status,
            "current_task": current_task,
            "last_updated": datetime.now().isoformat()
        }
        save_state(state)


def set_agent_working(is_working: bool, task_title: str = ""):
    """
    Broadcast a global 'agent_working' flag to the frontend.
    When True: pause aggressive polling during Build (file changes / hot reload).
    Do NOT set True during Test — browser tests run 5–15 min; UI must stay live.
    Always call set_agent_working(False) in a finally block.
    """
    state = load_state()
    state["agent_working"] = is_working
    state["agent_working_task"] = task_title if is_working else ""
    state["agent_working_since"] = datetime.now().isoformat() if is_working else None
    save_state(state)


def set_pipeline_status(
    phase: str,
    task_id: str = "",
    task_title: str = "",
    active_agent: str = "",
    message: str = "",
) -> None:
    """Track sprint pipeline phase for UI telemetry (pickup → build → test → close → git)."""
    state = load_state()
    prev = state.get("pipeline") or {}
    state["pipeline"] = {
        "phase": phase,
        "task_id": task_id,
        "task_title": task_title,
        "active_agent": active_agent,
        "message": message,
        "progress_pct": PHASE_PROGRESS.get(phase, 0),
        "updated_at": datetime.now().isoformat(),
        "completed_steps": prev.get("completed_steps", []),
    }
    if phase == "testing" and prev.get("test_started_at"):
        state["pipeline"]["test_started_at"] = prev["test_started_at"]
        state["pipeline"]["test_subphase"] = prev.get("test_subphase", "starting")
    elif phase != "testing":
        state["pipeline"].pop("test_started_at", None)
        state["pipeline"].pop("test_subphase", None)
    save_state(state)
    if task_id and phase not in ("idle",):
        update_queue_progress(task_id, phase, active_agent, message)


def mark_pipeline_step_complete(step: str) -> None:
    """Record a gated pipeline step as successfully completed (Task 37 step gates)."""
    state = load_state()
    pipeline = state.get("pipeline") or {}
    steps = list(pipeline.get("completed_steps") or [])
    if step not in steps:
        steps.append(step)
    pipeline["completed_steps"] = steps
    state["pipeline"] = pipeline
    save_state(state)


def reset_pipeline_steps(task_id: str = "", task_title: str = "") -> None:
    """Clear completed step markers when a new pickup cycle starts."""
    state = load_state()
    pipeline = state.get("pipeline") or {}
    pipeline["completed_steps"] = []
    if task_id:
        pipeline["task_id"] = task_id
    if task_title:
        pipeline["task_title"] = task_title
    state["pipeline"] = pipeline
    save_state(state)


def rewind_pipeline_to_step(keep_through: str = "pickup") -> None:
    """Remove completed steps after a gate failure (e.g. test fail → rewind to pickup only)."""
    order = ["pickup", "building", "testing", "closing", "git_push", "done"]
    if keep_through not in order:
        return
    keep_idx = order.index(keep_through)
    state = load_state()
    pipeline = state.get("pipeline") or {}
    steps = pipeline.get("completed_steps") or []
    pipeline["completed_steps"] = [s for s in steps if s in order[: keep_idx + 1]]
    state["pipeline"] = pipeline
    save_state(state)


def get_pipeline_status() -> dict:
    state = load_state()
    return state.get("pipeline") or {
        "phase": "idle",
        "task_id": "",
        "task_title": "",
        "active_agent": "",
        "message": "No active sprint task",
        "updated_at": None,
    }


PHASE_PROGRESS = {
    "idle": 0,
    "pickup": 15,
    "building": 40,
    "retry": 50,
    "testing": 65,
    "closing": 85,
    "git_push": 95,
    "done": 100,
    "failed": 0,
}

TEST_SUBPHASE_PROGRESS = {
    "starting": 65,
    "sprint_cases": 67,
    "unit": 70,
    "browser": 78,
    "excel": 83,
    "done": 84,
}


def update_test_progress(
    subphase: str,
    message: str,
    task_id: str = "",
    task_title: str = "",
) -> None:
    """Heartbeat during long Test runs — UI shows sub-phase + elapsed time."""
    state = load_state()
    pipeline = dict(state.get("pipeline") or {})
    if not pipeline.get("test_started_at"):
        pipeline["test_started_at"] = datetime.now().isoformat()
    pipeline["phase"] = "testing"
    pipeline["test_subphase"] = subphase
    pipeline["active_agent"] = "tester"
    pipeline["message"] = message
    pipeline["progress_pct"] = TEST_SUBPHASE_PROGRESS.get(subphase, PHASE_PROGRESS["testing"])
    pipeline["updated_at"] = datetime.now().isoformat()
    if task_id:
        pipeline["task_id"] = task_id
    if task_title:
        pipeline["task_title"] = task_title
    state["pipeline"] = pipeline
    save_state(state)
    tid = pipeline.get("task_id") or task_id
    if tid:
        update_queue_progress(tid, "testing", "tester", message)


def clear_test_progress() -> None:
    """Clear test heartbeat fields when Test gate finishes."""
    state = load_state()
    pipeline = dict(state.get("pipeline") or {})
    pipeline.pop("test_subphase", None)
    pipeline.pop("test_started_at", None)
    state["pipeline"] = pipeline
    save_state(state)


def _empty_task_queue() -> dict:
    return {
        "pending": [],
        "active": None,
        "completed": [],
        "failed": [],
        "updated_at": None,
    }


def get_task_queue() -> dict:
    state = load_state()
    return state.get("task_queue") or _empty_task_queue()


def _save_task_queue(queue: dict) -> None:
    state = load_state()
    queue["updated_at"] = datetime.now().isoformat()
    state["task_queue"] = queue
    save_state(state)


def sync_pending_tasks(actionable_tasks: list) -> None:
    """Merge Plane pickupable tasks into the pending queue (deduped, priority-sorted)."""
    queue = get_task_queue()
    active_id = (queue.get("active") or {}).get("id")
    done_ids = {t.get("id") for t in queue.get("completed", []) if t.get("id")}
    failed_ids = {t.get("id") for t in queue.get("failed", []) if t.get("id")}
    pending_ids = {t.get("id") for t in queue.get("pending", []) if t.get("id")}

    priority_weights = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
    new_pending = []
    for task in actionable_tasks:
        tid = task.get("id")
        if not tid or tid == active_id or tid in done_ids:
            continue
        if tid in pending_ids:
            existing = next((p for p in queue["pending"] if p.get("id") == tid), None)
            if existing:
                new_pending.append(existing)
            continue
        new_pending.append({
            "id": tid,
            "title": task.get("name", "Untitled"),
            "priority": (task.get("priority") or "medium").lower(),
            "project_name": task.get("project_name", ""),
            "queued_at": datetime.now().isoformat(),
        })

    new_pending.sort(
        key=lambda t: priority_weights.get(t.get("priority", "medium"), 2),
        reverse=True,
    )
    queue["pending"] = new_pending
    _save_task_queue(queue)


def set_queue_active(task_id: str, task_title: str, project_name: str = "", priority: str = "medium") -> None:
    queue = get_task_queue()
    queue["pending"] = [t for t in queue.get("pending", []) if t.get("id") != task_id]
    queue["active"] = {
        "id": task_id,
        "title": task_title,
        "project_name": project_name,
        "priority": priority,
        "phase": "pickup",
        "progress_pct": PHASE_PROGRESS["pickup"],
        "active_agent": "sprint_watcher",
        "message": "Task picked up from Plane",
        "started_at": datetime.now().isoformat(),
    }
    _save_task_queue(queue)


def update_queue_progress(
    task_id: str,
    phase: str,
    active_agent: str = "",
    message: str = "",
) -> None:
    queue = get_task_queue()
    active = queue.get("active") or {}
    if active.get("id") != task_id:
        return
    active["phase"] = phase
    active["progress_pct"] = PHASE_PROGRESS.get(phase, active.get("progress_pct", 0))
    active["active_agent"] = active_agent
    active["message"] = message
    active["updated_at"] = datetime.now().isoformat()
    queue["active"] = active
    _save_task_queue(queue)


def complete_queue_task(task_id: str, task_title: str, duration_seconds: float = 0) -> None:
    queue = get_task_queue()
    entry = {
        "id": task_id,
        "title": task_title,
        "completed_at": datetime.now().isoformat(),
        "duration_seconds": duration_seconds,
        "progress_pct": 100,
    }
    queue["completed"] = ([entry] + [t for t in queue.get("completed", []) if t.get("id") != task_id])[:30]
    queue["pending"] = [t for t in queue.get("pending", []) if t.get("id") != task_id]
    if (queue.get("active") or {}).get("id") == task_id:
        queue["active"] = None
    queue["failed"] = [t for t in queue.get("failed", []) if t.get("id") != task_id]
    _save_task_queue(queue)


def fail_queue_task(task_id: str, task_title: str, reason: str = "", attempts: int = 0, max_attempts: int = 0) -> None:
    queue = get_task_queue()
    entry = {
        "id": task_id,
        "title": task_title,
        "failed_at": datetime.now().isoformat(),
        "reason": reason[:300],
        "progress_pct": 0,
        "phase": "failed",
        "attempts": attempts,
        "max_attempts": max_attempts,
    }
    queue["failed"] = ([entry] + [t for t in queue.get("failed", []) if t.get("id") != task_id])[:20]
    queue["pending"] = [t for t in queue.get("pending", []) if t.get("id") != task_id]
    if (queue.get("active") or {}).get("id") == task_id:
        queue["active"] = None
    _save_task_queue(queue)


def get_queue_status_for_task(task_id: str):
    queue = get_task_queue()
    if (queue.get("active") or {}).get("id") == task_id:
        return {**queue["active"], "queue_status": "active"}
    for t in queue.get("pending", []):
        if t.get("id") == task_id:
            return {**t, "queue_status": "pending", "progress_pct": 0, "phase": "queued"}
    for t in queue.get("completed", []):
        if t.get("id") == task_id:
            return {**t, "queue_status": "completed", "phase": "done", "progress_pct": 100}
    for t in queue.get("failed", []):
        if t.get("id") == task_id:
            return {**t, "queue_status": "failed", "phase": "failed"}
    return None


def is_agent_working() -> bool:
    """Returns True if a builder/tester agent is currently running code changes."""
    state = load_state()
    if not state.get("agent_working", False):
        return False
    # Safety valve: if agent_working has been True for > 30 minutes, auto-clear it
    # (guards against crashes that leave the flag stuck True forever)
    since_str = state.get("agent_working_since") or ""
    if since_str:
        try:
            since = datetime.fromisoformat(since_str)
            if (datetime.now() - since).total_seconds() > 1800:  # 30 min
                console.print("[yellow]⚠️ agent_working flag stuck for >30min — auto-clearing.[/yellow]")
                set_agent_working(False)
                return False
        except Exception:
            pass
    return True


def _scan_agent_pids() -> dict:
    """Scan running agent processes (cached briefly — psutil is slow on Windows)."""
    now = time.time()
    if now - _PID_CACHE["at"] < _PID_CACHE_TTL:
        return _PID_CACHE["pids"]

    agent_pids = {}
    try:
        for proc in psutil.process_iter(["pid", "cmdline"]):
            try:
                cmd = " ".join(proc.info.get("cmdline") or []).lower()
                if "sprint_watcher_agent" in cmd:
                    agent_pids["sprint_watcher"] = proc.info["pid"]
                elif "builder_agent" in cmd:
                    agent_pids["builder"] = proc.info["pid"]
                elif "tester_agent" in cmd:
                    agent_pids["tester"] = proc.info["pid"]
                elif "git_agent" in cmd or "agents.git_agent" in cmd:
                    agent_pids["git_agent"] = proc.info["pid"]
                elif "memory_manager" in cmd:
                    agent_pids["memory"] = proc.info["pid"]
                elif "orchestrator_agent" in cmd:
                    agent_pids["orchestrator"] = proc.info["pid"]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception:
        pass

    _PID_CACHE["at"] = now
    _PID_CACHE["pids"] = agent_pids
    return agent_pids


def _fleet_is_online(agent_pids: dict) -> bool:
    """True when sprint watcher or orchestrator process is alive (fleet supervisor up)."""
    return bool(agent_pids.get("sprint_watcher") or agent_pids.get("orchestrator"))


def get_dynamic_agent_statuses() -> dict:
    state = load_state()
    agent_pids = _scan_agent_pids()
    agents_meta = state.get("agents", {})
    fleet_online = _fleet_is_online(agent_pids)
    listening_agents = {"orchestrator", "builder", "tester", "git_agent", "memory"}
    statuses = {}
    for name in ["sprint_watcher", "orchestrator", "builder", "tester", "git_agent", "memory"]:
        meta = agents_meta.get(name, {})
        pid = agent_pids.get(name)
        is_active = pid is not None
        if is_active:
            status = "running"
        elif fleet_online and name in listening_agents:
            # Idle-but-listening agents count as online when the fleet supervisor is up
            status = "running"
        else:
            status = meta.get("status", "idle")
            if status == "running":
                status = "idle"
        statuses[name] = {
            "name": name.replace("_", " ").title(),
            "status": status,
            "current_task": meta.get("current_task", "Monitoring"),
            "last_updated": meta.get("last_updated"),
            "pid": pid
        }
    return statuses


def log_task_result(task_id: str, task_title: str, agent_name: str, status: str, output: str = "", duration_seconds: float = 0.0):
    _ensure_dirs()
    today = datetime.now().strftime("%Y-%m-%d")
    history_file = TASK_HISTORY_DIR / f"{today}_task_history.jsonl"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "task_id": task_id,
        "task_title": task_title,
        "agent": agent_name,
        "status": status,
        "duration_seconds": duration_seconds,
        "output_summary": output[:500] if output else ""
    }
    try:
        with history_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        console.print(f"[yellow]⚠️ Failed to log task result: {e}[/yellow]")


def update_conversation_memory(agent_name: str = "assistant", user_query: str = "", response_summary: str = ""):
    _ensure_dirs()
    now = datetime.now()
    conv_file = CONVERSATIONS_DIR / f"{agent_name}_conversation.jsonl"
    entry = {
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "user_query": user_query[:500],
        "response_summary": response_summary[:1000]
    }
    try:
        with conv_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

    state = load_state()
    state["last_conversation_update"] = now.isoformat()
    save_state(state)


if __name__ == "__main__":
    import argparse
    import time as _time

    parser = argparse.ArgumentParser(description="Memory Manager")
    parser.add_argument("--daemon", action="store_true", help="Run continuous state persistence loop")
    args = parser.parse_args()

    if args.daemon:
        console.print("[green]Memory Agent daemon started[/green]")
        while True:
            update_agent_status("memory", "running", "State persistence active")
            _time.sleep(30)
    else:
        console.print(f"Memory Manager status: {load_state()}")
        cleanup_old_memory(CONVERSATIONS_DIR, TASK_HISTORY_DIR)
