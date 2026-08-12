import sys
import json
import time
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from rich.console import Console
try:
    from memory_helpers import cleanup_old_memory, load_conversation
except ImportError:
    from agents.memory_helpers import cleanup_old_memory, load_conversation

console = Console(force_terminal=True)

ROOT_DIR = Path(__file__).parent.parent
MEMORY_DIR = ROOT_DIR / "memory"
STATE_FILE = MEMORY_DIR / "agent_state.json"
_PID_CACHE = {"at": 0.0, "pids": {}}
_PID_CACHE_TTL = 2.5
CONVERSATIONS_DIR = MEMORY_DIR / "conversations"
TASK_HISTORY_DIR = MEMORY_DIR / "task_history"


def _ensure_dirs():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
    TASK_HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def load_state() -> dict:
    _ensure_dirs()
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "plane_project_id": None,
        "agents": {
            "orchestrator": {"status": "idle", "current_task": "Idle", "last_updated": None},
            "builder": {"status": "idle", "current_task": "Idle", "last_updated": None},
            "tester": {"status": "idle", "current_task": "Idle", "last_updated": None},
            "sprint_watcher": {"status": "idle", "current_task": "Idle", "last_updated": None},
            "git_agent": {"status": "idle", "current_task": "Idle", "last_updated": None},
            "memory": {"status": "idle", "current_task": "Idle", "last_updated": None},
        },
        "active_sprint_id": None,
        "last_conversation_update": None
    }


def save_state(state: dict):
    _ensure_dirs()
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception as e:
        console.print(f"[yellow]⚠️ Failed to save agent state: {e}[/yellow]")


def update_agent_status(agent_name: str, status: str, current_task: str = "Idle"):
    state = load_state()
    if agent_name in state.get("agents", {}):
        state["agents"][agent_name] = {
            "status": status,
            "current_task": current_task,
            "last_updated": datetime.now().isoformat()
        }
        save_state(state)


def set_agent_working(is_working: bool, task_title: str = ""):
    """
    Broadcast a global 'agent_working' flag to the frontend.
    When True: pause aggressive polling during Build (file changes / hot reload).
    Do NOT set True during Test — browser tests run 5–15 min; UI must stay live.
    Always call set_agent_working(False) in a finally block.
    """
    state = load_state()
    state["agent_working"] = is_working
    state["agent_working_task"] = task_title if is_working else ""
    state["agent_working_since"] = datetime.now().isoformat() if is_working else None
    save_state(state)


PHASE_PROGRESS = {
    "idle": 0,
    "pickup": 15,
    "building": 40,
    "retry": 50,
    "testing": 65,
    "closing": 85,
    "git_push": 95,
    "done": 100,
    "failed": 0,
}

# Persisted for Build detail popup — must survive phase transitions on the same task.
BUILD_DETAIL_KEYS = (
    "build_outcome",
    "build_duration_seconds",
    "build_files_modified",
    "build_intents",
    "build_functionality",
    "build_usage_guide",
    "build_detail_updated_at",
)

BUILD_PROGRESS_KEYS = (
    "build_started_at",
    "build_subphase",
)


def _carry_build_fields(pipeline: dict, prev: dict, task_id: str, phase: str) -> None:
    """Keep build popup data for the active task from Build through Done."""
    if not task_id or task_id != prev.get("task_id"):
        _merge_build_snapshot(pipeline, task_id)
        return
    for key in BUILD_DETAIL_KEYS:
        if key in prev:
            pipeline[key] = prev[key]
    if phase in ("building", "retry"):
        for key in BUILD_PROGRESS_KEYS:
            if key in prev:
                pipeline[key] = prev[key]
    _merge_build_snapshot(pipeline, task_id)


def _persist_build_snapshot(task_id: str, pipeline: dict) -> None:
    """Store build detail per task so UI survives phase transitions and idle reset."""
    if not task_id:
        return
    snap = {}
    for key in (*BUILD_DETAIL_KEYS, *BUILD_PROGRESS_KEYS):
        if key in pipeline and pipeline[key] not in (None, "", []):
            snap[key] = pipeline[key]
    if not snap:
        return
    state = load_state()
    snapshots = dict(state.get("build_snapshots_by_task") or {})
    snapshots[task_id] = {
        **snapshots.get(task_id, {}),
        **snap,
        "task_title": pipeline.get("task_title") or snapshots.get(task_id, {}).get("task_title", ""),
        "updated_at": datetime.now().isoformat(),
    }
    # Keep last 20 tasks
    if len(snapshots) > 20:
        for old_id in list(snapshots.keys())[:-20]:
            snapshots.pop(old_id, None)
    state["build_snapshots_by_task"] = snapshots
    save_state(state)


