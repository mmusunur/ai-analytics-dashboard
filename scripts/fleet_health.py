"""
Fleet Health — detect stopped agents and restart background daemons.
Used by orchestrator_agent (supervisor loop) and agent_watchdog.
"""

import os
import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent

# Long-running daemons the fleet must keep alive (Task 8.3).
def _default_sprint_interval() -> list[str]:
    try:
        sys.path.insert(0, str(ROOT_DIR / "agents"))
        from agent_config_loader import get_fleet_config
        return ["--interval", str(get_fleet_config()["sprint_watcher_interval_seconds"])]
    except Exception:
        return ["--interval", "60"]


FLEET_DAEMONS = [
    {
        "name": "sprint_watcher",
        "match": ("sprint_watcher_agent", "run_sprint_watcher"),
        "script": "scripts/run_sprint_watcher.py",
        "args_fn": _default_sprint_interval,
    },
    {
        "name": "memory",
        "match": ("memory_manager",),
        "script": "agents/memory_manager.py",
        "args": ["--daemon"],
    },
    {
        "name": "git_agent",
        "match": ("git_agent", "agents.git_agent"),
        "script": "agents/git_agent.py",
        "args": ["--standby"],
    },
]

ORCHESTRATOR_MATCH = ("orchestrator_agent",)
ORCHESTRATOR_SCRIPT = "agents/orchestrator_agent.py"
ORCHESTRATOR_ARGS = ["--supervise"]


def _process_running(keywords: tuple[str, ...]) -> bool:
    try:
        import psutil
        for proc in psutil.process_iter(["pid", "cmdline"]):
            try:
                cmd = " ".join(proc.info.get("cmdline") or []).lower()
                if "python" not in cmd:
                    continue
                if any(k.lower() in cmd for k in keywords):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception:
        pass
    return False


def start_agent(script_rel: str, extra_args: list | None = None) -> None:
    flags = subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    cmd = [sys.executable, str(ROOT_DIR / script_rel), *(extra_args or [])]
    subprocess.Popen(
        cmd,
        cwd=str(ROOT_DIR),
        creationflags=flags,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
    )


def ensure_fleet_running(include_orchestrator: bool = False) -> list[str]:
    """Restart any stopped fleet daemon. Returns names that were restarted."""
    restarted: list[str] = []

    for spec in FLEET_DAEMONS:
        if not _process_running(spec["match"]):
            print(f"[fleet] {spec['name']} not running — restarting...")
            args = spec["args_fn"]() if callable(spec.get("args_fn")) else spec.get("args", [])
            start_agent(spec["script"], args)
            restarted.append(spec["name"])

    if include_orchestrator and not _process_running(ORCHESTRATOR_MATCH):
        print("[fleet] orchestrator not running — restarting...")
        start_agent(ORCHESTRATOR_SCRIPT, ORCHESTRATOR_ARGS)
        restarted.append("orchestrator")

    return restarted


def fleet_snapshot() -> dict[str, bool]:
    """Return {agent_name: process_running} for UI / orchestrator status."""
    snap = {spec["name"]: _process_running(spec["match"]) for spec in FLEET_DAEMONS}
    snap["orchestrator"] = _process_running(ORCHESTRATOR_MATCH)
    return snap
