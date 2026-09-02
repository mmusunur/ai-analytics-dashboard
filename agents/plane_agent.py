"""
Plane Agent — Manages tasks, sprints, and issues in Plane via REST API.
Includes dynamic workspace & project switching support (< 300 lines).
"""

import sys
import os
import json
import time
import httpx
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict
from rich.console import Console
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "agents"))
import utf8_fix

load_dotenv()
console = Console(legacy_windows=False)
PLANE_CONFIG_FILE = ROOT_DIR / "config" / "plane_config.json"
PLANE_API_TOKEN = os.getenv("PLANE_API_TOKEN", "")
PLANE_WORKSPACE_SLUG = os.getenv("PLANE_WORKSPACE_SLUG", "agentbuilder")
PLANE_BASE_URL = "https://api.plane.so/api/v1"
HEADERS = {"X-API-Key": PLANE_API_TOKEN, "Content-Type": "application/json"}
CLIENT_TIMEOUT = httpx.Timeout(20.0, connect=8.0)


def _get_client() -> httpx.Client:
    return httpx.Client(timeout=CLIENT_TIMEOUT, follow_redirects=True)


def _load_plane_config() -> dict:
    if PLANE_CONFIG_FILE.exists():
        with open(PLANE_CONFIG_FILE) as f:
            return json.load(f)
    return {"workspace_slug": PLANE_WORKSPACE_SLUG, "project_name": "AI Analytics Dashboard", "project_id": None}


def _save_plane_config(config: dict) -> None:
    PLANE_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PLANE_CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def update_plane_config_active_workspace_project(workspace_slug: str, project_id: Optional[str] = None, project_name: Optional[str] = None) -> None:
    """Dynamically update config/plane_config.json with selected workspace, project_name, and project_id."""
    config = _load_plane_config()
    config["workspace_slug"] = workspace_slug
    config["dynamic_workspace_selection"] = True
    if project_id:
        config["project_id"] = project_id
    if project_name:
        config["project_name"] = project_name
    _save_plane_config(config)


import time

_CACHE_TTL = 3600.0  # Cache Plane API calls for 1 hour to avoid slow Plane API
_projects_cache = {}
_workspaces_cache = {"timestamp": 0.0, "data": []}
_refresh_in_progress = {"workspaces": False, "projects": {}}


def list_workspaces() -> List[Dict]:
    """Return accessible Plane workspaces.

    Plane's free/hobby plan returns 404 for GET /api/v1/workspaces/ (workspace listing
    is a paid-tier endpoint). Instead we build the workspace list from the env vars
    PLANE_WORKSPACE_SLUG / PLANE_WORKSPACE_SLUGS which are already correctly set.
    The cached data path is kept so callers that populate it via other means still work.
    """
    if _workspaces_cache["data"]:
        return _workspaces_cache["data"]

    # Build workspace list from env — no API call needed
    slugs_raw = os.getenv("PLANE_WORKSPACE_SLUGS", "") or ""
    slugs = [s.strip() for s in slugs_raw.split(",") if s.strip()]
    if not slugs:
        slugs = [PLANE_WORKSPACE_SLUG]
    workspaces = [{"name": s, "slug": s} for s in slugs]
    _workspaces_cache["data"] = workspaces
    _workspaces_cache["timestamp"] = time.time()
    return workspaces


