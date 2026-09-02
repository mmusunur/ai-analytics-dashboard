# ⚡ AgenticOps AI — MCP-Driven Autonomous Enterprise Platform

> An autonomous multi-agent enterprise control plane powered by **MCP (Model Context Protocol)**, **FastAPI + React**, and an **Autonomous Agent Fleet with Live Telemetry**.

> **Master task index:** [`tasks.md`](tasks.md) — mandatory sprint gates (Task 37), git sync (Task 38), dual search (Task 36), and all specs under [`tasks/`](tasks/).

---

## ✨ Core Features & Recent Enhancements (Aug 2026)

- 📊 **Interactive Executive Dashboard** — KPI summary cards, Cases Built bar charts, Scatter plots, Heatmaps, and Warehouse procurement statistics.
- 🏭 **Warehouse Sales & Invoice Analytics** — Real-time PostgreSQL (`sptn_sales_data`) item & invoice statistics with date, warehouse, batch, and scratch filters; local `warehouse_seed.json` fallback.
- 🗄️ **Multi-Target DB Architecture** — Parameter-driven querying across `pg_prod`, `pg_dev`, `oracle_dev`, `oracle_f1`, `oracle_prod`.
- 🤖 **6-Stage Gated Sprint Pipeline (Task 37)** — **Pickup → Build → Test → Close → Git → Done** with **no step skipping**. Build failure blocks Test; Test failure returns to Build with failure context; verify-close uses fast test mode.
- ⚡ **Smart Test Modes** — `full` (all unit + browser) after code changes; `fast` (unit + smoke + sprint cases ~1 min) for verify-close. Test heartbeat (`test_subphase`, elapsed time) in Sprint Board UI.
- 📦 **Git Repo Sync Gate (Task 38)** — Git Agent commits allowlisted paths (`agents/`, `backend/`, `frontend/src/`, `tasks/`, `tests/`, etc.) on **every** task close (including verify-close). Idle **git sweep** retries uncommitted files. Done only when Plane closed **and** git gate passes.
- 🔍 **Dual Search (Task 36)** — Global Header (date + DB + warehouse) vs AI Copilot (no date, NL intent); mutually exclusive modes.
- 🧠 **Builder NLP & Rules** — [`agents/builder_nlp.py`](agents/builder_nlp.py) intent taxonomy (incl. `DATA_ANALYTICS_ML`), [`agents/builder_helpers.py`](agents/builder_helpers.py) component builders, [`agents/builder_rules.py`](agents/builder_rules.py) deterministic fallback.
- ⚡ **Non-Blocking Background Sprint Watcher** — Polls Plane every **30s** (idle) / **15s** (active task); triggers build/test/close/git in daemon thread via `/api/sprints/tasks`.
- 🧭 **Live Pipeline UI** — [`AgentPipelineTracker`](frontend/src/components/AgentPipelineTracker.jsx) + [`TaskQueuePanel`](frontend/src/components/TaskQueuePanel.jsx): 6-step checkmarks, test sub-phases, verify-close waiting. **Idle = all ○** (no stale checkmarks).
- 🛡️ **`agent_working` Build-only** — UI polling pauses only during Builder file edits, not during long Test runs.
- 📊 **Automated Excel Test Matrix** — [`tests/generate_test_excel.py`](tests/generate_test_excel.py) + dynamic sprint cases via [`tests/sprint_task_test_generator.py`](tests/sprint_task_test_generator.py).
- 📽️ **Architecture Presentation** — [`AI_Analytics_Dashboard_Presentation.pptx`](AI_Analytics_Dashboard_Presentation.pptx) (regenerate: `python scripts/generate_architecture_pptx.py`).
- 📋 **Modular Task Index** — [`tasks.md`](tasks.md) + [`tasks/`](tasks/) (Tasks 1–40). **Task 39:** update README on architecture changes. **Task 40:** daily memory recall at session start.
- 🛡️ **Auto-Restart Watchdog** — [`scripts/agent_watchdog.py`](scripts/agent_watchdog.py) monitors `:8000`, `:5173`, sprint watcher.

---

## 🤖 Autonomous Agent Fleet & LLM Model Allocation

