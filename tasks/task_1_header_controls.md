# 📌 TASK 1 — Global Parameter & Header Control Panel (`#global-header-controls`)

## 🖥️ Screen / Component Location
- **Component File:** [`frontend/src/pages/Dashboard.jsx`](../frontend/src/pages/Dashboard.jsx)
- **UI Placement:** Top Navigation Header Control Bar
- **Related:** [Task 36 — Dual Search Global vs Copilot](task_36_dual_search_global_vs_copilot.md) (Global Search = Mode 1)

---

## ⚠️ Dual Search Rule (Task 36)

The global header controls **Mode 1 — Global Search**. When the user uses these controls (NOT the AI Copilot):
- All API calls **MUST include `oerdte`** (the submitted order date)
- Optional warehouse from `#global-whse-selector` applies **together with** the date
- Clicking **Submit** **clears Copilot mode** and restores global date filtering

---

## 🎯 Sub-Task Breakdown

### Sub-Task 1.1: 📅 Order Date Picker (`#global-date-picker`)
- **Element ID:** `#global-date-picker`
- **Description:** Select target order date (`oerdte` in `YYYY-MM-DD` format).
- **Behavior:** Updates `selectedDate`; applied on **Submit** as `appliedDate`.

### Sub-Task 1.2: 🗄️ Target Database Selector (`#global-db-selector`)
- **Element ID:** `#global-db-selector`
- **Options:** `pg_dev`, `oracle_dev`, `oracle_f1`
- **Behavior:** Updates `selectedDb`; applied on **Submit** as `appliedTargetDb`.

### Sub-Task 1.3: 🏢 Global Warehouse Selector (`#global-whse-selector`)
- **Element ID:** `#global-whse-selector`
- **Description:** Filter by warehouse facility **with global date** (NOT copilot mode).
- **Behavior:**
  - Updates `globalWhse` state
  - When copilot is **inactive**: immediately calls `fetchAll(appliedDate, appliedTargetDb, { whse }, false)`
  - When copilot is **active**: dropdown is read-only (shows copilot whse); use Submit or Clear to exit copilot
- **Banner:** Shows "Global Warehouse: Whse XX" when `globalWhse` is set

### Sub-Task 1.4: 🚀 Submit Button (`#submit-db-btn`)
- **Element ID:** `#submit-db-btn`
- **Behavior:**
  1. Clears copilot mode (`copilotFilterActive = false`, `tableFilters = null`)
  2. Sets `appliedDate`, `appliedTargetDb`
  3. Calls `fetchAll(selectedDate, selectedDb, { whse: globalWhse }, false)` — **dated** API queries

### Sub-Task 1.5: ✕ Clear Filters (`#header-clear-filter-btn`)
- Clears `globalWhse`, copilot filters, and restores global date-only view

### Sub-Task 1.6: ⚡ Active Target DB Status Badge
- Displays `Active: PG_DEV` (or current target DB)

### Sub-Task 1.7: Date & DB Submit Reload Verification
- After Submit, verify fresh API calls to:
  - `/api/charts/kpi?oerdte={date}&target_db={db}`
  - `/api/charts/bar?oerdte={date}&target_db={db}`
  - `/api/charts/scatter?oerdte={date}&target_db={db}`
  - `/api/warehouse/statistics?oerdte={date}&target_db={db}`

---

## 🧪 Tests
- TC-COMP-01, TC-COMP-02, TC-COMP-11 — [`test_comprehensive_module_suite.py`](../tests/browser/test_comprehensive_module_suite.py)
- Interactive flow Step 1–2 — [`test_interactive_ui_copilot_flow.py`](../tests/browser/test_interactive_ui_copilot_flow.py)