def list_projects(workspace_slug: Optional[str] = None) -> List[Dict]:
    """Fetch all projects in a workspace (synchronous, with 1-hour in-memory cache).

    Previously used a background thread which caused the first call to always return []
    (race condition: caller got result before thread finished). Now fetches synchronously
    so the first call always returns real data.
    """
    ws = workspace_slug or PLANE_WORKSPACE_SLUG
    now = time.time()

    # Return from cache if still fresh
    if ws in _projects_cache:
        cached_ts, cached_data = _projects_cache[ws]
        if cached_data and (now - cached_ts) < _CACHE_TTL:
            return cached_data

    # Synchronous fetch — no background thread
    url = f"{PLANE_BASE_URL}/workspaces/{ws}/projects/"
    try:
        with _get_client() as client:
            resp = client.get(url, headers=HEADERS, timeout=httpx.Timeout(25.0))
            resp.raise_for_status()
            data = resp.json()
            res = data.get("results", data) if isinstance(data, dict) else data
            if res:
                _projects_cache[ws] = (now, res)
                return res
    except Exception as e:
        console.print(f"[yellow]Plane projects ({ws}): {e}[/yellow]")

    # Return stale cache if fresh fetch failed
    if ws in _projects_cache:
        return _projects_cache[ws][1]
    
    # Fallback default projects for agentbuilder workspace
    fallback = [
        {"id": "6ceb45ad-db0b-42eb-8de1-b4fd05d6593a", "name": "AI Analytics Dashboard", "identifier": "AAD"},
        {"id": "f7186b86-7da4-4639-ae45-f815fc4d0614", "name": "AgenticOps AI - Enterprise Control Plane", "identifier": "AGENTICOPS"},
        {"id": "7e52225e-674b-4bbb-b09a-e23117d5e6f1", "name": "agentbuilder", "identifier": "AGENT"},
    ]
    _projects_cache[ws] = (now, fallback)
    return fallback


def get_or_create_project(workspace_slug: Optional[str] = None) -> str:
    config = _load_plane_config()
    ws = workspace_slug or config.get("workspace_slug") or PLANE_WORKSPACE_SLUG
    if config.get("project_id") and not workspace_slug:
        return config["project_id"]

    url = f"{PLANE_BASE_URL}/workspaces/{ws}/projects/"
    payload = {
        "name": config.get("project_name", "AI Analytics Dashboard"),
        "identifier": "AAD",
        "description": "Agentic AI Analytics Dashboard",
        "network": 2
    }
    for attempt in range(3):
        try:
            with _get_client() as client:
                resp = client.post(url, headers=HEADERS, json=payload)
                resp.raise_for_status()
                project = resp.json()
                project_id = project["id"]
                config["project_id"] = project_id
                config["workspace_slug"] = ws
                _save_plane_config(config)
                return project_id
        except Exception as e:
            if attempt == 2:
                break
            time.sleep(1)
    return config.get("project_id", "")


def list_sprints(project_id: str, workspace_slug: Optional[str] = None) -> list:
    ws = workspace_slug or PLANE_WORKSPACE_SLUG
    url = f"{PLANE_BASE_URL}/workspaces/{ws}/projects/{project_id}/cycles/"
    try:
        with _get_client() as client:
            resp = client.get(url, headers=HEADERS)
            resp.raise_for_status()
            return resp.json().get("results", [])
    except Exception:
        return []


