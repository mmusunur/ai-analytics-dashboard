"""
FastAPI Router — Sprint & Agent Task Management
Provides endpoints to fetch live Plane sprint tasks across multiple projects in a workspace.
Includes automatic non-blocking background task worker triggering for Plane task pickup (< 300 lines).
"""

import os
import sys
import time
import threading
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Query, Body
from fastapi.responses import JSONResponse

ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "agents"))

router = APIRouter()

_watcher_lock = threading.Lock()
_last_trigger_time = 0.0


def trigger_watcher_in_background(workspace_slug: Optional[str] = None, project_id: Optional[str] = None):
    """
    Spawns a non-blocking background thread to run SprintWatcherAgent
    whenever there are actionable (unstarted/todo/backlog) tasks in Plane.
    Cooldown: 20s minimum between triggers (was 60s — reduced to improve pickup responsiveness).
    """
    global _last_trigger_time
    now = time.time()
    elapsed = now - _last_trigger_time
    if elapsed < 20.0:
        print(f"[Sprint Router]: Watcher trigger throttled ({elapsed:.1f}s < 20s cooldown). Skipping.")
        return
    _last_trigger_time = now

    def _worker():
        if not _watcher_lock.acquire(blocking=False):
            print("[Sprint Router]: Watcher already running — skipping duplicate trigger.")
            return
        try:
            print(f"[Sprint Router]: Task picker triggered for workspace='{workspace_slug}' project='{project_id}'...")
            from sprint_watcher_agent import SprintWatcherAgent
            watcher = SprintWatcherAgent(poll_interval_seconds=5)
            # If a real project_id was passed (not 'all'), inject it into the watcher's state
            # so _resolve_project_id() has a concrete UUID to work with.
            if project_id and project_id != "all" and len(str(project_id)) > 10:
                watcher.project_id = project_id
                watcher.state["plane_project_id"] = project_id
                print(f"[Sprint Router]: Watcher project_id set to real UUID: {project_id[:8]}...")
            watcher.watch(max_cycles=1)
        except Exception as e:
            print(f"[Sprint Router Watcher Error]: {e}")
        finally:
            _watcher_lock.release()

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


@router.get("/agent-status")
def get_agent_status():
    """
    Return live agent status from memory/agent_state.json.
    Used by the frontend Sprint Board to show a real-time agent activity indicator.
    Includes agent_working flag so the frontend can pause polling during code changes.
    """
    try:
        from memory_manager import load_state, is_agent_working
        state = load_state()
        agents = state.get("agents", {})
        today_session = state.get("today_session", {})
        sprint_watcher = agents.get("sprint_watcher", {})
        builder = agents.get("builder", {})
        tester = agents.get("tester", {})
        return JSONResponse({
            "status": "success",
            "agent_working": is_agent_working(),
            "agent_working_task": state.get("agent_working_task", ""),
            "sprint_watcher": {
                "status": sprint_watcher.get("status", "idle"),
                "current_task": sprint_watcher.get("current_task", "Idle"),
                "last_updated": sprint_watcher.get("last_updated")
            },
            "builder": {
                "status": builder.get("status", "idle"),
                "current_task": builder.get("current_task", "Idle"),
                "last_updated": builder.get("last_updated")
            },
            "tester": {
                "status": tester.get("status", "idle"),
                "current_task": tester.get("current_task", "Idle"),
                "last_updated": tester.get("last_updated")
            },
            "today_session": today_session
        })
    except Exception as e:
        return JSONResponse({"status": "error", "agent_working": False, "message": str(e)})


@router.get("/agent-working")
def get_agent_working():
    """
    Lightweight endpoint — frontend polls every 5s to check if the agent is
    actively modifying code. When True, frontend should pause all data fetching
    to prevent UI disruption from uvicorn hot-reloads and Vite HMR errors.
    """
    try:
        from memory_manager import load_state, is_agent_working
        state = load_state()
        working = is_agent_working()
        return JSONResponse({
            "agent_working": working,
            "task": state.get("agent_working_task", "") if working else "",
            "since": state.get("agent_working_since") if working else None
        })
    except Exception:
        return JSONResponse({"agent_working": False, "task": "", "since": None})


@router.post("/clear-processed-ids")
def clear_processed_task_ids():
    """
    Clear the persisted processed task IDs file so the sprint watcher can
    re-pick tasks that were previously processed (e.g. after a sprint reset
    or when tasks are restored from cancelled to To Do).
    """
    try:
        from pathlib import Path
        import json
        pf = ROOT_DIR / "memory" / ".processed_task_ids.json"
        if pf.exists():
            try:
                data = json.loads(pf.read_text(encoding="utf-8"))
                count = len(data.get("entries", data.get("ids", [])))
            except Exception:
                count = 0
            pf.unlink()
            return JSONResponse({"status": "success", "message": f"Cleared {count} processed task IDs — watcher will re-scan on next trigger."})
        return JSONResponse({"status": "success", "message": "No processed IDs file found — nothing to clear."})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@router.get("/workspaces")
