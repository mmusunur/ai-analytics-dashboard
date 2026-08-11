# 📌 TASK 32 — Application Uptime Mandate & Sprint Pipeline Quality Gates (`#uptime-sprint-pipeline`)

## Overview
Agents **must start the application and keep it running** continuously. Browser tests and sprint task closure are forbidden while servers are offline.

---

## Mandatory Continuous Services

| Service | Port | Launcher |
|---------|------|----------|
| FastAPI Backend | `8000` | `scripts/start_all_services.bat` / `.sh` |
| Vite Frontend | `5173` | same |
| Sprint Watcher | — | `scripts/run_sprint_watcher.py --interval 60` |
| Watchdog Supervisor | — | `scripts/agent_watchdog.py` |

---

## Server Health Helpers
- **Script:** [`scripts/server_health.py`](../scripts/server_health.py)
- **`ensure_servers_running()`** — starts missing backend/frontend and waits until both ports respond.
- **Used by:** `agents/tester_agent.py`, `agents/sprint_watcher_agent.py`, `scripts/agent_watchdog.py`

---

## Watchdog Self-Healing
- **Script:** [`scripts/agent_watchdog.py`](../scripts/agent_watchdog.py)
- Polls every 15s: checks `:8000`, `:5173`, and sprint watcher process.
- Auto-restarts crashed servers and sprint watcher without user intervention.

---

## Sprint Pipeline (End-to-End)

```
Pickup (todo/unstarted/triaged)
  → Mark In Progress on Plane
  → Builder (LLM + rule-based fallback via builder_rules.py)
  → register_sprint_task_tests() — dynamic browser cases from task title/description
  → ensure_servers_running()
  → Tester (68 unit + 46 browser incl. dynamic sprint cases)
  → Update TEST_CASES.xlsx (always — PASS/FAIL per row)
  → PASS: Complete on Plane + git commit
  → FAIL: Move to To Do, log output, discard session processed-id
```

### Dynamic Sprint Test Cases (No User Interaction)
- **Generator:** [`tests/sprint_task_test_generator.py`](../tests/sprint_task_test_generator.py)
- **Browser runner:** [`tests/browser/test_sprint_task_dynamic.py`](../tests/browser/test_sprint_task_dynamic.py)
- **Registry:** `memory/sprint_test_registry.json`
- **Excel:** [`tests/generate_test_excel.py`](../tests/generate_test_excel.py) appends a **Sprint Task:** category per picked-up Plane task

### Pickup Rules
- **New pickup:** `AGENT_PICKUP_GROUPS = {unstarted, todo, triaged}`
- **Excluded from new pickup:** `backlog`, `completed`, `cancelled`
- **Retry:** Stale `in_progress` tasks may be re-processed

### Builder Fallback
- **File:** [`agents/builder_rules.py`](../agents/builder_rules.py)
- Applies deterministic patches when LLM is unavailable or returns no diff.

---

## Agent Directive (Plain Language)
> Before running Playwright browser tests or closing a Plane task, verify the dashboard loads at `http://localhost:5173` and the API responds at `http://localhost:8000/api/health`. If not, run `scripts/start_all_services.bat` (Windows) or `bash scripts/start_all_services.sh` (Linux/macOS), or call `ensure_servers_running()` from Python.

---

## Related Tasks
- [`task_9_continuous_application_uptime.md`](task_9_continuous_application_uptime.md)
- [`task_30_agent_monitoring_watchdog.md`](task_30_agent_monitoring_watchdog.md)
- [`task_29_multi_project_autonomous_execution.md`](task_29_multi_project_autonomous_execution.md)
- [`section_5_testing_and_quality_gates.md`](section_5_testing_and_quality_gates.md)
