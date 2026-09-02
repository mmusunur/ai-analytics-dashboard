"""
Run Sprint Watcher — Standalone entry point for the Sprint Watcher Agent.

Usage:
    python scripts/run_sprint_watcher.py               # poll every 2 minutes forever
    python scripts/run_sprint_watcher.py --interval 60 # poll every 60 seconds
    python scripts/run_sprint_watcher.py --cycles 5    # run exactly 5 poll cycles (for testing)
"""

import sys
import io
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "agents"))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")

from sprint_watcher_agent import SprintWatcherAgent
from rich.console import Console

console = Console()

import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Sprint Watcher — monitors Plane and drives autonomous task execution"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        metavar="SECONDS",
        help="How often to poll Plane for new tasks (default: 30s; uses 15s when tasks active)",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=0,
        metavar="N",
        help="Stop after N poll cycles. 0 = run indefinitely (default: 0)",
    )
    args = parser.parse_args()

    watcher = SprintWatcherAgent(poll_interval_seconds=args.interval)
    watcher.watch(max_cycles=args.cycles)


if __name__ == "__main__":
    main()
