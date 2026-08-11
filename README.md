# ⚡ AgenticOps AI — MCP-Driven Autonomous Enterprise Platform

> An autonomous multi-agent enterprise control plane powered by **MCP (Model Context Protocol)**, **FastAPI + React**, and an **Autonomous Agent Fleet with Live Telemetry**.

---

## ✨ Core Features & Recent Enhancements

- 📊 **Interactive Executive Dashboard** — KPI summary cards, Cases Built bar charts, Scatter plots, Heatmaps, and Warehouse procurement statistics.
- 🏭 **Warehouse Sales & Invoice Analytics** — Real-time PostgreSQL (`sptn_sales_data`) item & invoice statistics with date, warehouse, batch, and scratch filters.
- 🗄️ **Multi-Target DB Architecture** — Parameter-driven querying across `pg_prod`, `pg_dev`, `oracle_dev`, `oracle_f1`, `oracle_prod`.
- 🤖 **6-Stage Autonomous Task Pipeline** — Automated end-to-end task execution: **Pickup** (Plane API) ➔ **Understand** (Fuzzy Intent & LLM Classifier) ➔ **Build** (React & FastAPI edit) ➔ **Test** (Pytest & Playwright) ➔ **Close Task** (Plane REST API) ➔ **Git Push** (`origin/main`).
- ⚡ **Non-Blocking Background Sprint Watcher** — Polling `/api/sprints/tasks` automatically triggers `SprintWatcherAgent` in a daemon background thread.
- 🧠 **Daily Memory Persistence Engine** — Automatically updates `memory/conversations/assistant_conversation.jsonl`, `memory/task_history/YYYY-MM-DD_task_history.jsonl`, and `memory/agent_state.json` on every user conversation exchange.
- 📋 **Modular Task Index (`tasks.md` & `tasks/`)** — Master task specifications split into focused `.md` files under `tasks/` (e.g. `tasks/task_28_memory_and_daily_task_updates.md`, `tasks/task_7_git_automation.md`).
- 🛡️ **Auto-Restart Watchdog Engine** — [`scripts/agent_watchdog.py`](scripts/agent_watchdog.py) monitors `:8000`, `:5173`, and the sprint watcher; auto-restarts crashed services via [`scripts/server_health.py`](scripts/server_health.py).
- 🔧 **Rule-Based Builder Fallback** — [`agents/builder_rules.py`](agents/builder_rules.py) applies deterministic code fixes when LLM output is unavailable, alongside [`agents/builder_agent.py`](agents/builder_agent.py).
- 🧭 **Live Agent & Sprint Status UI** — Sidebar links to `/agents` (Agent Monitor) and `/sprints` (Sprint Board); floating pipeline panel shows active task, phase, and which agent is working (Builder, Tester, etc.).
- 📊 **Automated Excel Test Matrix** — Running `python tests/generate_test_excel.py` generates color-coded execution results in [`tests/TEST_CASES.xlsx`](tests/TEST_CASES.xlsx). Sprint tasks dynamically add browser test rows via [`tests/sprint_task_test_generator.py`](tests/sprint_task_test_generator.py) (no user interaction).
- 📖 **Agent Pipeline User Guide** — [`docs/AGENT_PIPELINE_USER_GUIDE.md`](docs/AGENT_PIPELINE_USER_GUIDE.md) (sprint auto-pickup, live status UI, documentation auto-update rules).

---

## 🤖 Autonomous Agent Fleet & LLM Model Allocation