def _merge_build_snapshot(pipeline: dict, task_id: str) -> None:
    """Fill missing build detail from per-task snapshot (Testing/Close/Done/idle)."""
    if not task_id:
        return
    snapshots = load_state().get("build_snapshots_by_task") or {}
    snap = snapshots.get(task_id)
    if not snap:
        return
    for key in BUILD_DETAIL_KEYS:
        if not pipeline.get(key) and snap.get(key) not in (None, "", []):
            pipeline[key] = snap[key]


def set_pipeline_status(
    phase: str,
    task_id: str = "",
    task_title: str = "",
    active_agent: str = "",
    message: str = "",
) -> None:
    """Track sprint pipeline phase for UI telemetry (pickup → build → test → close → git)."""
    state = load_state()
    prev = state.get("pipeline") or {}
    pipeline = {
        "phase": phase,
        "task_id": task_id,
        "task_title": task_title,
        "active_agent": active_agent,
        "message": message,
        "progress_pct": PHASE_PROGRESS.get(phase, 0),
        "updated_at": datetime.now().isoformat(),
        "completed_steps": [] if phase == "idle" and not task_id else prev.get("completed_steps", []),
    }
    _carry_build_fields(pipeline, prev, task_id, phase)
    state["pipeline"] = pipeline
    if phase == "testing" and prev.get("test_started_at"):
        state["pipeline"]["test_started_at"] = prev["test_started_at"]
        state["pipeline"]["test_subphase"] = prev.get("test_subphase", "starting")
    elif phase != "testing":
        state["pipeline"].pop("test_started_at", None)
        state["pipeline"].pop("test_subphase", None)
    if phase == "idle" and not task_id:
        for key in ("build_outcome", "build_duration_seconds", "build_files_modified",
                    "build_started_at", "build_subphase", "build_intents", "build_functionality",
                    "build_usage_guide", "build_detail_updated_at"):
            state["pipeline"].pop(key, None)
    save_state(state)
    if task_id:
        if phase not in ("idle",):
            _persist_build_snapshot(task_id, state["pipeline"])
        update_queue_progress(task_id, phase, active_agent, message)


def mark_pipeline_step_complete(step: str) -> None:
    """Record a gated pipeline step as successfully completed (Task 37 step gates)."""
    state = load_state()
    pipeline = state.get("pipeline") or {}
    steps = list(pipeline.get("completed_steps") or [])
    if step not in steps:
        steps.append(step)
    pipeline["completed_steps"] = steps
    state["pipeline"] = pipeline
    save_state(state)


def reset_pipeline_steps(task_id: str = "", task_title: str = "") -> None:
    """Clear completed step markers when a new pickup cycle starts."""
    state = load_state()
    pipeline = state.get("pipeline") or {}
    prev_task = pipeline.get("task_id")
    pipeline["completed_steps"] = []
    # Only wipe build detail when picking up a different task (retries keep last build info).
    if task_id and prev_task and task_id != prev_task:
        for key in (*BUILD_DETAIL_KEYS, *BUILD_PROGRESS_KEYS):
            pipeline.pop(key, None)
    if task_id:
        pipeline["task_id"] = task_id
    if task_title:
        pipeline["task_title"] = task_title
    state["pipeline"] = pipeline
    save_state(state)


def rewind_pipeline_to_step(keep_through: str = "pickup") -> None:
    """Remove completed steps after a gate failure (e.g. test fail → rewind to pickup only)."""
    order = ["pickup", "building", "testing", "closing", "git_push", "done"]
    if keep_through not in order:
        return
    keep_idx = order.index(keep_through)
    state = load_state()
    pipeline = state.get("pipeline") or {}
    steps = pipeline.get("completed_steps") or []
    pipeline["completed_steps"] = [s for s in steps if s in order[: keep_idx + 1]]
    state["pipeline"] = pipeline
    save_state(state)


def get_pipeline_status() -> dict:
    state = load_state()
    pipeline = dict(state.get("pipeline") or {
        "phase": "idle",
        "task_id": "",
        "task_title": "",
        "active_agent": "",
        "message": "No active sprint task",
        "updated_at": None,
    })
    tid = pipeline.get("task_id")
    if tid:
        _merge_build_snapshot(pipeline, tid)
    return pipeline


