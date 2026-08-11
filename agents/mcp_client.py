"""
MCP Client — unified tool routing layer for AgenticOps AI.

Agents call call_tool(name, args) instead of importing each backend directly.
Config: mcp_servers/mcp_config.json
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).parent.parent
CONFIG_PATH = ROOT_DIR / "mcp_servers" / "mcp_config.json"

# Tool → server id
TOOL_SERVER_MAP = {
    "list_tasks": "plane",
    "update_task_status": "plane",
    "add_comment": "plane",
    "list_projects": "plane",
    "get_single_task": "plane",
    "git_commit": "github",
    "git_push": "github",
    "get_commit_log": "github",
    "get_meaningful_changed_files": "github",
    "load_state": "memory",
    "update_agent_status": "memory",
    "set_pipeline_status": "memory",
    "log_task_result": "memory",
    "get_task_queue": "memory",
    "save_conversation": "memory",
    "run_unit_tests": "browser",
    "run_browser_tests": "browser",
    "run_sprint_task_tests": "browser",
}


def load_mcp_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {"mcpServers": {}}


def _env_configured(keys: list[str]) -> bool:
    for key in keys:
        val = os.getenv(key, "")
        if not val or val.startswith("${"):
            return False
    return True


def _check_server_health(server_id: str, quick: bool = True) -> dict:
    """Lightweight health probe per MCP server. quick=True skips external API calls."""
    status = "online"
    detail = "OK"
    try:
        if server_id == "plane":
            if not _env_configured(["PLANE_API_TOKEN", "PLANE_WORKSPACE_SLUG"]):
                return {"status": "degraded", "detail": "Missing PLANE_API_TOKEN or PLANE_WORKSPACE_SLUG"}
            if quick:
                return {"status": "online", "detail": "Plane credentials configured"}
            from agents import plane_agent
            workspaces = plane_agent.list_workspaces()
            if not workspaces:
                return {"status": "degraded", "detail": "Plane API reachable but no workspaces returned"}
        elif server_id == "github":
            from agents import git_agent
            git_agent.init_repo()
            detail = "Git repo initialized"
            if not _env_configured(["GITHUB_TOKEN"]):
                status = "degraded"
                detail = "Local git OK — GITHUB_TOKEN not set (push may fail)"
        elif server_id == "memory":
            state_file = ROOT_DIR / "memory" / "agent_state.json"
            if not state_file.parent.exists():
                status = "degraded"
                detail = "memory/ directory missing"
            else:
                detail = "State store ready"
        elif server_id == "browser":
            sys.path.insert(0, str(ROOT_DIR / "scripts"))
            try:
                from server_health import servers_healthy
                sh = servers_healthy()
                if not sh["healthy"]:
                    status = "degraded"
                    detail = f"Servers: backend={sh['backend']} frontend={sh['frontend']}"
                else:
                    detail = "Backend :8000 + Frontend :5173 up"
            except Exception as exc:
                status = "degraded"
                detail = str(exc)[:120]
    except Exception as exc:
        status = "offline"
        detail = str(exc)[:200]
    return {"status": status, "detail": detail}


def get_mcp_registry() -> dict:
    """Return full MCP registry with live health for UI / API."""
    config = load_mcp_config()
    servers = []
    for sid, meta in config.get("mcpServers", {}).items():
        health = _check_server_health(sid)
        env_keys = list((meta.get("env") or {}).keys())
        servers.append({
            "id": sid,
            "name": meta.get("name", sid),
            "description": meta.get("description", ""),
            "backedBy": meta.get("backedBy", ""),
            "usedBy": meta.get("usedBy", []),
            "tools": meta.get("tools", []),
            "toolCount": len(meta.get("tools", [])),
            "command": meta.get("command", ""),
            "args": meta.get("args", []),
            "envConfigured": _env_configured(env_keys) if env_keys else True,
            "envKeys": env_keys,
            "health": health["status"],
            "healthDetail": health["detail"],
        })
    online = sum(1 for s in servers if s["health"] == "online")
    return {
        "version": config.get("version", "1.0"),
        "description": config.get("description", ""),
        "configPath": str(CONFIG_PATH.relative_to(ROOT_DIR)).replace("\\", "/"),
        "clientModule": "agents/mcp_client.py",
        "serverCount": len(servers),
        "onlineCount": online,
        "toolCount": sum(s["toolCount"] for s in servers),
        "servers": servers,
        "checkedAt": datetime.now().isoformat(),
    }


def call_tool(tool_name: str, args: dict | None = None) -> Any:
    """Route a tool call to the correct agent backend."""
    args = args or {}
    server_id = TOOL_SERVER_MAP.get(tool_name)
    if not server_id:
        raise ValueError(f"Unknown MCP tool: {tool_name}")

    if server_id == "plane":
        from agents import plane_agent
        if tool_name == "list_tasks":
            return plane_agent.list_tasks(args["project_id"], args.get("workspace_slug"))
        if tool_name == "update_task_status":
            return plane_agent.update_task_status(
                args["project_id"], args["task_id"], args["state_name"], args.get("workspace_slug")
            )
        if tool_name == "add_comment":
            return plane_agent.add_comment(
                args["project_id"], args["task_id"], args["comment"], args.get("workspace_slug")
            )
        if tool_name == "list_projects":
            return plane_agent.list_projects(args.get("workspace_slug"))
        if tool_name == "get_single_task":
            return plane_agent.get_single_task(
                args["project_id"], args["task_id"], args.get("workspace_slug")
            )

    if server_id == "github":
        from agents import git_agent
        if tool_name == "git_commit":
            git_agent.init_repo()
            files = git_agent.get_meaningful_changed_files()
            if not files:
                return {"ok": False, "reason": "no_changes"}
            git_agent.stage_all()
            return {"ok": git_agent.commit(args.get("message", "Agent commit"))}
        if tool_name == "git_push":
            return {"ok": git_agent.push(args.get("branch", "main"))}
        if tool_name == "get_commit_log":
            return git_agent.get_commit_log(args.get("n", 5))
        if tool_name == "get_meaningful_changed_files":
            return git_agent.get_meaningful_changed_files()

    if server_id == "memory":
        from agents import memory_manager
        if tool_name == "load_state":
            return memory_manager.load_state()
        if tool_name == "update_agent_status":
            memory_manager.update_agent_status(args["agent_name"], args["status"], args.get("current_task", "Idle"))
            return {"ok": True}
        if tool_name == "set_pipeline_status":
            memory_manager.set_pipeline_status(
                args["phase"], args.get("task_id", ""), args.get("task_title", ""),
                args.get("active_agent", ""), args.get("message", ""),
            )
            return {"ok": True}
        if tool_name == "log_task_result":
            memory_manager.log_task_result(
                args.get("task_id", ""), args.get("task_title", ""), args.get("agent_name", ""),
                args.get("status", ""), args.get("output", ""), args.get("duration_seconds", 0.0),
            )
            return {"ok": True}
        if tool_name == "get_task_queue":
            return memory_manager.get_task_queue()

    if server_id == "browser":
        if tool_name == "run_unit_tests":
            res = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/unit/", "-q"],
                cwd=str(ROOT_DIR), capture_output=True, text=True, timeout=600,
            )
            return {"ok": res.returncode == 0, "output": (res.stdout or "")[-500:]}
        if tool_name in ("run_browser_tests", "run_sprint_task_tests"):
            cmd = [sys.executable, str(ROOT_DIR / "agents" / "tester_agent.py")]
            for key in ("task_id", "task_title", "description", "project_name"):
                if args.get(key):
                    cmd.extend([f"--{key.replace('_', '-')}", str(args[key])])
            res = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, timeout=900)
            return {"ok": res.returncode == 0, "output": ((res.stdout or "") + (res.stderr or ""))[-800:]}

    raise ValueError(f"Tool '{tool_name}' not implemented for server '{server_id}'")


if __name__ == "__main__":
    import pprint
    pprint.pp(get_mcp_registry())
