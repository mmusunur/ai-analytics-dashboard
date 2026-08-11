# 🧪 Section 5: Automated Testing, Excel Matrix Updates & Quality Gates

This document defines the automated testing procedures, Playwright browser testing tasks, Excel test matrix generation scripts, Quality Gate push policies, and regression validation steps.

---

## 📄 Dedicated Testing Task Files
- 📄 [`tasks/task_10_end_to_end_parameter_testing.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_10_end_to_end_parameter_testing.md) — Interactive Browser Parameter Combination Testing & Quality Gate Push Policy
- 📄 [`tasks/task_20_full_e2e_component_suite.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_20_full_e2e_component_suite.md) — Full E2E + Unit Test Suite Component Validation & Regression Prevention

---

## 📊 1. Excel Test Matrix Automatic Update Task
- **Generator Script:** [`tests/generate_test_excel.py`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tests/generate_test_excel.py)
- **Sprint Task Generator:** [`tests/sprint_task_test_generator.py`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tests/sprint_task_test_generator.py)
- **Dynamic Browser Tests:** [`tests/browser/test_sprint_task_dynamic.py`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tests/browser/test_sprint_task_dynamic.py)
- **Registry:** `memory/sprint_test_registry.json` — persisted dynamic cases per Plane sprint task
- **Output Spreadsheet:** [`tests/TEST_CASES.xlsx`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tests/TEST_CASES.xlsx)
- **Execution Command:** `python tests/generate_test_excel.py --unit-passed true --browser-passed true --task-id <plane-task-id>`
- **Autonomous Pipeline:** `SprintWatcherAgent` → `tester_agent.py --task-id ...` registers sprint cases, runs **all** unit + browser + dynamic sprint browser tests, then updates Excel **every run** (PASS or FAIL).
- **Functionality:**
  - Dynamically adds browser test cases from each picked-up Plane sprint task title/description + matching `tasks/*.md` specs.
  - Executes unit tests and Playwright browser tests in real-time (no user interaction).
  - Automatically generates and overwrites `tests/TEST_CASES.xlsx` with formatted, color-coded rows (Green for `PASS`, Red for `FAIL`, Yellow for `PENDING`).
  - Contains 72+ detailed test case records across 8 segregated feature categories (aligned with **65 unit + 39 browser** pytest tests).
  - **🚫 Plain-Language Description Standard Directive:** All `Expected Result` and `Actual Result` entries MUST avoid technical API path/verb jargon (such as `GET /api/...`, `POST`, `HTTP 200`, `endpoint`). Every entry MUST be written in clear, simple, human-readable plain English sentences describing system behavior.

---

## 🧪 2. Pytest Unit Testing Suite
- **Execution Command:** `python -m pytest tests/unit/ -v --tb=short`
- **Total Test Cases:** 65 Unit Tests
- **Coverage:** ML models, AI Copilot, Anomaly alerts, KPI cards, Bar chart, Scatter plot, Heatmaps, FastAPI endpoints, Database filters.

---

## 🎭 3. Playwright Browser E2E Testing Suite
- **Execution Command:** `python -m pytest tests/browser/ -v --tb=short`
- **Total Test Cases:** 39 Interactive Browser Tests (across 6 browser test modules)
- **Prerequisite:** Backend `:8000` and frontend `:5173` MUST be running. [`agents/tester_agent.py`](../agents/tester_agent.py) and [`scripts/server_health.py`](../scripts/server_health.py) auto-start servers if down.
- **Test Files:** [`tests/browser/test_dashboard_loads.py`](../tests/browser/test_dashboard_loads.py), [`test_full_e2e_component_suite.py`](../tests/browser/test_full_e2e_component_suite.py), [`test_ai_copilot_and_anomalies.py`](../tests/browser/test_ai_copilot_and_anomalies.py), [`test_sprint_board_browser.py`](../tests/browser/test_sprint_board_browser.py), and others.

---

## 🚨 4. Mandatory Sequential Quality Gate & Excel Update Policy
- **Sequential 3-Stage Pipeline Directive:**
  0. **Stage 0 (Server Uptime):** Verify or auto-start backend `:8000` and frontend `:5173` via `ensure_servers_running()`.
  1. **Stage 1 (Unit Tests):** Execute `python -m pytest tests/unit/ -v`.
  2. **Stage 2 (Real Browser Tests):** Execute `python -m pytest tests/browser/ -v` (requires live servers).
  3. **Stage 3 (Excel Sync Gate):** `TEST_CASES.xlsx` matrix is ONLY generated/updated IF AND ONLY IF both Stage 1 AND Stage 2 achieve a 100% PASS rate.
- **100% Pass Rate Mandate:** No code commit or git push is permitted unless all unit tests and browser tests pass cleanly.
- **Zero Hardcoding Directive:** All dates, warehouse facility numbers, and sprint projects MUST be extracted dynamically from live DOM or API responses — no static hardcoded test strings.