| Agent Name | Script | LLM Model | Role & Responsibilities | Key Tools / Capabilities |
|---|---|---|---|---|
| **Orchestrator Agent** | [`agents/orchestrator_agent.py`](agents/orchestrator_agent.py) | `Claude 3.5 Opus` (`claude-opus-4-5`) | Master coordinator; task decomposition, sprint planning, and high-level workflow decisions | Plane API, GitHub API, Memory |
| **Builder Agent** | [`agents/builder_agent.py`](agents/builder_agent.py) | `Claude 3.5 Opus` (`claude-opus-4-5`) | Autonomous code generation (FastAPI backend & React components), bug fixing, and NLP taxonomy expansion | File System, Plane, Memory Manager |
| **Tester Agent** | [`agents/tester_agent.py`](agents/tester_agent.py) | `Claude 3.5 Sonnet` (`claude-sonnet-4-5`) | Precision test execution (`pytest` unit tests & `Playwright` browser E2E tests), quality gate validation | Terminal, Playwright Browser, Pytest |
| **Sprint Watcher** | [`agents/sprint_watcher_agent.py`](agents/sprint_watcher_agent.py) | `Claude 3.5 Haiku` (`claude-haiku-4-5`) | Continuous 15s background loop polling Plane tasks, detecting status updates, triggering automated builds/tests | Plane REST API, Subprocess Hooks |
| **Git Agent** | [`agents/git_agent.py`](agents/git_agent.py) | `Claude 3.5 Haiku` (`claude-haiku-4-5`) | Automated staging, committing, branch merging, merge conflict resolution, and End-of-Day pushing | Git CLI, GitHub MCP, Memory |
| **Plane Agent** | [`agents/plane_agent.py`](agents/plane_agent.py) | `Claude 3.5 Haiku` (`claude-haiku-4-5`) | Task creation, cycle/sprint management, and issue comments updating | Plane REST API |
| **Memory Manager** | [`agents/memory_manager.py`](agents/memory_manager.py) | Rule-Based State Engine | Per-conversation memory logger (`update_conversation_memory`), process inspector (`psutil`), persistent state storage (`agent_state.json`) | OS Process Table (`psutil`), File I/O |

---

## 🗂️ Project Structure

```
ai_analytics_dashboard/
├── tasks.md         # Master Task Index (links to tasks/*.md)
├── tasks/           # Modular Task Specifications (task_1 to task_28, section_1 to section_5)
├── agents/          # AI agents (Orchestrator, Builder, Tester, Plane, Git, Memory, Sprint Watcher)
├── backend/         # FastAPI backend (data, analytics, charts, warehouse_service, sprints)
├── frontend/        # React + Vite dashboard (Dashboard, WarehouseSalesAnalytics, KPICard, AgentTaskActivityTracker)
├── tests/           # pytest unit tests + Playwright browser tests + generate_test_excel.py
├── memory/          # Persistent agent memory (conversations/, task_history/, agent_state.json, nlp_taxonomy.json)
├── mcp_servers/     # MCP server configurations (plane, github, memory, browser)
├── scripts/         # start_all_services.bat/.sh, agent_watchdog.py, server_health.py, end_of_day.py
└── reports/         # Auto-generated test reports
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

# 4. Sprint Watcher Continuous Agent Loop (15s)
python scripts/run_sprint_watcher.py --interval 15

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
| `/api/agents/status` | GET | None | Returns real-time status and active tasks for all 6 agents |

---

## 📁 Memory & Conversation Logging System

Agent conversations and daily task states are automatically stored in `memory/`:
```
memory/
├── conversations/
│   ├── assistant_conversation.jsonl
│   └── orchestrator_conversation.jsonl
├── task_history/
│   └── 2026-08-05_task_history.jsonl
├── nlp_taxonomy.json
└── agent_state.json
```

---

*Built with ❤️ by AI agents — managed by Antigravity*

- **Automatic Documentation Sync:** [`docs/doc_content.py`](docs/doc_content.py) is the single source for PPTX + DOCX. Run `python docs/sync_all_documentation.py` to **replace in place** [`docs/AgenticOps_AI_Overview.pptx`](docs/AgenticOps_AI_Overview.pptx) and [`docs/AgenticOps_AI_Documentation.docx`](docs/AgenticOps_AI_Documentation.docx) — one file each, no duplicates.