def get_build_snapshot(task_id: str) -> dict:
    """Build detail for a task (popup + delivery notice)."""
    if not task_id:
        return {}
    snapshots = load_state().get("build_snapshots_by_task") or {}
    return dict(snapshots.get(task_id) or {})


TEST_SUBPHASE_PROGRESS = {
    "starting": 65,
    "sprint_cases": 67,
    "unit": 70,
    "browser": 78,
    "excel": 83,
    "done": 84,
}

BUILD_SUBPHASE_PROGRESS = {
    "starting": 18,
    "classifying": 22,
    "spec_load": 26,
    "patching": 32,
    "unit_verify": 38,
    "done": 40,
}


def update_build_progress(
    subphase: str,
    message: str,
    task_id: str = "",
    task_title: str = "",
    files_modified: list | None = None,
    build_outcome: str = "",
    intents: list | None = None,
    already_applied: bool = False,
) -> None:
    """Heartbeat during Build — UI shows sub-phase, elapsed time, files touched."""
    state = load_state()
    pipeline = dict(state.get("pipeline") or {})
    if not pipeline.get("build_started_at"):
        pipeline["build_started_at"] = datetime.now().isoformat()
    pipeline["phase"] = "building"
    pipeline["build_subphase"] = subphase
    pipeline["active_agent"] = "builder"
    pipeline["message"] = message
    pipeline["progress_pct"] = BUILD_SUBPHASE_PROGRESS.get(subphase, PHASE_PROGRESS["building"])
    pipeline["updated_at"] = datetime.now().isoformat()
    if files_modified is not None:
        pipeline["build_files_modified"] = files_modified
    if build_outcome:
        pipeline["build_outcome"] = build_outcome
    if intents is not None:
        pipeline["build_intents"] = list(intents)
    intent_list = pipeline.get("build_intents") or intents or []
    real_files = pipeline.get("build_files_modified") or []
    if intent_list and subphase in ("classifying", "spec_load", "patching", "unit_verify", "done"):
        pipeline["build_functionality"] = _build_functionality_lines(
            intent_list, real_files, already_applied,
        )
        pipeline["build_usage_guide"] = _build_usage_guide(
            intent_list, real_files, task_title or pipeline.get("task_title", ""), already_applied,
        )
    if task_id:
        pipeline["task_id"] = task_id
    if task_title:
        pipeline["task_title"] = task_title
    state["pipeline"] = pipeline
    save_state(state)
    tid = pipeline.get("task_id") or task_id
    if tid:
        _persist_build_snapshot(tid, pipeline)
        update_queue_progress(tid, "building", "builder", message)


def clear_build_progress() -> None:
    """Clear in-progress build heartbeat; keep build result for UI detail popup."""
    state = load_state()
    pipeline = dict(state.get("pipeline") or {})
    for key in ("build_subphase", "build_started_at"):
        pipeline.pop(key, None)
    state["pipeline"] = pipeline
    save_state(state)


BUILD_INTENT_LABELS = {
    "DATA_ANALYTICS_ML": "Data Analytics — CSV/Excel upload, quick train, dashboard panel",
    "NAVBAR_AND_SIDEBAR_NAVIGATION": "Navbar & sidebar navigation links and layout",
    "MULTI_TARGET_DATABASE_ARCHITECTURE": "Warehouse / multi-DB analytics wiring",
    "HIDE_UI_CONTENT": "Hide or remove dashboard widgets per task spec",
    "REMOVE_UNWANTED_CONTENT": "Remove unwanted UI sections from dashboard",
    "HIDE_ITEMS_FROM_UI": "Hide specific UI items from dashboard",
    "BROWSER_HEADER_TITLE": "Browser tab title (index.html)",
    "SPRINT_AGENT_FIX": "Agent pipeline / import path fixes",
    "AI_COPILOT": "AI Data Copilot search and NL filters",
    "WAREHOUSE_TABLE": "Warehouse sales table and filters",
    "KPI_CARDS": "Executive KPI summary cards",
    "CHARTS": "Bar / scatter chart components",
    "ADDITIONAL_FEATURES": "Additional dashboard features panel (AddAditionalFeatures)",
}