def list_active_sprint(project_id: str, workspace_slug: Optional[str] = None) -> Optional[Dict]:
    """
    Return the CURRENTLY ACTIVE sprint (cycle) for a project.

    Plane auto-cancels tasks whose sprint cycle has expired (start_date in the past
    and end_date passed). This function finds the sprint whose date window includes
    today, preventing the backend from ever pointing at an expired sprint.

    Priority order:
      1. Sprint whose start_date <= today <= end_date  (actively running)
      2. Sprint whose start_date <= today and no end_date  (open-ended / ongoing)
      3. Sprint with a future start_date closest to today  (upcoming)
      4. Most recently created sprint (fallback — never return expired sprints[0])
    """
    sprints = list_sprints(project_id, workspace_slug)
    if not sprints:
        return None

    today = datetime.now().date()

    def _parse_date(d: Optional[str]):
        if not d:
            return None
        try:
            return datetime.fromisoformat(d[:10]).date()
        except Exception:
            return None

    running, open_ended, upcoming, all_valid = [], [], [], []

    for s in sprints:
        s_start = _parse_date(s.get("start_date"))
        s_end   = _parse_date(s.get("end_date"))

        if s_start and s_end:
            if s_start <= today <= s_end:
                running.append(s)       # Actively running right now
            elif s_end < today:
                pass                    # Expired — skip entirely
            elif s_start > today:
                upcoming.append(s)      # Hasn't started yet
        elif s_start and not s_end:
            if s_start <= today:
                open_ended.append(s)    # Started, no end — ongoing
        else:
            all_valid.append(s)         # No dates — include as fallback only

    if running:
        # Multiple running sprints: pick the one ending soonest
        return sorted(running, key=lambda s: _parse_date(s.get("end_date")) or today)[0]
    if open_ended:
        return open_ended[-1]           # Most recently started open-ended sprint
    if upcoming:
        return sorted(upcoming, key=lambda s: _parse_date(s.get("start_date")) or today)[0]
    if all_valid:
        return all_valid[-1]            # Last sprint with no dates

    # Absolute last resort: newest sprint in the list (avoid stale [0])
    console.print("[yellow]⚠️  All sprints appear expired — returning newest sprint as fallback.[/yellow]")
    return sorted(sprints, key=lambda s: s.get("created_at", ""), reverse=True)[0]


def list_tasks(project_id: str, workspace_slug: Optional[str] = None) -> list:
    ws = workspace_slug or PLANE_WORKSPACE_SLUG
    url = f"{PLANE_BASE_URL}/workspaces/{ws}/projects/{project_id}/issues/"
    try:
        with _get_client() as client:
            resp = client.get(url, headers=HEADERS)
            resp.raise_for_status()
            return resp.json().get("results", [])
    except Exception:
        return []


def get_single_task(project_id: str, task_id: str, workspace_slug: Optional[str] = None) -> Optional[Dict]:
    """
    Fetch a single Plane issue by ID to get its LIVE current state.
    Used by the sprint watcher to verify a task's state before processing
    (prevents race conditions where stale state_group causes re-pickup of
    manually In Progress tasks).
    Returns the issue dict, or None on failure.
    """
    ws = workspace_slug or PLANE_WORKSPACE_SLUG
    url = f"{PLANE_BASE_URL}/workspaces/{ws}/projects/{project_id}/issues/{task_id}/"
    try:
        with _get_client() as client:
            resp = client.get(url, headers=HEADERS)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        console.print(f"[yellow]⚠️ Could not fetch task {task_id}: {e}[/yellow]")
        return None


def get_states(project_id: str, workspace_slug: Optional[str] = None) -> list:
    ws = workspace_slug or PLANE_WORKSPACE_SLUG
    url = f"{PLANE_BASE_URL}/workspaces/{ws}/projects/{project_id}/states/"
    try:
        with _get_client() as client:
            resp = client.get(url, headers=HEADERS)
            resp.raise_for_status()
            return resp.json().get("results", [])
    except Exception:
        return []


def update_task_status(project_id: str, task_id: str, state_name: str, workspace_slug: Optional[str] = None) -> dict:
    """
    Update a Plane issue state. Resolves state by GROUP name first (reliable),
    then falls back to display name match. Plane group names are:
      backlog | unstarted | started | completed | cancelled
    """
    ws = workspace_slug or PLANE_WORKSPACE_SLUG
    states = get_states(project_id, ws)

    # 1. Match by group name first (e.g. "started", "completed") — most reliable
    state_obj = next(
        (s for s in states if s.get("group", "").lower() == state_name.lower()),
        None
    )
    # 2. Fallback: match by display name (e.g. "In Progress", "Done")
    if not state_obj:
        state_obj = next(
            (s for s in states if s.get("name", "").lower() == state_name.lower()),
            None
        )

    if not state_obj:
        console.print(f"[yellow]⚠️ No Plane state found matching group/name '{state_name}' in project {project_id}. Available: {[s.get('name') for s in states]}[/yellow]")
        return {}

    state_id = state_obj["id"]
    console.print(f"[dim]-> Resolved state '{state_name}' -> '{state_obj.get('name')}' (id={state_id[:8]})[/dim]")
    url = f"{PLANE_BASE_URL}/workspaces/{ws}/projects/{project_id}/issues/{task_id}/"
    payload = {"state": state_id}

    for attempt in range(4):
        try:
            with _get_client() as client:
                resp = client.patch(url, headers=HEADERS, json=payload)
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            if attempt == 3:
                console.print(f"[yellow]⚠️ Failed to update task status after retries: {e}[/yellow]")
                return {}
            time.sleep(1.5 * (attempt + 1))