| Agent Name | Script | LLM Model | Role & Responsibilities | Key Tools / Capabilities |
|---|---|---|---|---|
| **Orchestrator Agent** | [`agents/orchestrator_agent.py`](agents/orchestrator_agent.py) | `Claude 3.5 Opus` (`claude-opus-4-5`) | Master coordinator; task decomposition, sprint planning, and high-level workflow decisions | Plane API, GitHub API, Memory |
| **Builder Agent** | [`agents/builder_agent.py`](agents/builder_agent.py) | `Claude 3.5 Opus` (`claude-opus-4-5`) | Autonomous code generation (FastAPI backend & React components), bug fixing, and NLP taxonomy expansion | File System, Plane, Memory Manager |
| **Tester Agent** | [`agents/tester_agent.py`](agents/tester_agent.py) | `Claude 3.5 Sonnet` (`claude-sonnet-4-5`) | Quality gate: `--mode full|fast`, unit + Playwright + dynamic sprint cases, Excel sync, test heartbeat | Terminal, Playwright, Pytest |
| **Sprint Watcher** | [`agents/sprint_watcher_agent.py`](agents/sprint_watcher_agent.py) | `Claude 3.5 Haiku` (`claude-haiku-4-5`) | Gated pipeline orchestrator: pickup, build/test loops, verify-close, Plane close, git sweep | Plane REST API, subprocess hooks, `memory_manager` telemetry |
| **Git Agent** | [`agents/git_agent.py`](agents/git_agent.py) | `Claude 3.5 Haiku` (`claude-haiku-4-5`) | Repo sync gate: allowlisted commit paths, pull-rebase-push, idle sweep (Task 38) | Git CLI, GitHub MCP, `commit_and_push_for_task()` |
| **Plane Agent** | [`agents/plane_agent.py`](agents/plane_agent.py) | `Claude 3.5 Haiku` (`claude-haiku-4-5`) | Task creation, cycle/sprint management, and issue comments updating | Plane REST API |
| **Memory Manager** | [`agents/memory_manager.py`](agents/memory_manager.py) | Rule-Based State Engine | Pipeline telemetry (`set_pipeline_status`, `completed_steps`, `test_subphase`), task queue, fleet PID scan | `agent_state.json`, `psutil`, File I/O |

---

## 🚦 Sprint Pipeline Quick Reference

See **[`tasks.md`](tasks.md)** for the full mandatory gate table. Summary:

| Step | Agent | Key rule |
|------|-------|----------|
| 1 Pickup | Sprint Watcher | Plane → In Progress |
| 2 Build | Builder | Exit 0 before Test |
| 3 Test | Tester | `full` after build; `fast` on verify-close |
| 4 Close | Plane Agent | Mark Completed when tests pass |
| 5 Git | Git Agent | Commit allowlisted repo paths (Task 38) |
| 6 Done | UI | All gates passed; idle = empty pipeline ○ |

**Env vars:** `SPRINT_TEST_MODE`, `SPRINT_VERIFY_CLOSE_COOLDOWN` (45s), `SPRINT_ACTIVE_POLL_INTERVAL` (15s), `SPRINT_WATCHER_INTERVAL` (30s).

---

## 🗂️ Project Structure

```
ai_analytics_dashboard/
├── tasks.md         # Master Task Index (gates, git map, links to tasks/*.md)
├── tasks/           # Modular specs (task_1 … task_38, section_1 … section_5)
├── AI_Analytics_Dashboard_Presentation.pptx   # Architecture deck (see scripts/generate_architecture_pptx.py)
├── agents/          # Orchestrator, Builder (+nlp, helpers, rules), Tester, Sprint Watcher, Git, Plane, Memory
├── backend/         # FastAPI (data, analytics, charts, warehouse, sprints, mcp)
├── frontend/        # React + Vite (Dashboard, Sprint Board, AgentPipelineTracker, DataAnalytics, Copilot)
├── tests/           # pytest unit + Playwright browser + generate_test_excel.py
├── memory/          # agent_state.json, task_history/, conversations/ (runtime — not git-committed)
├── mcp_servers/     # MCP registry (plane, github, memory, browser)
├── config/          # plane_config.json
├── scripts/         # start_all_services, run_sprint_watcher, generate_architecture_pptx, server_health
└── reports/         # Generated test HTML reports
```

---

## 🚀 1-Click Launchers & Continuous Operations

> **Agent directive:** Start the application once and keep it running. Do not run browser tests or close Plane tasks while `:8000` or `:5173` are down. Use the watchdog or `ensure_servers_running()` to recover automatically.

### 1-Click Launch (Zero Approval Prompts)
* **Windows Launcher:** `scripts\start_all_services.bat`
* **Linux/macOS Launcher:** `bash scripts/start_all_services.sh`