# Where + how users find agent-delivered functionality (Task 44).
BUILD_USAGE_GUIDES = {
    "DATA_ANALYTICS_ML": {
        "headline": "Data Analytics — upload CSV/Excel and train a quick ML model",
        "where": "Dashboard (main page) — scroll to the Data Analytics panel",
        "route": "/",
        "route_label": "Open Dashboard",
        "steps": [
            "Go to Dashboard (home page)",
            "Find the “Data Analytics” card below the anomaly alerts",
            "Upload a CSV or Excel file, then click Train to run the model",
        ],
    },
    "ADDITIONAL_FEATURES": {
        "headline": "Additional Features panel added to the dashboard",
        "where": "Dashboard — “Add Aditional Features” card with status metrics",
        "route": "/",
        "route_label": "Open Dashboard",
        "steps": [
            "Open the main Dashboard",
            "Scroll to the “Add Aditional Features” section",
            "Review the new metrics/status widgets added by the agent",
        ],
    },
    "NAVBAR_AND_SIDEBAR_NAVIGATION": {
        "headline": "Navigation bar and sidebar links updated",
        "where": "Left sidebar + top quick nav on every page",
        "route": "/",
        "route_label": "Open Dashboard",
        "steps": [
            "Use the left sidebar to switch pages (Dashboard, Analytics, Sprint Board, Agents)",
            "Try the Quick Nav bar at the top of each page",
        ],
    },
    "AI_COPILOT_DATE_AGNOSTIC_QUERY": {
        "headline": "AI Data Copilot — natural-language warehouse search",
        "where": "Dashboard — AI Data Copilot panel",
        "route": "/",
        "route_label": "Open Dashboard",
        "steps": [
            "Open Dashboard",
            "Type a question in the AI Data Copilot box (no date required)",
            "Submit — filters apply to charts and the data table",
        ],
    },
    "SPRINT_BOARD_STYLING_AND_DROPDOWNS": {
        "headline": "Sprint Board styling and workspace dropdowns",
        "where": "Sprint Board page",
        "route": "/sprints",
        "route_label": "Open Sprint Board",
        "steps": [
            "Open Sprint Board from the sidebar",
            "Use workspace/project dropdowns to filter Plane tasks",
            "Watch the live agent pipeline while tasks run",
        ],
    },
    "BROWSER_HEADER_TITLE": {
        "headline": "Browser tab title updated",
        "where": "Browser tab — visible on all pages",
        "route": "/",
        "route_label": "Open Dashboard",
        "steps": ["Refresh any page — the browser tab title reflects the new name"],
    },
    "HIDE_UI_CONTENT": {
        "headline": "Unwanted dashboard widgets hidden",
        "where": "Dashboard — removed sections no longer appear",
        "route": "/",
        "route_label": "Open Dashboard",
        "steps": ["Open Dashboard — previously hidden widgets should be gone"],
    },
    "REMOVE_UNWANTED_CONTENT": {
        "headline": "Unwanted content removed from the UI",
        "where": "Dashboard and related pages",
        "route": "/",
        "route_label": "Open Dashboard",
        "steps": ["Browse Dashboard — removed panels should no longer show"],
    },
}


def _infer_route_from_files(files_modified: list) -> dict:
    """Guess primary UI route from changed file paths."""
    joined = " ".join(files_modified or []).lower()
    if "sprintboard" in joined or "sprint" in joined and "pages" in joined:
        return {"route": "/sprints", "route_label": "Open Sprint Board", "where": "Sprint Board page"}
    if "agentmonitor" in joined or "/agents" in joined:
        return {"route": "/agents", "route_label": "Open Agent Monitor", "where": "Agent Monitor page"}
    if "analytics.jsx" in joined or "analytics/" in joined:
        return {"route": "/analytics", "route_label": "Open Analytics", "where": "Analytics page"}
    if "mcp" in joined:
        return {"route": "/mcp", "route_label": "Open MCP Explorer", "where": "MCP Explorer page"}
    if "dashboard.jsx" in joined or "components/" in joined:
        return {"route": "/", "route_label": "Open Dashboard", "where": "Main Dashboard (home page)"}
    return {"route": "/", "route_label": "Open Dashboard", "where": "Main Dashboard"}


