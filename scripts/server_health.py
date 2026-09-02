"""
Server Health Helpers — Check and start backend (:8000) and frontend (:5173).
Used by agent_watchdog, tester_agent, and sprint_watcher before browser tests.
"""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent


def is_port_open(port: int, host: str = "127.0.0.1", timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def servers_healthy() -> dict:
    backend = is_port_open(8000)
    frontend = is_port_open(5173)
    return {
        "backend": backend,
        "frontend": frontend,
        "healthy": backend and frontend,
    }


def start_backend() -> None:
    flags = subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        cwd=str(ROOT_DIR / "backend"),
        creationflags=flags,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )


def start_frontend() -> None:
    flags = subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    cmd = ["cmd.exe", "/c", "npm", "run", "dev", "--", "--host", "0.0.0.0"] if sys.platform == "win32" else "npm run dev -- --host 0.0.0.0"
    subprocess.Popen(
        cmd,
        cwd=str(ROOT_DIR / "frontend"),
        shell=(sys.platform != "win32"),
        creationflags=flags,
    )


def ensure_servers_running(wait_seconds: int = 12) -> bool:
    """Start missing servers and wait until both ports respond."""
    status = servers_healthy()
    if not status["backend"]:
        print("[server_health] Backend :8000 down — starting FastAPI...")
        start_backend()
    if not status["frontend"]:
        print("[server_health] Frontend :5173 down — starting Vite...")
        start_frontend()

    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        status = servers_healthy()
        if status["healthy"]:
            return True
        time.sleep(1.5)

    return servers_healthy()["healthy"]