### Individual Agent & Service Commands
```bash
# 1. FastAPI Backend Server (Port 8000)
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 2. Vite Frontend Dev Server (Port 5173)
cd frontend && npm run dev -- --host 0.0.0.0

# 3. Agent & Server Health Watchdog Supervisor (auto-restarts :8000, :5173, sprint watcher)
python scripts/agent_watchdog.py

# 3b. Ensure servers are up (used internally by tester & sprint watcher)
python -c "from scripts.server_health import ensure_servers_running; print(ensure_servers_running())"

# 4. Sprint Watcher (30s idle / 15s when task active)
python scripts/run_sprint_watcher.py --interval 30

# 4b. Tester — fast vs full quality gate
python agents/tester_agent.py --mode fast --task-id <id> --task-title "My Task"
python agents/tester_agent.py --mode full

# 5. Automated Excel Test Case Matrix Generation
python tests/generate_test_excel.py

# 6. Git Agent & End-of-Day Auto-Push
python scripts/end_of_day.py
```

---

## 🔀 Git Commands Reference

| Command | Description |
|---|---|
| `python scripts/end_of_day.py` | Staging, committing, and pushing all daily progress to remote `origin/main` |
| `python -m agents.git_agent` | Git MCP Server & Git Agent automation handler |
| `git pull origin main` | Synchronizes local workspace with latest remote commits |
| `git status --porcelain` | Used by agents to detect changed files in real time |
| `git push origin main` | Pushes staged commits to GitHub repository (`mmusunur/ai-analytics-dashboard`) |

---

## 📋 Key API Endpoints

| Endpoint | Method | Parameters | Description |
|---|---|---|---|
| `/api/health` | GET | None | Backend & DB health check |
| `/api/warehouse/statistics` | GET | `target_db`, `oerdte`, `batch_id`, `oewhse`, `oeinv`, `only_scratches` | Direct PostgreSQL query for warehouse item/invoice stats |
| `/api/analytics/ai-copilot` | POST | `prompt`, `target_db`, `oerdte` | AI Data Copilot intent parser & table filter generator (Date-Agnostic) |
| `/api/charts/kpi` | GET | `oerdte`, `target_db` | Returns KPI cards (Total Warehouses, Cases Built, Order Qty, Invoices) |
| `/api/charts/bar` | GET | `oerdte`, `target_db`, `oewhse` | Returns cases built breakdown per warehouse (Supports single-whse filtering) |
| `/api/charts/scatter` | GET | `oerdte`, `target_db`, `oewhse` | Returns order quantity vs cases built scatter plot |
| `/api/sprints/tasks` | GET | None | Fetches Plane sprint tasks and triggers non-blocking `SprintWatcherAgent` |
| `/api/agents/status` | GET | None | Pipeline phase, `completed_steps`, `test_subphase`, task queue, fleet agent PIDs |

---

## 📋 Latest Task Specs (see [`tasks.md`](tasks.md))

| Task | Topic |
|------|--------|
| **36** | Dual search — Global Header vs AI Copilot |
| **37** | Mandatory step gates & auto-retry until pass |
| **38** | Git repo sync gate & folder allowlist |
| **39** | README sync on architecture / agent changes |
| **40** | Daily memory recall — read yesterday's `memory/task_history/` |
| **35** | Comprehensive browser testing + calculation verify |
| **34** | Close Plane task when quality gate passes |

---

## 📁 Memory & Conversation Logging System

Agent conversations and daily task states are automatically stored in `memory/` (Task 28 write, **Task 40 read-back**):

```python
from agents.memory_manager import get_previous_day_context
print(get_previous_day_context()["summary"])  # call at session start
```

```
memory/
├── conversations/
│   ├── assistant_conversation.jsonl
│   └── orchestrator_conversation.jsonl
├── task_history/
│   └── YYYY-MM-DD_task_history.jsonl   # one file per day — agents read yesterday's file
├── nlp_taxonomy.json
└── agent_state.json
```

---

*Built with ❤️ by AI agents — managed by Antigravity*

- **Automatic Documentation Sync:** [`docs/doc_content.py`](docs/doc_content.py) is the single source for PPTX + DOCX. Run `python docs/sync_all_documentation.py` to **replace in place** [`docs/AgenticOps_AI_Overview.pptx`](docs/AgenticOps_AI_Overview.pptx) and [`docs/AgenticOps_AI_Documentation.docx`](docs/AgenticOps_AI_Documentation.docx) — one file each, no duplicates.
