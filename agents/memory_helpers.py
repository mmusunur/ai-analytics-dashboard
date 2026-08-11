"""
Memory Helpers — Logging and historical task cleanup utilities for Memory Manager.
Keeps agents/memory_manager.py lightweight (< 250 lines).
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from rich.console import Console

console = Console(legacy_windows=False)


def cleanup_old_memory(conversations_dir: Path, task_history_dir: Path, retention_days: int = 30):
    """Clean up memory files older than retention_days."""
    cutoff = datetime.now() - timedelta(days=retention_days)
    for folder in [conversations_dir, task_history_dir]:
        if not folder.exists():
            continue
        for filepath in folder.glob("*.jsonl"):
            try:
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                if mtime < cutoff:
                    filepath.unlink()
                    console.print(f"[dim]Deleted old memory: {filepath.name}[/dim]")
            except Exception:
                pass


def load_conversation(conversations_dir: Path, agent_name: str, max_messages: int = 50) -> list:
    """Load conversation history for an agent."""
    file_path = conversations_dir / f"{agent_name}_conversation.jsonl"
    if not file_path.exists():
        return []

    messages = []
    try:
        with file_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        messages.append(json.loads(line.strip()))
                    except Exception:
                        pass
        return messages[-max_messages:]
    except Exception:
        return []
