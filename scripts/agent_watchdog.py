"""
Agent & Server Health Watchdog Supervisor.
Monitors FastAPI (:8000), Vite (:5173), and key background agents.
Auto-restarts any crashed server or agent process without user intervention.
"""

import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "scripts"))

from server_health import ensure_servers_running, servers_healthy
from fleet_health import ensure_fleet_running


def watchdog_health_loop(poll_interval: int | None = None) -> None:
    from agent_config_loader import get_fleet_config
    fleet = get_fleet_config()
    interval = poll_interval or fleet["watchdog_poll_interval_seconds"]
    print("Starting Agent & Server Watchdog Supervisor...")
    print("Monitoring: backend :8000, frontend :5173, orchestrator, sprint watcher, memory, git")

    while True:
        status = servers_healthy()
        if not status["backend"] or not status["frontend"]:
            print(f"[watchdog] Server check: backend={status['backend']} frontend={status['frontend']} — restarting...")
            ensure_servers_running(wait_seconds=20)

        restarted = ensure_fleet_running(include_orchestrator=True)
        if restarted:
            print(f"[watchdog] Fleet restarted: {', '.join(restarted)}")

        time.sleep(interval)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, str(ROOT_DIR / "agents"))
    from agent_config_loader import get_fleet_config
    watchdog_health_loop(poll_interval=get_fleet_config()["watchdog_poll_interval_seconds"])
