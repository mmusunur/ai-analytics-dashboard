r"""
Diagnostic script — tests Plane API connectivity, project listing, task states,
backend import chain, and agent state. Run with:
    .venv\Scripts\python scripts\diagnose.py
"""
import sys, os, json, traceback
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "agents"))
sys.path.insert(0, str(ROOT / "scripts"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import httpx

TOKEN  = os.getenv("PLANE_API_TOKEN", "")
WS     = os.getenv("PLANE_WORKSPACE_SLUG", "agentbuilder")
BASE   = "https://api.plane.so/api/v1"
HEADERS = {"X-API-Key": TOKEN, "Content-Type": "application/json"}

print("=" * 60)
print("PLANE API DIAGNOSTICS")
print("=" * 60)
print(f"Token  : {TOKEN[:20]}..." if TOKEN else "Token  : NOT SET")
print(f"WS slug: {WS}")
print()

def get(url, label):
    try:
        r = httpx.get(url, headers=HEADERS, timeout=12)
        print(f"[{r.status_code}] {label}")
        if r.status_code == 200:
            return r.json()
        print(f"     Body: {r.text[:300]}")
    except Exception as e:
        print(f"[ERR] {label}: {e}")
    return None

# 1. workspaces listing
get(f"{BASE}/workspaces/", "GET /workspaces/  (list all)")

# 2. projects in workspace
data = get(f"{BASE}/workspaces/{WS}/projects/", f"GET /workspaces/{WS}/projects/")
projects = (data or {}).get("results", []) if isinstance(data, dict) else (data or [])
print(f"\n  Projects found: {len(projects)}")
for p in projects:
    print(f"    - [{p.get('identifier')}] {p.get('name')} | id={p.get('id')}")

# 3. issues for each project
print()
all_actionable = []
for p in projects:
    pid   = p.get("id")
    pname = p.get("name")
    d2 = get(f"{BASE}/workspaces/{WS}/projects/{pid}/issues/", f"GET issues for '{pname}'")
    issues = (d2 or {}).get("results", []) if isinstance(d2, dict) else []
    print(f"    {len(issues)} issues total")
    for i in issues:
        sg = (i.get("state_detail") or {}).get("group", i.get("state_group", "?"))
        print(f"      [{sg:12}] {i.get('name','?')[:55]}  id={str(i.get('id','?'))[:8]}")
        if sg in ("unstarted", "todo", "triaged", "backlog"):
            all_actionable.append({"project": pname, "pid": pid, "id": i.get("id"), "name": i.get("name"), "group": sg})

print()
print("=" * 60)
print(f"ACTIONABLE tasks (watcher pickup candidates): {len(all_actionable)}")
for t in all_actionable:
    print(f"  [{t['group']}] {t['name'][:55]}  (proj={t['project']}, id={str(t['id'])[:8]})")

# 4. processed task IDs on disk
print()
print("=" * 60)
print("PROCESSED TASK IDs (memory/.processed_task_ids.json):")
pfile = ROOT / "memory" / ".processed_task_ids.json"
if pfile.exists():
    d = json.loads(pfile.read_text("utf-8"))
    entries = d.get("entries", [])
    print(f"  {len(entries)} entries:")
    for e in entries:
        print(f"    {e}")
else:
    print("  File does not exist.")

# 5. agent_state.json
print()
print("=" * 60)
print("AGENT STATE (memory/agent_state.json):")
sf = ROOT / "memory" / "agent_state.json"
if sf.exists():
    s = json.loads(sf.read_text("utf-8"))
    print(f"  plane_project_id   : {s.get('plane_project_id')}")
    print(f"  plane_workspace_slug: {s.get('plane_workspace_slug')}")
    print(f"  agent_working      : {s.get('agent_working')}")
    print(f"  pipeline.phase     : {(s.get('pipeline') or {}).get('phase')}")
    for name, info in (s.get("agents") or {}).items():
        print(f"  agent[{name}]: status={info.get('status')} task={info.get('current_task')}")
else:
    print("  Not found.")

# 6. Backend import chain
print()
print("=" * 60)
print("BACKEND IMPORT CHAIN:")
for mod in ["memory_manager", "plane_agent", "sprint_watcher_agent"]:
    try:
        __import__(mod)
        print(f"  [OK ] {mod}")
    except Exception as e:
        print(f"  [ERR] {mod}: {e}")
        traceback.print_exc()

# 7. fleet_health / server_health
print()
print("=" * 60)
print("FLEET / SERVER STATUS:")
try:
    from fleet_health import fleet_snapshot
    snap = fleet_snapshot()
    for name, running in snap.items():
        status = "RUNNING" if running else "STOPPED"
        print(f"  [{status:7}] {name}")
except Exception as e:
    print(f"  fleet_health error: {e}")

try:
    from server_health import servers_healthy
    h = servers_healthy()
    print(f"  backend :8000 = {'UP' if h['backend'] else 'DOWN'}")
    print(f"  frontend:5173 = {'UP' if h['frontend'] else 'DOWN'}")
except Exception as e:
    print(f"  server_health error: {e}")

print()
print("=" * 60)
print("DIAGNOSIS COMPLETE")
