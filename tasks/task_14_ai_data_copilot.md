# 📌 TASK 14 — Natural Language AI Data Copilot Component & Query Engine (`#ai-data-copilot`)

## 📋 Task Description & Architecture
- **Status:** ✅ IMPLEMENTED & ENFORCED
- **Component File:** [`frontend/src/components/AiDataCopilot.jsx`](../frontend/src/components/AiDataCopilot.jsx)
- **Backend Service:** [`backend/routers/analytics.py`](../backend/routers/analytics.py) (`POST /api/analytics/ai-copilot`)
- **Related:** [Task 36 — Dual Search Global vs Copilot](task_36_dual_search_global_vs_copilot.md) (Copilot Search = Mode 2)

---

## ⚠️ MANDATORY RULE: Copilot Search Has NO Date Parameter

This is **Mode 2** of the dual search system (see Task 36).

| Rule | Detail |
|------|--------|
| **No global date** | Frontend MUST POST `"oerdte": ""` — never the header date |
| **Full dataset** | Backend queries all available dates for the user's question |
| **Intent filters only** | Warehouse, batch, scratch parsed from NL query — not from header |
| **Dashboard sync** | On result, KPI/charts/table refresh with `oerdte=''` until user Submit or Clear |

### Copilot Mode Active Banner
- Text: *"Copilot Mode Active — Searching without date restriction (all available dates)"*
- **Clear & Use Date Filter** button (`#copilot-clear-btn`) → restores global date mode

---

## 🛠️ Implementation Details

### 1. Frontend (`AiDataCopilot.jsx`)
```javascript
// CORRECT — always empty date
await axios.post(`${API}/api/analytics/ai-copilot`, {
  prompt: q,
  target_db: globalTargetDb,
  oerdte: '',  // NEVER globalDate
});
```
- Quick pills: *High Scratch Quantity*, *Pending Procurement Transfers*, etc.
- Auto-applies copilot filters to dashboard via `onApplyFilter` (warehouse/batch/scratch only)
- Re-runs query on `target_db` change only — **NOT** on global date change

### 2. Backend (`analytics.py`)
- Parses intent: warehouse number, scratch filter, batch ID from prompt
- `oerdte_filter = ""` when frontend sends empty string → all dates
- Returns: `summary_answer`, `chart_data`, `filtered_whse`, `filter_scratch`, `metrics_found`

### 3. Dashboard Integration (`Dashboard.jsx`)
- `handleApplyTableFilter` → sets `copilotFilterActive = true`
- `fetchAll(..., copilotMode=true)` → all widgets use `oerdte=''`

---

## 🧪 Tests

| Case | File | Assertion |
|------|------|-----------|
| TC-06 | `test_full_e2e_component_suite.py` | Copilot POST never contains global date |
| TC-COMP-04 | `test_comprehensive_module_suite.py` | Copilot sends `oerdte=''` with global date set |
| TC-UNIT-09 | `test_task19_20_copilot_date_rules.py` | No-date query ≥ dated query results |
| TC-UNIT-10 | `test_task19_20_copilot_date_rules.py` | Empty oerdte returns data |
| TC-UNIT-13/14 | `test_task19_20_copilot_date_rules.py` | Warehouse & scratch intent parsing |

---

## 🚫 Do NOT
- Send `globalDate` as `oerdte` in copilot POST
- Apply header date when copilot filter is active
- Treat global warehouse dropdown changes as copilot filters
