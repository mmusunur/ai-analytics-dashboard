"""Restart backend, frontend, and agent fleet."""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from server_health import ensure_servers_running, servers_healthy
from fleet_health import ensure_fleet_running


def main() -> int:
    print("Starting backend + frontend...")
    ensure_servers_running(wait_seconds=30)
    status = servers_healthy()
    print(f"Servers: backend={status['backend']} frontend={status['frontend']} healthy={status['healthy']}")
    restarted = ensure_fleet_running(include_orchestrator=True)
    print(f"Fleet restarted: {restarted or 'none needed'}")
    time.sleep(2)
    status = servers_healthy()
    return 0 if status["healthy"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