def get_plane_workspaces():
    """Fetch all available Plane workspaces and projects for workspace selection."""
    try:
        from plane_agent import list_workspaces, list_projects
        workspaces = list_workspaces()
        data = []
        for ws in workspaces:
            slug = ws.get("slug") or ws.get("id") or "agentbuilder"
            name = ws.get("name") or slug
            projects = list_projects(slug)
            data.append({
                "name": name,
                "slug": slug,
                "projects": [
                    {"id": p.get("id"), "name": p.get("name"), "identifier": p.get("identifier")}
                    for p in projects
                ]
            })
        return JSONResponse({"status": "success", "workspaces": data})
    except Exception as e:
        print(f"[Workspaces API Error]: {e}")
        return JSONResponse({
            "status": "fallback",
            "workspaces": [
                {
                    "name": "AgentBuilder Workspace",
                    "slug": "agentbuilder",
                    "projects": [
                        {"id": "all", "name": "⚡ All Projects (Aggregate Workspace Tasks)", "identifier": "ALL"},
                        {"id": "6ceb45ad-db0b-42eb-8de1-b4fd05d6593a", "name": "AI Analytics Dashboard", "identifier": "AAD"}
                    ]
                }
            ]
        })


@router.get("/tasks")
def get_sprint_tasks(workspace_slug: Optional[str] = Query(None), project_id: Optional[str] = Query(None)):
    """Fetch live sprint tasks across projects in a workspace and trigger agent task picker."""
    try:
        from plane_agent import get_or_create_project, list_projects, list_tasks, list_sprints, list_active_sprint, update_plane_config_active_workspace_project
        from memory_manager import load_state, save_state

        state = load_state()
        ws_str = workspace_slug if isinstance(workspace_slug, str) and workspace_slug else None
        pid_str = project_id if isinstance(project_id, str) and project_id else None

        ws = ws_str or state.get("plane_workspace_slug") or "agentbuilder"
        pid = pid_str or state.get("plane_project_id") or "all"

        state["plane_workspace_slug"] = str(ws)
        state["plane_project_id"] = str(pid)
        save_state(state)
        update_plane_config_active_workspace_project(str(ws), str(pid))

        # Multi-Project Scanning and Exact Project Name Mapping
        all_projects = list_projects(ws)
        proj_map = {p.get("id"): (p.get("name") or p.get("identifier") or "Project") for p in all_projects if isinstance(p, dict) and p.get("id")}

        projects_to_scan = []
        if not pid or pid == "all":
            projects_to_scan = all_projects if all_projects else [{"id": get_or_create_project(ws), "name": "AI Analytics Dashboard"}]
        else:
            p_name = proj_map.get(pid, "AI Analytics Dashboard")
            projects_to_scan = [{"id": pid, "name": p_name}]

        active_sprint = None
        all_raw_tasks = []
        sprints = []

        for p_info in projects_to_scan:
            p_id = p_info.get("id")
            p_name = p_info.get("name") or proj_map.get(p_id, "Project")
            if not p_id:
                continue
            p_tasks = list_tasks(p_id, ws)
            for t in p_tasks:
                t["project_id"] = p_id
                t["project_name"] = p_name
                all_raw_tasks.append(t)

            if not sprints:
                sprints = list_sprints(p_id, ws)
            if not active_sprint:
                # Use date-aware active sprint selection instead of blindly taking sprints[0].
                # sprints[0] is often the OLDEST/EXPIRED sprint — Plane auto-cancels tasks
                # in expired cycles, which was causing manually In-Progress tasks to flip to Cancelled.
                active_sprint = list_active_sprint(p_id, ws)

        # Resolve the display sprint: prefer active (date-valid), then newest fallback
        if active_sprint:
            current_sprint = active_sprint
        elif sprints:
            # Sort by created_at desc so we get the newest, not the expired first one
            current_sprint = sorted(sprints, key=lambda s: s.get("created_at", ""), reverse=True)[0]
        else:
            current_sprint = {"name": "Sprint 1 - Foundation", "id": "sprint-1"}

        # Build cycle-task membership map so we only show tasks in the ACTIVE sprint.
        # Tasks in expired cycles are excluded — Plane auto-cancels them and they
        # should never trigger the watcher or appear as actionable.
        active_cycle_task_ids: set = set()
        if current_sprint.get("id") and current_sprint["id"] != "sprint-1":
            try:
                cycle_id = current_sprint["id"]
                cycle_issues_url = (
                    f"https://api.plane.so/api/v1/workspaces/{ws}/projects/"
                    f"{projects_to_scan[0]['id']}/cycles/{cycle_id}/cycle-issues/"
                )
                import httpx as _httpx
                _headers = {"X-API-Key": os.getenv("PLANE_API_TOKEN", ""), "Content-Type": "application/json"}
                with _httpx.Client(timeout=10) as _c:
                    _resp = _c.get(cycle_issues_url, headers=_headers)
                    if _resp.status_code == 200:
                        for ci in _resp.json().get("results", []):
                            issue_id = ci.get("issue") or (ci.get("issue_detail") or {}).get("id")
                            if issue_id:
                                active_cycle_task_ids.add(issue_id)
            except Exception as _ce:
                print(f"[Sprint Router]: Could not fetch cycle issues (non-fatal): {_ce}")

        # If we got cycle membership, filter raw tasks to this sprint only.
        # If cycle fetch failed (empty set), show all tasks as a safe fallback.
        if active_cycle_task_ids:
            all_raw_tasks = [t for t in all_raw_tasks if t.get("id") in active_cycle_task_ids]

        backlog_list = []
        todo_list = []
        in_progress_list = []
        completed_list = []
        cancelled_list = []   # Explicitly track cancelled — NOT the same as backlog

        has_actionable_tasks = False

        for task in all_raw_tasks:
            sg = (task.get("state_group") or "").lower()
            state_name = str(task.get("state_detail", {}).get("name") if isinstance(task.get("state_detail"), dict) else task.get("state", "")).lower()

            task_obj = {
                "id": task.get("id"),
                "name": task.get("name", "Unnamed Task"),
                "priority": task.get("priority", "medium"),
                "story_points": task.get("estimate_point") or 3,
                "state_group": sg,
                "state_name": state_name,
                "project_id": task.get("project_id"),
                "project_name": task.get("project_name", "Project"),
                "created_at": task.get("created_at"),
                "updated_at": task.get("updated_at"),
                "description": task.get("description_stripped") or task.get("description_html") or ""
            }

            if sg in ("completed", "done", "closed"):
                completed_list.append(task_obj)
            elif sg in ("cancelled", "wont_fix", "rejected", "duplicate"):
                # Cancelled tasks are NOT backlog — they are closed/rejected
                # Do NOT set has_actionable_tasks for cancelled tasks
                cancelled_list.append(task_obj)
            elif sg in ("started", "in_progress", "in progress", "active"):
                # In Progress — agent is already working on these OR user moved them manually.
                # Do NOT mark as actionable — the agent must never auto-pick 'started' tasks.
                in_progress_list.append(task_obj)
            elif sg in ("todo", "to_do", "triaged"):
                todo_list.append(task_obj)
                has_actionable_tasks = True
            elif sg in ("unstarted", "backlog"):
                # Backlog = holding area (not yet ready for pickup)
                # unstarted = explicitly To Do (ready for pickup)
                backlog_list.append(task_obj)
                if sg == "unstarted":   # Only unstarted is actionable, not raw backlog
                    has_actionable_tasks = True
            else:
                # Unknown state — treat as backlog display, not actionable
                backlog_list.append(task_obj)

        # Trigger watcher ONLY for tasks explicitly in unstarted/todo/triaged/backlog state.
        # These mirror AGENT_PICKUP_GROUPS in sprint_watcher_agent.py exactly.
        # "started"   = In Progress (human or agent action) — NEVER trigger watcher for these
        # "cancelled" = closed/rejected by human — NEVER trigger watcher
        TRIGGER_GROUPS = {"unstarted", "todo", "triaged"}
        pickup_tasks = [
            task for task in all_raw_tasks
            if (task.get("state_group") or "").lower() in TRIGGER_GROUPS
            and (task.get("state_group") or "").lower() not in {"started", "in_progress", "completed", "cancelled"}
        ]
        has_pickup_tasks = len(pickup_tasks) > 0
        if has_pickup_tasks:
            # Pass the first real project UUID to the watcher so it can resolve tasks correctly.
            # Never pass "all" — that causes the watcher's _verify_task_still_pickupable to fail.
            real_pid = pid if (pid and pid != "all" and len(str(pid)) > 10) else None
            if not real_pid and projects_to_scan:
                real_pid = projects_to_scan[0].get("id")
            print(f"[Sprint Router]: {len(pickup_tasks)} actionable task(s) found — triggering watcher (project_id={real_pid})")
            trigger_watcher_in_background(ws, real_pid)
        else:
            print(f"[Sprint Router]: No pickup-eligible tasks found — watcher not triggered.")

        total_tasks = len(all_raw_tasks)
        # Completion % excludes cancelled tasks from denominator (they're not part of sprint scope)
        open_tasks = total_tasks - len(cancelled_list)
        completed_count = len(completed_list)
        completion_pct = round((completed_count / open_tasks * 100), 1) if open_tasks > 0 else 100.0

        return JSONResponse({
            "status": "success",
            "workspace_slug": ws,
            "project_id": pid,
            "scanned_projects_count": len(projects_to_scan),
            "sprint": {
                "name": current_sprint.get("name", "Sprint AAD-5"),
                "id": current_sprint.get("id"),
                "total_tasks": total_tasks,
                "open_tasks": open_tasks,
                "completed_tasks": completed_count,
                "in_progress_tasks": len(in_progress_list),
                "todo_tasks": len(todo_list),
                "backlog_tasks": len(backlog_list),
                "cancelled_tasks": len(cancelled_list),
                "completion_percentage": completion_pct
            },
            "tasks": {
                "backlog": backlog_list,
                "todo": todo_list,
                "in_progress": in_progress_list,
                "completed": completed_list,
                "cancelled": cancelled_list,  # Separated from backlog — these are closed/rejected
                "all": [
                    {
                        "id": t.get("id"),
                        "name": t.get("name", "Unnamed Task"),
                        "priority": t.get("priority", "medium"),
                        "points": t.get("estimate_point") or 3,
                        "status": t.get("state_group", "unstarted"),
                        "project_id": t.get("project_id"),
                        "project_name": t.get("project_name", "Project"),
                        "description": t.get("description_stripped") or ""
                    }
                    for t in all_raw_tasks
                ]
            },
            "active_agent_tasks": state.get("active_tasks", [])
        })

    except Exception as e:
        print(f"[Sprints API Error]: {repr(e)}")
        from memory_manager import load_state
        state = load_state()
        return JSONResponse({
            "status": "fallback",
            "sprint": {
                "name": "Sprint AAD-5 · Real-time Warehouse Item & Procurement Analytics",
                "id": "sprint-aad-5",
                "total_tasks": 18,
                "completed_tasks": 18,
                "in_progress_tasks": 0,
                "todo_tasks": 0,
                "backlog_tasks": 0,
                "completion_percentage": 100.0
            },
            "tasks": {"backlog": [], "todo": [], "in_progress": [], "completed": [], "all": []},
            "active_agent_tasks": state.get("active_tasks", [])
        })


