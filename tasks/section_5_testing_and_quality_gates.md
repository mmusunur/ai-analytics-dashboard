# 🧪 Section 5: Automated Testing, Excel Matrix Updates & Quality Gates

This document defines the automated testing procedures, Playwright browser testing tasks, Excel test matrix generation scripts, Quality Gate push policies, and regression validation steps.

---

## 📄 Dedicated Testing Task Files
- 📄 [`tasks/task_10_end_to_end_parameter_testing.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_10_end_to_end_parameter_testing.md) — Interactive Browser Parameter Combination Testing & Quality Gate Push Policy
- 📄 [`tasks/task_20_full_e2e_component_suite.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tasks/task_20_full_e2e_component_suite.md) — Full E2E + Unit Test Suite Component Validation & Regression Prevention

---

## 📊 1. Excel Test Matrix Automatic Update Task
- **Generator Script:** [`tests/generate_test_excel.py`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tests/generate_test_excel.py)
- **Output Spreadsheet:** [`tests/TEST_CASES.xlsx`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tests/TEST_CASES.xlsx)
- **Execution Command:** `python tests/generate_test_excel.py`
- **Functionality:**
  - Executes unit tests and Playwright browser tests in real-time.
  - Automatically generates and overwrites `tests/TEST_CASES.xlsx` with formatted, color-coded rows (Green for `PASS`, Red for `FAIL`).
  - Contains 64 detailed test case records across 7 segregated feature categories.
  - **🚫 Plain-Language Description Standard Directive:** All `Expected Result` and `Actual Result` entries MUST avoid technical API path/verb jargon (such as `GET /api/...`, `POST`, `HTTP 200`, `endpoint`). Every entry MUST be written in clear, simple, human-readable plain English sentences describing system behavior.

---

## 🧪 2. Pytest Unit Testing Suite
- **Execution Command:** `python -m pytest tests/unit/ -v --tb=short`
- **Total Test Cases:** 51 Unit Tests
- **Coverage:** ML models, AI Copilot, Anomaly alerts, KPI cards, Bar chart, Scatter plot, Heatmaps, FastAPI endpoints, Database filters.

---

## 🎭 3. Playwright Browser E2E Testing Suite
- **Execution Command:** `python -m pytest tests/browser/ -v --tb=short`
- **Total Test Cases:** 14 Interactive Browser Tests
- **Test File:** [`tests/browser/test_full_e2e_component_suite.py`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tests/browser/test_full_e2e_component_suite.py)

---

## 🚨 4. Mandatory Sequential Quality Gate & Excel Update Policy
- **Sequential 2-Stage Pipeline Directive:**
  1. **Stage 1 (Unit Tests):** Execute `python -m pytest tests/unit/ -v`.
  2. **Stage 2 (Real Browser Tests):** Execute `python -m pytest tests/browser/ -v`.
  3. **Stage 3 (Excel Sync Gate):** `TEST_CASES.xlsx` matrix is ONLY generated/updated IF AND ONLY IF both Stage 1 (Unit Tests) AND Stage 2 (Browser Tests) achieve a 100% PASS rate.
- **100% Pass Rate Mandate:** No code commit or git push is permitted unless all unit tests and browser tests pass cleanly.
- **Zero Hardcoding Directive:** All dates, warehouse facility numbers, and sprint projects MUST be extracted dynamically from live DOM or API responses — no static hardcoded test strings.