def _build_usage_guide(
    intents: list,
    files_modified: list,
    task_title: str,
    already_applied: bool,
) -> dict:
    """User-facing delivery notice — where to find and how to use agent-built features."""
    primary_intent = next((i for i in (intents or []) if i in BUILD_USAGE_GUIDES), None)
    base = dict(BUILD_USAGE_GUIDES.get(primary_intent) or {})
    route_hint = _infer_route_from_files(files_modified)

    if not base:
        comp_files = [f for f in (files_modified or []) if f.endswith(".jsx") and "components/" in f.replace("\\", "/")]
        comp_name = comp_files[0].split("/")[-1].replace(".jsx", "") if comp_files else ""
        base = {
            "headline": task_title or "New functionality delivered by the agent",
            "where": route_hint.get("where", "Main Dashboard"),
            "route": route_hint.get("route", "/"),
            "route_label": route_hint.get("route_label", "Open Dashboard"),
            "steps": [
                f"Open {route_hint.get('route_label', 'Dashboard').replace('Open ', '')}",
            ],
        }
        if comp_name:
            base["headline"] = f"{task_title} — {comp_name} component added"
            base["steps"].append(f"Look for the “{comp_name}” panel on the page")
        base["steps"].append("Changes were applied automatically — no manual coding needed")

    guide = {
        "headline": base.get("headline", task_title),
        "where": base.get("where", route_hint.get("where", "Dashboard")),
        "route": base.get("route", route_hint.get("route", "/")),
        "route_label": base.get("route_label", route_hint.get("route_label", "Open Dashboard")),
        "steps": list(base.get("steps") or []),
        "task_title": task_title,
        "verify_only": already_applied,
    }
    if already_applied:
        guide["headline"] = f"{guide['headline']} (already in codebase — verified)"
        guide["steps"].insert(0, "No new UI needed — existing code already matched your task")
    return guide


def format_delivery_comment(guide: dict) -> str:
    """Plain-text delivery notice for Plane task comments."""
    if not guide:
        return ""
    lines = [
        "📦 **What the agent delivered**",
        f"**{guide.get('headline', 'Feature delivered')}**",
        "",
        f"📍 **Where:** {guide.get('where', 'Dashboard')}",
        f"🔗 **Open:** {guide.get('route_label', 'Dashboard')} → `{guide.get('route', '/')}`",
        "",
        "**How to use:**",
    ]
    for i, step in enumerate(guide.get("steps") or [], 1):
        lines.append(f"{i}. {step}")
    lines.append("")
    lines.append("🤖 Built autonomously — no manual coding required.")
    return "\n".join(lines)


def _build_functionality_lines(intents: list, files_modified: list, already_applied: bool) -> list[str]:
    """Human-readable functionality summary for Build detail popup."""
    lines = []
    for intent in intents or []:
        label = BUILD_INTENT_LABELS.get(intent)
        if label:
            lines.append(label)
        elif intent and not intent.startswith("_"):
            lines.append(intent.replace("_", " ").title())
    if not lines and files_modified:
        lines.append(f"Code updates in {len(files_modified)} file(s)")
    if already_applied and not files_modified:
        lines.append("Requirements already satisfied in codebase — verify-only (no new files)")
    elif already_applied:
        lines.append("Partial verify-only — some requirements were already implemented")
    if not lines:
        lines.append("Builder ran — see changed files below")
    return lines


def record_build_result(
    task_id: str,
    task_title: str,
    files_modified: list,
    already_applied: bool,
    duration_seconds: float,
    intents: list | None = None,
) -> None:
    """Persist build outcome so UI distinguishes real code changes vs verify-only."""
    state = load_state()
    pipeline = dict(state.get("pipeline") or {})
    real_files = [f for f in (files_modified or []) if f != "already_applied"]
    outcome = "verify_only" if already_applied or not real_files else "code_changed"
    pipeline["build_outcome"] = outcome
    pipeline["build_files_modified"] = real_files
    pipeline["build_duration_seconds"] = round(duration_seconds, 1)
    pipeline["build_intents"] = list(intents or [])
    pipeline["build_functionality"] = _build_functionality_lines(intents or [], real_files, already_applied)
    pipeline["build_usage_guide"] = _build_usage_guide(intents or [], real_files, task_title, already_applied)
    pipeline["build_detail_updated_at"] = datetime.now().isoformat()
    pipeline["updated_at"] = datetime.now().isoformat()
    state["pipeline"] = pipeline
    save_state(state)
    if task_id:
        _persist_build_snapshot(task_id, pipeline)
    log_task_result(
        task_id or "BUILD",
        task_title or "Build gate",
        "builder",
        "completed",
        f"outcome={outcome} files={len(real_files)} duration={duration_seconds:.1f}s",
        duration_seconds,
    )


