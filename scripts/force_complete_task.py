"""One-off: force-complete a sprint task and reset pipeline (user-requested cleanup)."""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agents"))

from memory_manager import load_state, save_state, set_agent_working, complete_queue_task, update_agent_status
from plane_agent import list_projects, get_single_task, update_task_status, add_comment

TASK_ID = "b1ce165d-5d17-4281-9566-b4fedd7644e5"
TASK_TITLE = "Add Aditional Features"
WS = "agentbuilder"


def main() -> None:
    set_agent_working(False)
    for agent in ("builder", "tester", "sprint_watcher", "git_agent", "orchestrator"):
        update_agent_status(agent, "idle", "Idle")

    state = load_state()
    state["pipeline"] = {
        "phase": "idle",
        "task_id": "",
        "task_title": "",
        "active_agent": "",
        "message": "Manually force-completed — Additional Features removed per user request",
        "progress_pct": 0,
        "updated_at": datetime.now().isoformat(),
        "completed_steps": [],
    }
    snap = state.get("build_snapshots_by_task") or {}
    snap.pop(TASK_ID, None)
    state["build_snapshots_by_task"] = snap
    save_state(state)
    complete_queue_task(TASK_ID, TASK_TITLE, duration_seconds=0)

    proc_file = ROOT / "memory" / ".processed_task_ids.json"
    proc = json.loads(proc_file.read_text(encoding="utf-8"))
    entries = proc.get("entries", [])
    if not any(e.get("id") == TASK_ID for e in entries):
        entries.append({"id": TASK_ID, "at": datetime.now().isoformat()})
    proc["entries"] = entries
    proc_file.write_text(json.dumps(proc, indent=2), encoding="utf-8")

    plane_ok = False
    plane_msg = "task not found in any project"
    try:
        for p in list_projects(WS):
            pid = p.get("id")
            if not pid or not get_single_task(pid, TASK_ID, WS):
                continue
            result = update_task_status(pid, TASK_ID, "completed", WS)
            if result:
                add_comment(
                    pid,
                    TASK_ID,
                    "Force-completed by user: Additional Features task cancelled; placeholder panel removed from Dashboard.",
                    WS,
                )
                plane_ok = True
                plane_msg = f"closed in project {p.get('name', pid)}"
                break
    except Exception as exc:
        plane_msg = str(exc)

    reg_file = ROOT / "memory" / "sprint_test_registry.json"
    if reg_file.exists():
        reg = json.loads(reg_file.read_text(encoding="utf-8"))
        if reg.get("active_task_id") == TASK_ID:
            reg["active_task_id"] = None
        active = reg.get("active_task_ids") or []
        if TASK_ID in active:
            reg["active_task_ids"] = [t for t in active if t != TASK_ID]
        reg_file.write_text(json.dumps(reg, indent=2), encoding="utf-8")

    print("Pipeline reset to idle")
    print(f"Task queue completed: {TASK_ID}")
    print(f"Plane: {plane_ok} — {plane_msg}")


if __name__ == "__main__":
    main()
