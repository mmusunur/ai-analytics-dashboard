r"""
Reset script: clears the processed-task-ID cache and moves any 'started'
tasks that should be re-picked back to 'unstarted' in Plane.

Run once to unblock stuck agents:
    .venv\Scripts\python scripts\reset_stuck_tasks.py
"""
import sys, os, json
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "agents"))
sys.path.insert(0, str(ROOT / "scripts"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# ── Step 1: Clear processed task IDs ─────────────────────────────────────────
pfile = ROOT / "memory" / ".processed_task_ids.json"
if pfile.exists():
    data = json.loads(pfile.read_text("utf-8"))
    count = len(data.get("entries", data.get("ids", [])))
    pfile.unlink()
    print(f"[reset] Cleared {count} processed task ID(s) from {pfile.name}")
else:
    print("[reset] No processed task IDs file found — already clean.")

# ── Step 2: Reset agent_state pipeline and agent statuses ────────────────────
sf = ROOT / "memory" / "agent_state.json"
if sf.exists():
    state = json.loads(sf.read_text("utf-8"))
    # Reset all agent statuses to idle
    for name in (state.get("agents") or {}):
        state["agents"][name]["status"] = "idle"
        state["agents"][name]["current_task"] = "Idle"
    # Reset pipeline
    state["agent_working"] = False
    state["agent_working_task"] = None
    state["agent_working_since"] = None
    state["pipeline"] = {
        "phase": "idle",
        "task_id": None,
        "task_title": None,
        "active_agent": None,
        "message": "Monitoring — waiting for next task",
        "progress_pct": 0,
        "updated_at": None,
        "completed_steps": []
    }
    sf.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print("[reset] Agent state reset to idle.")

# ── Step 3: Move stuck 'started' tasks back to 'unstarted' in Plane ──────────
import httpx

TOKEN   = os.getenv("PLANE_API_TOKEN", "")
WS      = os.getenv("PLANE_WORKSPACE_SLUG", "agentbuilder")
BASE    = "https://api.plane.so/api/v1"
HEADERS = {"X-API-Key": TOKEN, "Content-Type": "application/json"}

print(f"\n[reset] Scanning workspace '{WS}' for stuck 'started' tasks...")

# Get all projects
r = httpx.get(f"{BASE}/workspaces/{WS}/projects/", headers=HEADERS, timeout=12)
projects = r.json().get("results", []) if r.status_code == 200 else []
print(f"[reset] Found {len(projects)} project(s).")

reset_count = 0
for p in projects:
    pid   = p.get("id")
    pname = p.get("name", "?")

    # Get issues
    r2 = httpx.get(f"{BASE}/workspaces/{WS}/projects/{pid}/issues/", headers=HEADERS, timeout=12)
    if r2.status_code != 200:
        print(f"  [SKIP] {pname}: HTTP {r2.status_code}")
        continue
    issues = r2.json().get("results", [])

    # Get states for this project
    r3 = httpx.get(f"{BASE}/workspaces/{WS}/projects/{pid}/states/", headers=HEADERS, timeout=12)
    states = r3.json().get("results", []) if r3.status_code == 200 else []
    # Find 'unstarted' state id
    unstarted_state = next((s for s in states if s.get("group", "").lower() == "unstarted"), None)
    if not unstarted_state:
        print(f"  [WARN] {pname}: No 'unstarted' state found — skipping.")
        continue
    unstarted_id = unstarted_state["id"]

    for issue in issues:
        sg = (issue.get("state_detail") or {}).get("group", issue.get("state_group", ""))
        if sg in ("started", "in_progress"):
            tid   = issue.get("id")
            tname = issue.get("name", "?")
            print(f"  [RESET] {pname}: '{tname[:55]}' ({tid[:8]}) {sg} -> unstarted")
            patch_r = httpx.patch(
                f"{BASE}/workspaces/{WS}/projects/{pid}/issues/{tid}/",
                headers=HEADERS,
                json={"state": unstarted_id},
                timeout=12
            )
            if patch_r.status_code in (200, 201):
                print(f"    OK — task moved to unstarted.")
                reset_count += 1
            else:
                print(f"    FAILED: HTTP {patch_r.status_code} — {patch_r.text[:200]}")

print(f"\n[reset] Done. {reset_count} task(s) moved back to 'unstarted'.")
print("[reset] Restart the sprint watcher to pick them up automatically.")