@router.post("/extend-sprint")
def extend_sprint_endpoint(
    project_id: str = Body(..., embed=True),
    cycle_id: str = Body(..., embed=True),
    days: int = Body(14, embed=True),
    workspace_slug: Optional[str] = Body(None, embed=True)
):
    """
    Extend the active sprint's end_date by N days (default 14).
    Prevents Plane from auto-cancelling unfinished tasks when a cycle expires.
    Called from the Sprint Board when the UI detects an expiring/expired sprint.
    """
    try:
        from plane_agent import extend_sprint
        from datetime import datetime, timedelta

        ws = workspace_slug or "agentbuilder"
        new_end_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        result = extend_sprint(project_id, cycle_id, new_end_date, ws)
        if result:
            return JSONResponse({
                "status": "success",
                "message": f"Sprint extended to {new_end_date} (+{days} days)",
                "new_end_date": new_end_date,
                "cycle": result
            })
        return JSONResponse({"status": "error", "message": "Plane API returned empty response — check project_id and cycle_id"}, status_code=400)
    except Exception as e:
        print(f"[Extend Sprint Error]: {repr(e)}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@router.post("/restore-task")
def restore_cancelled_task(
    project_id: str = Body(..., embed=True),
    task_id: str = Body(..., embed=True),
    workspace_slug: Optional[str] = Body(None, embed=True)
):
    """
    Restore a task that was auto-cancelled by Plane's sprint-expiry process
    back to 'unstarted' (To Do) so it can be picked up and worked on again.
    Only acts on tasks that are actually in a 'cancelled' state — safe to call
    on any task.
    """
    try:
        from plane_agent import restore_task_from_cancelled
        ws = workspace_slug or "agentbuilder"
        result = restore_task_from_cancelled(project_id, task_id, ws)
        if result.get("status") == "already_ok":
            return JSONResponse({"status": "success", "message": f"Task is already in '{result['group']}' — no change needed"})
        if result:
            return JSONResponse({"status": "success", "message": "Task restored to To Do (unstarted)", "task": result})
        return JSONResponse({"status": "error", "message": "Could not restore task — check project_id and task_id"}, status_code=400)
    except Exception as e:
        print(f"[Restore Task Error]: {repr(e)}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
