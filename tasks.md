# 📋 System Task Specification & Master Index (`tasks.md`)

This master index organizes the **AI Analytics Dashboard Autonomous Agent Network** specifications into modular, lightweight, focused task documents located in the [`tasks/`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/) directory.

---

## 🤖 Sprint Agent — Mandatory Step Gates (Task 37) — **NO SKIPPING**

**Full spec:** [`tasks/task_37_auto_retry_until_tests_pass.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_37_auto_retry_until_tests_pass.md)

### Pipeline steps (each must PASS before the next runs)

| Step | Agent | Gate rule | On failure |
|------|-------|-----------|------------|
| **1. Pickup** | Sprint Watcher | Move Plane task → In Progress | Retry pickup next poll |
| **2. Build** | Builder | Code changes + builder exit 0 | **Stay on Build** — retry same step up to N times. **Do NOT run Test.** |
| **3. Test** | Tester | Unit + browser + sprint tests pass | **Return to Build** with failure log — fix code, then Test again |
| **3b. Verify-close** | Tester | **Only if Build already ✓** — re-test to close on Plane | If tests fail → **idle/waiting UI** (not frozen at 65%); retry after cooldown. **Do not** set `agent_working` during Test. |
| **4. Close** | Plane Agent | Mark Completed on Plane | Only after Test passes |
| **5. Git Push** | Git Agent | Commit **all meaningful repo paths** (see folder map below) | **Done ✓ only if commit succeeds OR tree clean** — never skip because verify-close |
| **6. Done** | — | UI shows Done | Plane closed **and** git gate passed |

### Mandatory rules (agents MUST follow)

1. **Never skip a failed step** — if Build fails, Test must **not** start.
2. **Retry the same step** — Build failure → retry Build with error context; Test failure → go back to Build (not straight to Close).
3. **No human To Do move** between retries — agent auto-moves To Do and re-picks after all cycles exhausted.
4. **UI checkmarks** — a step shows ✓ only when that step **actually passed** (`completed_steps` in pipeline state). **When idle with no active task**, all six steps show **○** (empty) — never stale ✓ from a prior task.
5. **Plane In Progress** during Build/Test is normal — **Done** only when all gates pass.
6. **Test heartbeat** — `tester_agent.py` writes `test_subphase` + `test_started_at` to pipeline state (starting → sprint_cases → unit → browser → excel). UI shows sub-phase chips and elapsed time. **`agent_working` is Build-only** — UI keeps polling during long Test runs.
7. **Verify-close failure** — pipeline resets to `idle` with a cooldown message (not stuck at 65% Testing). Sprint watcher retries verify-close after cooldown when task stays In Progress.
8. **Git gate (Task 38)** — Step 6 Done requires git sync. Git runs for **every** close (including verify-close), not only when Builder ran. Watcher **git sweep** retries uncommitted `agents/`, `backend/`, `frontend/src/`, `tasks/`, `tests/`, etc. each idle poll.

### 📁 Repo folder map — Git Agent commit allowlist

| Path | Commit after sprint task? |
|------|---------------------------|
| `agents/` | ✅ Agent pipeline code |
| `backend/` | ✅ FastAPI, routers, services, `data/` seed |
| `frontend/src/` | ✅ React components, pages, context |
| `scripts/` | ✅ Launchers, watcher, PPTX generators |
| `tasks/` + `tasks.md` | ✅ Specs & task docs |
| `tests/` | ✅ Unit + browser + Excel matrix |
| `config/` | ✅ Plane/MCP config |
| `docs/`, `mcp_servers/` | ✅ Documentation & MCP registry |
| Root | ✅ `README.md`, `.env.example`, `*.pptx` presentations |
| `memory/` (runtime) | ❌ agent_state, processed IDs, retry blobs |
| `.env`, `node_modules/`, `reports/` | ❌ Secrets, deps, generated reports |

### ⚡ Smart performance (complete tasks faster)

| Situation | Smart behavior | Typical time |
|-----------|----------------|--------------|
| **After Build (code changed)** | `full` mode — all unit + all browser tests | ~5–15 min |
| **Verify-close (Build already ✓)** | `fast` mode — unit + 2 smoke browser tests + sprint task cases only | ~2–4 min |
| **Watcher idle** | Poll Plane every **30s** | — |
| **Watcher has active task** | Poll every **15s** (`SPRINT_ACTIVE_POLL_INTERVAL`) | — |
| **Verify-close retry** | Cooldown **45s** (`SPRINT_VERIFY_CLOSE_COOLDOWN`) | — |

**Rules:** Never skip the Test gate — choose the **smallest test set that still validates the change**. Full comprehensive browser suite runs only after Build; verify-close uses targeted smoke + sprint cases. Override with env `SPRINT_TEST_MODE=full|fast`.

### Human vs agent

| Who | Action |
|-----|--------|
| **Human** | Create task in Plane → To Do **once** |
| **Agent** | Everything else — pickup, build, test, retry, close, git |
| **Human** | **Do not** manually move task between retries |

**Restart sprint watcher** after changing `agents/sprint_watcher_agent.py`.

**Do not** manually implement an open Plane sprint task in Cursor (e.g. Data Analytics) — let the sprint pipeline run it.

---

## 📚 Agent Documentation & Memory Mandates (Tasks 39–40)

| Task | Rule | Agent MUST |
|------|------|------------|
| **39** | [`task_39_readme_architecture_sync.md`](tasks/task_39_readme_architecture_sync.md) | Update **`README.md`** whenever architecture, agents, pipeline, or new `tasks/*.md` specs change — same session as the code change |
| **40** | [`task_40_daily_memory_recall.md`](tasks/task_40_daily_memory_recall.md) | On new day / session start, **read `memory/`** (yesterday's `task_history`, `agent_state`, conversations) via `get_previous_day_context()` before acting |
| **41** | [`task_41_build_authenticity_pipeline_telemetry.md`](tasks/task_41_build_authenticity_pipeline_telemetry.md) | **Build is not Done** — show sub-phases, elapsed time, verify-only vs code-changed; full completion requires Test→Close→Git |
| **42** | [`task_42_build_detail_popup_end_to_end.md`](tasks/task_42_build_detail_popup_end_to_end.md) | **Build detail popup** — files + functionality persist from Build through Done for the current task; cleared only on idle/new pickup |
| **43** | [`task_43_demo_readiness_zero_manual.md`](tasks/task_43_demo_readiness_zero_manual.md) | **Demo readiness** — zero manual intervention; servers up, git gate demo-friendly, pipeline resets idle after Done |
| **44** | [`task_44_user_delivery_notice.md`](tasks/task_44_user_delivery_notice.md) | **User delivery notice** — after each task: what was added, where to find it, how to use it (UI banner + Build popup + Plane comment) |

9. **README sync (Task 39)** — after agent or architecture changes: update `tasks.md` index + `README.md` (features, agent table, pipeline table, latest task numbers). Included in git allowlist.
10. **Daily memory recall (Task 40)** — agents check previous-day logs in `memory/task_history/` so tomorrow's session knows what completed, failed, or stayed In Progress.
11. **Build authenticity (Task 41)** — Pickup/Build checkmarks ≠ task complete. UI shows build sub-phases, elapsed seconds, and **verify-only** (amber) vs **code changed** (green). **Click Build** to open detail popup (files + functionality). Test gate always runs after Build.
12. **Build detail persistence (Task 42)** — `set_pipeline_status()` MUST carry `build_files_modified`, `build_functionality`, `build_outcome`, and `build_intents` for the **same task_id** through Test → Close → Git → Done. Popup stays populated until pipeline goes idle or a new task is picked up.
13. **Demo readiness (Task 43)** — Before demo: all unit tests pass; servers + watcher running; `GIT_PUSH_OPTIONAL=true` for local-commit git gate; pipeline returns to **idle** after Done; builder auto-wires components to Dashboard.
14. **User delivery notice (Task 44)** — After Build/Close, agent MUST tell the user **what was added**, **where to open it** (route link), and **how to use it** — Sprint Board banner, Build popup, Recently Completed list, and Plane task comment.

---

## 🚨 Section 1: Mandatory Operational Rules & Git Automation
- 📄 [`tasks/section_1_mandatory_tasks.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/section_1_mandatory_tasks.md)
  - 6-Stage Autonomous Lifecycle Pipeline (Pickup → Understand → Build → Test → Close → Git Push)
  - 🚫 **Mandatory Zero Unnecessary / Spam Git Commit Directive**
  - Mandatory Services & Launcher Scripts ([`scripts/start_all_services.bat`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/scripts/start_all_services.bat) / [`scripts/start_all_services.sh`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/scripts/start_all_services.sh))
  - Automatic README.md Maintenance Mandate
  - Mandatory Per-Turn Conversation Memory Update Directive
- 📄 [`tasks/task_7_git_automation.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_7_git_automation.md) — Pre-Approved Git Automation, Branch Merging, Anti-Spam Commit Filter & Merge Conflict Resolution

---

## 🖥️ Section 2: Architecture & Data Flow Rules
- 📄 [`tasks/section_2_system_architecture.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/section_2_system_architecture.md)
  - Full Technology Stack (React + Vite, FastAPI, PostgreSQL, Plane API)
  - Header Parameter Propagation & **Dual Search Rules (Task 36)**
  - Single-Warehouse Chart Filtering Specifications

---

## 📑 Section 3: Screen-by-Screen Component Task Files

### 🎯 Global Controls & Header
- 📄 [`tasks/task_1_header_controls.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_1_header_controls.md) — Header Controls Panel (Global Search Mode 1: date + DB + warehouse + Submit)
- 📄 [`tasks/task_36_dual_search_global_vs_copilot.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_36_dual_search_global_vs_copilot.md) — **Dual Search Architecture:** Global Header vs AI Copilot (date vs no-date, mode switching, DoD)
- 📄 [`tasks/task_26_memory_and_sprint_automation.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_26_memory_and_sprint_automation.md) — Dynamic `#header-clear-filter` Component

### 📊 Summary Cards & Visualizations
- 📄 [`tasks/task_2_kpi_cards.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_2_kpi_cards.md) — Executive KPI Summary Cards
- 📄 [`tasks/task_3_charts_analytics.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_3_charts_analytics.md) — Warehouse Analytics Charts
- 📄 [`tasks/task_27_single_warehouse_filtering.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_27_single_warehouse_filtering.md) — Single-Warehouse Chart Filtering

### 📋 Data Table & Procurement
- 📄 [`tasks/task_4_data_table.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_4_data_table.md) — Warehouse Item Level Data Table

### 🧠 AI & Agent Network
- 📄 [`tasks/task_6_agents_and_mcp.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_6_agents_and_mcp.md) — Autonomous Agent Network & Plane PM Integration
- 📄 [`tasks/task_14_ai_data_copilot.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_14_ai_data_copilot.md) — Natural Language AI Data Copilot (Copilot Search Mode 2: no date parameter)
- 📄 [`tasks/task_15_anomaly_alert_panel.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_15_anomaly_alert_panel.md) — Real-Time Anomaly & Risk Alerts
- 📄 [`tasks/task_28_memory_and_daily_task_updates.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_28_memory_and_daily_task_updates.md) — Daily Memory Persistence & State Updating Engine

### 🗄️ Database & Fleet Services
- 📄 [`tasks/task_5_database_service.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_5_database_service.md) — Multi-Database SQL Service
- 📄 [`tasks/task_7_git_automation.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_7_git_automation.md) — Pre-Approved Git Automation, Branch Merges, Anti-Spam Commit Filter & Conflict Resolution
- 📄 [`tasks/task_8_parallel_background_agents.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_8_parallel_background_agents.md) — Continuous Parallel Background Agent Fleet
- 📄 [`tasks/task_29_multi_project_autonomous_execution.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_29_multi_project_autonomous_execution.md) — Multi-Project Workspace Scanning (`agentbuilder`) & End-to-End Execution Mandate
- 📄 [`tasks/task_30_sprint_board_browser_navigation.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_30_sprint_board_browser_navigation.md) — Sprint Board Browser Navigation, Page Refresh & Dynamic Dropdown E2E Verification
- 📄 [`tasks/task_9_continuous_application_uptime.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_9_continuous_application_uptime.md) — Continuous Server Uptime & Mandatory .bat / .sh Launchers
- 📄 [`tasks/task_30_agent_monitoring_watchdog.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_30_agent_monitoring_watchdog.md) — Real-Time Agent Monitoring & Watchdog Supervisor
- 📄 [`tasks/task_32_application_uptime_and_sprint_pipeline.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_32_application_uptime_and_sprint_pipeline.md) — Application Must Stay Running + Sprint Pipeline Quality Gates
- 📄 [`tasks/task_33_automatic_documentation_updates.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_33_automatic_documentation_updates.md) — Auto-Update README, tasks/, docs/, PPTX + DOCX on Major Changes (`python docs/sync_all_documentation.py`)
- 📄 [`tasks/task_34_sprint_close_on_test_pass.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_34_sprint_close_on_test_pass.md) — Close Plane Sprint Task When Quality Gate Tests Pass (never leave Completed work stuck In Progress)
- 📄 [`tasks/task_35_comprehensive_browser_testing.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_35_comprehensive_browser_testing.md) — Comprehensive Browser Tests: All Fields + Submit + Calculation Verification + Excel Status Sync (see Task 36 for dual search rules)
- 📄 [`tasks/task_37_auto_retry_until_tests_pass.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_37_auto_retry_until_tests_pass.md) — **Auto-Retry Until Pass:** On test failure agent rebuilds automatically with failure context; UI shows retry/failed/done clearly (no manual To Do move)
- 📄 [`tasks/task_38_git_repo_sync_gate.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_38_git_repo_sync_gate.md) — **Git Repo Sync Gate:** Commit allowlist by folder structure; never mark Done without git sync; idle git sweep
- 📄 [`tasks/task_39_readme_architecture_sync.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_39_readme_architecture_sync.md) — **README Architecture Sync:** Update README.md whenever agents, pipeline, or architecture changes (same session)
- 📄 [`tasks/task_40_daily_memory_recall.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_40_daily_memory_recall.md) — **Daily Memory Recall:** Read yesterday's task_history + agent_state at session start (`get_previous_day_context()`)
- 📄 [`tasks/task_41_build_authenticity_pipeline_telemetry.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_41_build_authenticity_pipeline_telemetry.md) — **Build Authenticity:** Sub-phase telemetry, verify-only vs code-changed; task complete only after Test→Close→Git
- 📄 [`tasks/task_42_build_detail_popup_end_to_end.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_42_build_detail_popup_end_to_end.md) — **Build Detail Popup:** Files + functionality persist from Build through Done for current task; cleared on idle/new pickup
- 📄 [`tasks/task_43_demo_readiness_zero_manual.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_43_demo_readiness_zero_manual.md) — **Demo Readiness:** Zero manual intervention — servers, watcher, git gate, pipeline idle reset, builder Dashboard wiring
- 📄 [`tasks/task_44_user_delivery_notice.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_44_user_delivery_notice.md) — **User Delivery Notice:** What was added, where to find it, how to use it — UI + Plane comment

---

## 🔌 Section 4: API Endpoint Registry & Database Schemas
- 📄 [`tasks/section_4_api_registry.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/section_4_api_registry.md)
  - Active FastAPI Endpoints (`/api/data`, `/api/charts`, `/api/warehouse`, `/api/sprints`, `/api/agents`)
  - PostgreSQL Table Schemas (`sptn_sales_data`)

---

## 🧪 Section 5: Automated Testing & Excel Matrix Tasks
- 📄 [`tasks/section_5_testing_and_quality_gates.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/section_5_testing_and_quality_gates.md) — Automated Testing, Excel Matrix Updates & Quality Gates
- 📄 [`tasks/task_10_end_to_end_parameter_testing.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_10_end_to_end_parameter_testing.md) — Interactive Browser Parameter Combination Testing
- 📄 [`tasks/task_20_full_e2e_component_suite.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_20_full_e2e_component_suite.md) — Full Playwright Browser E2E Suite (39 Scenarios) & Pytest Unit Suite (65 Tests)
- 📄 [`tasks/task_32_application_uptime_and_sprint_pipeline.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_32_application_uptime_and_sprint_pipeline.md) — Servers Must Stay Running Before Browser Tests & Sprint Closure
