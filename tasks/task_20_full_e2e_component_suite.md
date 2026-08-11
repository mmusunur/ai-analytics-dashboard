# 📌 TASK 20 — Full E2E + Unit Test Suite: Component Validation & Regression Prevention (`#full-e2e-testing`)

## 📋 Overview
This task specification governs the **Full Automated Testing Suite** (Pytest Unit Tests + Playwright Browser End-to-End Tests) for the AI Analytics Dashboard.

---

## 🧪 Section 1: Test Suite Specifications

### 1. Unit Test Suite (`tests/unit/`)
- **Execution Command:** `python -m pytest tests/unit/ -v --tb=short`
- **Total Test Cases:** 65 Unit Tests
- **Key Modules Tested:**
  - `test_analytics.py` — ML models, AI Copilot, Anomaly alerts
  - `test_charts.py` — KPI cards, Bar chart, Scatter plot, Heatmaps
  - `test_core_components.py` — Navbar, Warehouse Analytics components
  - `test_data_endpoints.py` — CSV ingestion, Health check, Summary stats
  - `test_task19_20_copilot_date_rules.py` — Date-agnostic Copilot & Date-strict Dashboard rules
  - `test_warehouse_db_filters.py` — PostgreSQL parameters & schema integrity

  - `test_sprints.py` — Sprint board API, agent status, pickup group rules, watcher behavior

### 2. Playwright Browser E2E Suite (`tests/browser/`)
- **Execution Command:** `python -m pytest tests/browser/ -v --tb=short`
- **Total Test Cases:** 39 Interactive Browser Tests
- **Prerequisite:** Application servers must be running (`:8000` + `:5173`). Auto-started by `tester_agent.py` via `scripts/server_health.py`.
- **Key Flow Validations:**
  - Default date auto-application on page load (`#global-date-picker`)
  - KPI card real number rendering
  - Date parameter submission & propagation
  - AI Copilot query submission & "Copilot Mode Active" banner
  - Multi-database engine toggle (`pg_dev` ↔ `oracle_dev`)
  - Excel test result sheet maintenance (`tests/TEST_CASES.xlsx`)

---

## 🚨 Section 2: Quality Gate Push Policy & Excel Matrix Standards
- **Sequential Testing Gate:** Real Playwright Browser Tests (`pytest tests/browser/`) are strictly required AFTER unit tests pass. `TEST_CASES.xlsx` is ONLY updated if both unit and browser tests pass 100%.
- **100% Test Pass Rate Mandate:** No code commit or git push is permitted unless all unit tests and browser tests pass cleanly.
- **Zero Hardcoding Rule:** Dates, warehouse facility numbers, and sprint projects MUST be computed dynamically — no static hardcoded test strings.
- **🚫 Plain-Language Test Description Standard:** All test case `Expected Result` and `Actual Result` spreadsheet descriptions MUST avoid technical API verbs and path jargon (such as `GET /api/...`, `POST`, `HTTP 200`, `endpoint`). Entries must be written in clear, simple, human-readable plain English sentences describing system functionality.
