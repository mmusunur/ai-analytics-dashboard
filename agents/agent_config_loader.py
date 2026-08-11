"""
Agent Config Loader — reads config/agent_config.json with per-agent .env overrides.
"""

import json
import os
from pathlib import Path
from functools import lru_cache

ROOT_DIR = Path(__file__).parent.parent
CONFIG_FILE = ROOT_DIR / "config" / "agent_config.json"

_ENV_MODEL_KEYS = {
    "orchestrator": "ORCHESTRATOR_MODEL",
    "builder": "BUILDER_MODEL",
    "tester": "TESTER_MODEL",
    "sprint_watcher": "SPRINT_WATCHER_MODEL",
    "plane_agent": "PLANE_AGENT_MODEL",
    "git_agent": "GIT_AGENT_MODEL",
}


@lru_cache(maxsize=1)
def load_agent_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_agent_section(agent_name: str) -> dict:
    return load_agent_config().get(agent_name, {})


def get_agent_model(agent_name: str, default: str = "claude-opus-4-5") -> str:
    env_key = _ENV_MODEL_KEYS.get(agent_name)
    if env_key:
        val = os.getenv(env_key, "").strip()
        if val:
            return val
    return get_agent_section(agent_name).get("model") or os.getenv("AGENT_MODEL", default)


def get_agent_max_tokens(agent_name: str, default: int = 4096) -> int:
    section = get_agent_section(agent_name)
    try:
        return int(section.get("max_tokens") or os.getenv("AGENT_MAX_TOKENS", default))
    except (TypeError, ValueError):
        return default


def get_fleet_config() -> dict:
    cfg = load_agent_config().get("fleet_supervisor", {})
    return {
        "enabled": str(os.getenv("FLEET_AUTO_RESTART", cfg.get("enabled", True))).lower() not in ("0", "false", "no"),
        "orchestrator_poll_interval_seconds": int(os.getenv("FLEET_SUPERVISOR_INTERVAL", cfg.get("orchestrator_poll_interval_seconds", 30))),
        "watchdog_poll_interval_seconds": int(os.getenv("WATCHDOG_POLL_INTERVAL", cfg.get("watchdog_poll_interval_seconds", 15))),
        "sprint_watcher_interval_seconds": int(os.getenv("SPRINT_WATCHER_INTERVAL", cfg.get("sprint_watcher_interval_seconds", 60))),
        "auto_restart_idle_agents": cfg.get("auto_restart_idle_agents", True),
    }


def get_workspace_slugs() -> list[str]:
    """Primary + additional Plane workspace slugs (multi-workspace)."""
    multi = load_agent_config().get("multi_workspace", {})
    slugs_env = os.getenv("PLANE_WORKSPACE_SLUGS", "").strip()
    if slugs_env:
        slugs = [s.strip() for s in slugs_env.split(",") if s.strip()]
    else:
        slugs = list(multi.get("workspace_slugs") or [])
    primary = os.getenv("PLANE_WORKSPACE_SLUG") or multi.get("primary_workspace_slug") or "agentbuilder"
    if primary and primary not in slugs:
        slugs.insert(0, primary)
    return slugs or [primary]


def get_project_scope() -> str:
    return os.getenv("PLANE_PROJECT_SCOPE") or load_agent_config().get("multi_workspace", {}).get("project_scope", "all")
