# Agent Pipeline & Live Status — User Guide

This guide explains how sprint tasks are picked up automatically and how to monitor agent activity in the UI.

---

## Will sprint tasks be picked up automatically?

**Yes.** When you add a task in Plane with status **To Do**, **Unstarted**, or **Triaged**, the Sprint Watcher agent will:

1. Detect it within 15–60 seconds (while `run_sprint_watcher.py` or `start_all_services.bat` is running)
2. Move it to **In Progress** on Plane
3. Run the Builder → Tester → Close → Git pipeline with **no user interaction**

Tasks in **Backlog** are not auto-picked. Stale **In Progress** tasks may be retried.

---

## Where to see live agent & task status

| Page | URL | Refresh rate |
|------|-----|----------------|
| **Agent Monitor** | `/agents` | Every **4 seconds** (pauses while agent modifies code) |
| **Sprint Monitor & Board** | `/sprints` | Tasks every **12 seconds**, agent pipeline every **4 seconds** |
| **Sidebar footer** | All pages | Every **4 seconds** |
| **Floating panel** | Dashboard & other pages | Every **4 seconds** |

Both monitor pages show **Last updated** timestamp, **countdown to next refresh**, and **Refresh Now** button.

---

## Pipeline phases

```
1. Pickup        → Sprint Watcher (reads Plane task)
2. Building      → Builder Agent (code changes)
3. Testing       → Tester Agent (68 unit + 46 browser + dynamic sprint tests)
4. Close Task    → Plane Agent (mark completed)
5. Git Push      → Git Agent (commit & push)
6. Done          → Watcher resumes monitoring
```

If tests fail, the task returns to **To Do** on Plane (never auto-cancelled).

---

## API endpoints (for integrations)

| Endpoint | Description |
|----------|-------------|
| `GET /api/agents/status` | All agents + `pipeline` object + `agent_working` flag |
| `GET /api/sprints/agent-working` | Lightweight working flag for frontend polling |
| `GET /api/sprints/tasks` | Sprint tasks + triggers background watcher |

Pipeline state is stored in `memory/agent_state.json` under `"pipeline"`.

---

## Starting the autonomous fleet

```bash
# Windows — starts backend, frontend, watcher, watchdog
scripts\start_all_services.bat

# Or individually
python scripts/run_sprint_watcher.py --interval 60
python scripts/agent_watchdog.py
```

Open **http://localhost:5173/agents** after launch to confirm agents are running.

---

## Documentation maintenance

When major features are added, agents must update:

- `README.md` (preserve LLM allocation table)
- `tasks/*.md` and `tasks.md`
- `docs/AGENT_PIPELINE_USER_GUIDE.md` (this file)
- `docs/AgenticOps_AI_Overview.pptx` and `docs/AgenticOps_AI_Documentation.docx` via `python docs/sync_all_documentation.py`
- Shared content source: `docs/doc_content.py`

See [`tasks/task_33_automatic_documentation_updates.md`](../tasks/task_33_automatic_documentation_updates.md).