def update_test_progress(
    subphase: str,
    message: str,
    task_id: str = "",
    task_title: str = "",
) -> None:
    """Heartbeat during long Test runs — UI shows sub-phase + elapsed time."""
    state = load_state()
    pipeline = dict(state.get("pipeline") or {})
    if not pipeline.get("test_started_at"):
        pipeline["test_started_at"] = datetime.now().isoformat()
    pipeline["phase"] = "testing"
    pipeline["test_subphase"] = subphase
    pipeline["active_agent"] = "tester"
    pipeline["message"] = message
    pipeline["progress_pct"] = TEST_SUBPHASE_PROGRESS.get(subphase, PHASE_PROGRESS["testing"])
    pipeline["updated_at"] = datetime.now().isoformat()
    if task_id:
        pipeline["task_id"] = task_id
    if task_title:
        pipeline["task_title"] = task_title
    state["pipeline"] = pipeline
    save_state(state)
    tid = pipeline.get("task_id") or task_id
    if tid:
        _persist_build_snapshot(tid, pipeline)
        update_queue_progress(tid, "testing", "tester", message)


def clear_test_progress() -> None:
    """Clear test heartbeat fields when Test gate finishes."""
    state = load_state()
    pipeline = dict(state.get("pipeline") or {})
    pipeline.pop("test_subphase", None)
    pipeline.pop("test_started_at", None)
    state["pipeline"] = pipeline
    save_state(state)


def _empty_task_queue() -> dict:
    return {
        "pending": [],
        "active": None,
        "completed": [],
        "failed": [],
        "updated_at": None,
    }


def get_task_queue() -> dict:
    state = load_state()
    return state.get("task_queue") or _empty_task_queue()


def _save_task_queue(queue: dict) -> None:
    state = load_state()
    queue["updated_at"] = datetime.now().isoformat()
    state["task_queue"] = queue
    save_state(state)


def sync_pending_tasks(actionable_tasks: list) -> None:
    """Merge Plane pickupable tasks into the pending queue (deduped, priority-sorted)."""
    queue = get_task_queue()
    active_id = (queue.get("active") or {}).get("id")
    done_ids = {t.get("id") for t in queue.get("completed", []) if t.get("id")}
    failed_ids = {t.get("id") for t in queue.get("failed", []) if t.get("id")}
    pending_ids = {t.get("id") for t in queue.get("pending", []) if t.get("id")}

    priority_weights = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
    new_pending = []
    for task in actionable_tasks:
        tid = task.get("id")
        if not tid or tid == active_id or tid in done_ids:
            continue
        if tid in pending_ids:
            existing = next((p for p in queue["pending"] if p.get("id") == tid), None)
            if existing:
                new_pending.append(existing)
            continue
        new_pending.append({
            "id": tid,
            "title": task.get("name", "Untitled"),
            "priority": (task.get("priority") or "medium").lower(),
            "project_name": task.get("project_name", ""),
            "queued_at": datetime.now().isoformat(),
        })

    new_pending.sort(
        key=lambda t: priority_weights.get(t.get("priority", "medium"), 2),
        reverse=True,
    )
    queue["pending"] = new_pending
    _save_task_queue(queue)


def set_queue_active(task_id: str, task_title: str, project_name: str = "", priority: str = "medium") -> None:
    queue = get_task_queue()
    queue["pending"] = [t for t in queue.get("pending", []) if t.get("id") != task_id]
    queue["active"] = {
        "id": task_id,
        "title": task_title,
        "project_name": project_name,
        "priority": priority,
        "phase": "pickup",
        "progress_pct": PHASE_PROGRESS["pickup"],
        "active_agent": "sprint_watcher",
        "message": "Task picked up from Plane",
        "started_at": datetime.now().isoformat(),
    }
    _save_task_queue(queue)


def update_queue_progress(
    task_id: str,
    phase: str,
    active_agent: str = "",
    message: str = "",
) -> None:
    queue = get_task_queue()
    active = queue.get("active") or {}
    if active.get("id") != task_id:
        return
    active["phase"] = phase
    active["progress_pct"] = PHASE_PROGRESS.get(phase, active.get("progress_pct", 0))
    active["active_agent"] = active_agent
    active["message"] = message
    active["updated_at"] = datetime.now().isoformat()
    queue["active"] = active
    _save_task_queue(queue)


