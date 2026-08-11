"""
Agent & Server Health Watchdog Supervisor.
Monitors FastAPI (:8000), Vite (:5173), and key background agents.
Auto-restarts any crashed server or agent process without user intervention.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "scripts"))

from server_health import ensure_servers_running, is_port_open, servers_healthy


def _process_running(keyword: str) -> bool:
    try:
        import psutil
        key = keyword.lower()
        for proc in psutil.process_iter(["pid", "cmdline"]):
            try:
                cmd = " ".join(proc.info.get("cmdline") or []).lower()
                if key in cmd and "python" in cmd:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception:
        pass
    return False


def _start_agent(script_rel: str, extra_args: list | None = None) -> None:
    flags = subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    cmd = [sys.executable, str(ROOT_DIR / script_rel), *(extra_args or [])]
    subprocess.Popen(
        cmd,
        cwd=str(ROOT_DIR),
        creationflags=flags,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
    )


def watchdog_health_loop(poll_interval: int = 15) -> None:
    print("Starting Agent & Server Watchdog Supervisor...")
    print("Monitoring: backend :8000, frontend :5173, sprint watcher")

    while True:
        status = servers_healthy()
        if not status["backend"] or not status["frontend"]:
            print(f"[watchdog] Server check: backend={status['backend']} frontend={status['frontend']} — restarting...")
            ensure_servers_running(wait_seconds=20)

        if not _process_running("run_sprint_watcher") and not _process_running("sprint_watcher_agent"):
            print("[watchdog] Sprint watcher not running — restarting...")
            _start_agent("scripts/run_sprint_watcher.py", ["--interval", "60"])

        time.sleep(poll_interval)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    watchdog_health_loop(poll_interval=15)
