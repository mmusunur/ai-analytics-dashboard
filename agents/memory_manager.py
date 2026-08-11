import sys
import json
import psutil
from datetime import datetime
from pathlib import Path
from rich.console import Console
from agents.memory_helpers import cleanup_old_memory, load_conversation

console = Console(force_terminal=True)

ROOT_DIR = Path(__file__).parent.parent
MEMORY_DIR = ROOT_DIR / "memory"
STATE_FILE = MEMORY_DIR / "agent_state.json"
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
    When True: the frontend pauses all API polling to prevent UI disruption
    while the builder agent is actively modifying files / running tests.
    Always call set_agent_working(False) in a finally block.
    """
    state = load_state()
    state["agent_working"] = is_working
    state["agent_working_task"] = task_title if is_working else ""
    state["agent_working_since"] = datetime.now().isoformat() if is_working else None
    save_state(state)


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


def get_dynamic_agent_statuses() -> dict:
    state = load_state()
    agent_pids = {}
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmd = " ".join(proc.info.get("cmdline") or []).lower()
            if "sprint_watcher" in cmd:
                agent_pids["sprint_watcher"] = proc.info["pid"]
            elif "builder_agent" in cmd:
                agent_pids["builder"] = proc.info["pid"]
            elif "tester_agent" in cmd:
                agent_pids["tester"] = proc.info["pid"]
            elif "git_agent" in cmd:
                agent_pids["git_agent"] = proc.info["pid"]
            elif "memory_manager" in cmd:
                agent_pids["memory"] = proc.info["pid"]
            elif "orchestrator" in cmd:
                agent_pids["orchestrator"] = proc.info["pid"]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    statuses = {}
    agents_meta = state.get("agents", {})
    for name in ["sprint_watcher", "orchestrator", "builder", "tester", "git_agent", "memory"]:
        meta = agents_meta.get(name, {})
        is_active = (name in agent_pids) or meta.get("status") in ("running", "active")
        statuses[name] = {
            "name": name.replace("_", " ").title(),
            "status": "running",
            "current_task": meta.get("current_task", "Monitoring"),
            "pid": agent_pids.get(name)
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
    console.print(f"Memory Manager status: {load_state()}")
    cleanup_old_memory(CONVERSATIONS_DIR, TASK_HISTORY_DIR)