def complete_queue_task(task_id: str, task_title: str, duration_seconds: float = 0) -> None:
    queue = get_task_queue()
    pipeline = load_state().get("pipeline") or {}
    delivery = None
    if pipeline.get("task_id") == task_id and pipeline.get("build_usage_guide"):
        delivery = pipeline["build_usage_guide"]
    if not delivery:
        snap = get_build_snapshot(task_id)
        delivery = snap.get("build_usage_guide")
    entry = {
        "id": task_id,
        "title": task_title,
        "completed_at": datetime.now().isoformat(),
        "duration_seconds": duration_seconds,
        "progress_pct": 100,
    }
    if delivery:
        entry["delivery_guide"] = delivery
    queue["completed"] = ([entry] + [t for t in queue.get("completed", []) if t.get("id") != task_id])[:30]
    queue["pending"] = [t for t in queue.get("pending", []) if t.get("id") != task_id]
    if (queue.get("active") or {}).get("id") == task_id:
        queue["active"] = None
    queue["failed"] = [t for t in queue.get("failed", []) if t.get("id") != task_id]
    _save_task_queue(queue)


def fail_queue_task(task_id: str, task_title: str, reason: str = "", attempts: int = 0, max_attempts: int = 0) -> None:
    queue = get_task_queue()
    entry = {
        "id": task_id,
        "title": task_title,
        "failed_at": datetime.now().isoformat(),
        "reason": reason[:300],
        "progress_pct": 0,
        "phase": "failed",
        "attempts": attempts,
        "max_attempts": max_attempts,
    }
    queue["failed"] = ([entry] + [t for t in queue.get("failed", []) if t.get("id") != task_id])[:20]
    queue["pending"] = [t for t in queue.get("pending", []) if t.get("id") != task_id]
    if (queue.get("active") or {}).get("id") == task_id:
        queue["active"] = None
    _save_task_queue(queue)


def get_queue_status_for_task(task_id: str):
    queue = get_task_queue()
    if (queue.get("active") or {}).get("id") == task_id:
        return {**queue["active"], "queue_status": "active"}
    for t in queue.get("pending", []):
        if t.get("id") == task_id:
            return {**t, "queue_status": "pending", "progress_pct": 0, "phase": "queued"}
    for t in queue.get("completed", []):
        if t.get("id") == task_id:
            return {**t, "queue_status": "completed", "phase": "done", "progress_pct": 100}
    for t in queue.get("failed", []):
        if t.get("id") == task_id:
            return {**t, "queue_status": "failed", "phase": "failed"}
    return None


def is_agent_working() -> bool:
    """Returns True if a builder/tester agent is currently running code changes."""
    state = load_state()
    if not state.get("agent_working", False):
        return False
    # Safety valve: if agent_working has been True for > 30 minutes, auto-clear it
    # (guards against crashes that leave the flag stuck True forever)
    since_str = state.get("agent_working_since") or ""
    if since_str:
        try:
            since = datetime.fromisoformat(since_str)
            if (datetime.now() - since).total_seconds() > 1800:  # 30 min
                console.print("[yellow]⚠️ agent_working flag stuck for >30min — auto-clearing.[/yellow]")
                set_agent_working(False)
                return False
        except Exception:
            pass
    return True


def _scan_agent_pids() -> dict:
    """Scan running agent processes (cached briefly — psutil is slow on Windows)."""
    now = time.time()
    if now - _PID_CACHE["at"] < _PID_CACHE_TTL:
        return _PID_CACHE["pids"]

    agent_pids = {}
    try:
        for proc in psutil.process_iter(["pid", "cmdline"]):
            try:
                cmd = " ".join(proc.info.get("cmdline") or []).lower()
                if "sprint_watcher_agent" in cmd:
                    agent_pids["sprint_watcher"] = proc.info["pid"]
                elif "builder_agent" in cmd:
                    agent_pids["builder"] = proc.info["pid"]
                elif "tester_agent" in cmd:
                    agent_pids["tester"] = proc.info["pid"]
                elif "git_agent" in cmd or "agents.git_agent" in cmd:
                    agent_pids["git_agent"] = proc.info["pid"]
                elif "memory_manager" in cmd:
                    agent_pids["memory"] = proc.info["pid"]
                elif "orchestrator_agent" in cmd:
                    agent_pids["orchestrator"] = proc.info["pid"]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception:
        pass

    _PID_CACHE["at"] = now
    _PID_CACHE["pids"] = agent_pids
    return agent_pids


def _fleet_is_online(agent_pids: dict) -> bool:
    """True when sprint watcher or orchestrator process is alive (fleet supervisor up)."""
    return bool(agent_pids.get("sprint_watcher") or agent_pids.get("orchestrator"))