def add_comment(project_id: str, task_id: str, comment_text: str, workspace_slug: Optional[str] = None) -> dict:
    ws = workspace_slug or PLANE_WORKSPACE_SLUG
    url = f"{PLANE_BASE_URL}/workspaces/{ws}/projects/{project_id}/issues/{task_id}/comments/"
    payload = {"comment_html": f"<p>{comment_text}</p>"}

    for attempt in range(3):
        try:
            with _get_client() as client:
                resp = client.post(url, headers=HEADERS, json=payload)
                resp.raise_for_status()
                return resp.json()
        except Exception:
            if attempt == 2:
                return {}
            time.sleep(1.5)


def extend_sprint(project_id: str, cycle_id: str, new_end_date: str, workspace_slug: Optional[str] = None) -> dict:
    """
    Extend a Plane sprint cycle's end_date to prevent auto-cancellation of tasks.

    Plane auto-cancels unfinished tasks when a cycle's end_date passes.
    This function patches the cycle to push the end_date forward so in-flight
    tasks are not automatically cancelled by Plane's cycle-completion process.

    Args:
        project_id:   Plane project ID
        cycle_id:     Plane cycle (sprint) ID
        new_end_date: ISO date string 'YYYY-MM-DD' for the new end date
        workspace_slug: optional workspace override
    Returns:
        Updated cycle dict, or {} on failure.
    """
    ws = workspace_slug or PLANE_WORKSPACE_SLUG
    url = f"{PLANE_BASE_URL}/workspaces/{ws}/projects/{project_id}/cycles/{cycle_id}/"
    payload = {"end_date": new_end_date}
    try:
        with _get_client() as client:
            resp = client.patch(url, headers=HEADERS, json=payload)
            resp.raise_for_status()
            console.print(f"[green]✅ Sprint extended to {new_end_date}[/green]")
            return resp.json()
    except Exception as e:
        console.print(f"[yellow]⚠️ Could not extend sprint: {e}[/yellow]")
        return {}


def restore_task_from_cancelled(project_id: str, task_id: str, workspace_slug: Optional[str] = None) -> dict:
    """
    Move a task that was auto-cancelled by Plane (due to sprint expiry) back to
    the 'unstarted' (To Do) state so it can be worked on again.

    This is a targeted recovery function — it ONLY moves tasks OUT of 'cancelled'
    back to 'unstarted'. It will never touch tasks that are already in a valid state.
    """
    ws = workspace_slug or PLANE_WORKSPACE_SLUG
    # First verify the task is actually cancelled before restoring
    live = get_single_task(project_id, task_id, ws)
    if not live:
        return {}
    live_group = (
        (live.get("state_detail") or {}).get("group") or live.get("state_group") or ""
    ).lower()
    if live_group not in ("cancelled", "wont_fix", "rejected"):
        console.print(f"[dim]Task {task_id[:8]} is '{live_group}' — no restore needed.[/dim]")
        return {"status": "already_ok", "group": live_group}
    # Move back to unstarted (To Do)
    console.print(f"[cyan]Restoring task {task_id[:8]} from '{live_group}' -> 'unstarted'[/cyan]")
    return update_task_status(project_id, task_id, "unstarted", ws)


if __name__ == "__main__":
    console.print("[blue]✈️ Plane Agent Status Check[/blue]")