def get_dynamic_agent_statuses() -> dict:
    state = load_state()
    agent_pids = _scan_agent_pids()
    agents_meta = state.get("agents", {})
    fleet_online = _fleet_is_online(agent_pids)
    listening_agents = {"orchestrator", "builder", "tester", "git_agent", "memory"}
    statuses = {}
    for name in ["sprint_watcher", "orchestrator", "builder", "tester", "git_agent", "memory"]:
        meta = agents_meta.get(name, {})
        pid = agent_pids.get(name)
        is_active = pid is not None
        if is_active:
            status = "running"
        elif fleet_online and name in listening_agents:
            # Idle-but-listening agents count as online when the fleet supervisor is up
            status = "running"
        else:
            status = meta.get("status", "idle")
            if status == "running":
                status = "idle"
        statuses[name] = {
            "name": name.replace("_", " ").title(),
            "status": status,
            "current_task": meta.get("current_task", "Monitoring"),
            "last_updated": meta.get("last_updated"),
            "pid": pid
        }
    return statuses


def log_task_result(task_id: str, task_title: str, agent_name: str, status: str, output: str = "", duration_seconds: float = 0.0):
    _ensure_dirs()
    today = datetime.now().strftime("%Y-%m-%d")
    history_file = TASK_HISTORY_DIR / f"{today}_task_history.jsonl"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "task_id": task_id,
        "task_title": task_title,
        "agent": agent_name,
        "status": status,
        "duration_seconds": duration_seconds,
        "output_summary": output[:500] if output else ""
    }
    try:
        with history_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        console.print(f"[yellow]⚠️ Failed to log task result: {e}[/yellow]")


def load_task_history_for_date(date_str: str = "") -> list[dict]:
    """Load task history entries for a given YYYY-MM-DD (default: today)."""
    _ensure_dirs()
    day = date_str or datetime.now().strftime("%Y-%m-%d")
    history_file = TASK_HISTORY_DIR / f"{day}_task_history.jsonl"
    if not history_file.exists():
        return []
    entries = []
    try:
        with history_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entries.append(json.loads(line.strip()))
                    except Exception:
                        pass
    except Exception:
        pass
    return entries


def get_previous_day_context() -> dict:
    """
    Task 40 — Summary of yesterday's activity for agent session startup.
    Agents call this at the start of a new day/session before picking Plane tasks.
    """
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")
    y_entries = load_task_history_for_date(yesterday)
    t_entries = load_task_history_for_date(today)
    state = load_state()

    completed = [e for e in y_entries if e.get("status") == "completed"]
    failed = [e for e in y_entries if e.get("status") == "failed"]
    titles_done = list({e.get("task_title") for e in completed if e.get("task_title")})

    return {
        "recall_date": yesterday,
        "today": today,
        "yesterday_task_count": len(y_entries),
        "yesterday_completed": titles_done[:20],
        "yesterday_failed_count": len(failed),
        "yesterday_failed_titles": [e.get("task_title") for e in failed[:10]],
        "today_task_count_so_far": len(t_entries),
        "last_pipeline_phase": (state.get("pipeline") or {}).get("phase", "idle"),
        "last_conversation_update": state.get("last_conversation_update"),
        "queue_completed_recent": (state.get("task_queue") or {}).get("completed", [])[:5],
        "summary": (
            f"Previous day {yesterday}: {len(completed)} completed, {len(failed)} failed. "
            f"Pipeline now {(state.get('pipeline') or {}).get('phase', 'idle')}."
        ),
    }


def update_conversation_memory(agent_name: str = "assistant", user_query: str = "", response_summary: str = ""):
    _ensure_dirs()
    now = datetime.now()
    conv_file = CONVERSATIONS_DIR / f"{agent_name}_conversation.jsonl"
    entry = {
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "user_query": user_query[:500],
        "response_summary": response_summary[:1000]
    }
    try:
        with conv_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

    state = load_state()
    state["last_conversation_update"] = now.isoformat()
    save_state(state)


if __name__ == "__main__":
    import argparse
    import time as _time

    parser = argparse.ArgumentParser(description="Memory Manager")
    parser.add_argument("--daemon", action="store_true", help="Run continuous state persistence loop")
    args = parser.parse_args()

    if args.daemon:
        console.print("[green]Memory Agent daemon started[/green]")
        while True:
            update_agent_status("memory", "running", "State persistence active")
            _time.sleep(30)
    else:
        console.print(f"Memory Manager status: {load_state()}")
        cleanup_old_memory(CONVERSATIONS_DIR, TASK_HISTORY_DIR)
