# 📌 TASK 36 — Dual Search Mode: Global Header vs AI Data Copilot

## 📋 Status
- **Status:** ✅ IMPLEMENTED & TESTED (2026-08-12)
- **Priority:** CRITICAL — governs all dashboard filter behavior
- **Related Tasks:** Task 1 (Header), Task 14 (Copilot), Task 35 (Browser Tests), Task 20 (E2E Suite)

---

## 🎯 Objective

The dashboard has **two independent search paths**. They must never be merged or confused:

| # | Search Path | User Action | Date Parameter | Warehouse |
|---|-------------|-------------|----------------|-----------|
| **1** | **Global Header** | Select date + DB + warehouse → **Submit** | `oerdte` = selected date | Global `#global-whse-selector` **with** date |
| **2** | **AI Data Copilot** | Type query → **Ask AI** | `oerdte = ''` (no date) | Parsed from NL query only |

---

## 🔀 Mode Switching Rules

```
┌─────────────────────────────────────────────────────────────┐
│  DEFAULT: Global Mode (date + DB + optional warehouse)     │
│  Trigger: #submit-db-btn OR global warehouse dropdown change │
└─────────────────────────────────────────────────────────────┘
                              │
              User asks Copilot │ "Warehouse 58 overview"
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  COPILOT MODE (no date — all available dates)               │
│  KPI / Bar / Scatter / Table → oerdte=''                    │
│  Banner: "Copilot Mode Active — no date restriction"        │
└─────────────────────────────────────────────────────────────┘
                              │
         User clicks Submit   │  OR  Clear / Clear Filters
         on global header     │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Back to GLOBAL MODE (restores applied date + global whse)  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Implementation Files

| Layer | File | Responsibility |
|-------|------|----------------|
| Frontend — Copilot | [`frontend/src/components/AiDataCopilot.jsx`](../frontend/src/components/AiDataCopilot.jsx) | POST `oerdte: ''`; never pass global date |
| Frontend — Dashboard | [`frontend/src/pages/Dashboard.jsx`](../frontend/src/pages/Dashboard.jsx) | `fetchAll(..., copilotMode)` dual paths; `globalWhse` state |
| Frontend — Table | [`frontend/src/components/WarehouseSalesAnalytics.jsx`](../frontend/src/components/WarehouseSalesAnalytics.jsx) | `oerdte=''` when `copilotFilterActive` |
| Backend | [`backend/routers/analytics.py`](../backend/routers/analytics.py) | Copilot endpoint; empty `oerdte` = all dates |

---

## 📐 Global Header Search (Mode 1)

### Controls
- `#global-date-picker` — Order date (`YYYY-MM-DD` → API `YYYYMMDD`)
- `#global-db-selector` — Target database (`pg_dev`, `oracle_dev`, etc.)
- `#global-whse-selector` — Optional warehouse (applies **with** global date)
- `#submit-db-btn` — Applies date + DB + warehouse; **clears copilot mode**

### API Calls (Global Mode)
All widgets MUST include the submitted date:
```
GET /api/charts/kpi?oerdte={YYYYMMDD}&target_db={db}&oewhse={whse}
GET /api/charts/bar?oerdte={YYYYMMDD}&target_db={db}&oewhse={whse}
GET /api/charts/scatter?oerdte={YYYYMMDD}&target_db={db}&oewhse={whse}
GET /api/warehouse/statistics?oerdte={YYYYMMDD}&target_db={db}&oewhse={whse}
```

### State Variables (`Dashboard.jsx`)
- `selectedDate` / `appliedDate` — form vs applied date
- `globalWhse` — header warehouse (NOT copilot)
- `copilotFilterActive === false`

---

## 🧠 AI Data Copilot Search (Mode 2)

### Controls
- `#copilot-input` — Natural language query
- `#copilot-submit-btn` / **Ask AI** — triggers copilot search
- `#copilot-clear-btn` — **Clear & Use Date Filter** → restores global mode

### API Call (Copilot Mode)
```
POST /api/analytics/ai-copilot
Body: { "prompt": "...", "target_db": "pg_dev", "oerdte": "" }
```
**CRITICAL:** Frontend MUST always send `"oerdte": ""`. Global header date is **ignored**.

### Dashboard Sync After Copilot
When copilot returns results, dashboard widgets refresh with:
- `oerdte = ''` (all dates)
- `oewhse` / `batch_id` / `only_scratches` from copilot intent parsing
- `copilotFilterActive === true`

### Banner Text
> Copilot Mode Active — Searching without date restriction (all available dates)

---

## 🚫 Forbidden Behaviors

| ❌ Wrong | ✅ Correct |
|---------|-----------|
| Copilot sends global date in POST body | Copilot sends `oerdte: ''` |
| Global warehouse dropdown activates copilot mode | Global whse uses `globalWhse` + applied date |
| KPI uses global date while copilot is active | KPI uses `oerdte=''` during copilot mode |
| Copilot re-runs when global date changes | Copilot re-runs only on `target_db` change |

---

## 🧪 Acceptance Tests

| Case ID | Mode | Assertion |
|---------|------|-----------|
| TC-06 | Copilot | POST body `oerdte=""` even when global date is set |
| TC-COMP-04 | Copilot | Global date submitted → copilot still sends no date |
| TC-COMP-11 | Global | Submit → KPI API URL contains `oerdte=` |
| TC-COMP-12 | Copilot | Warehouse 58 (9,700) vs 61 (10,900) — different totals |

### Per-Warehouse Calculations
- **Never hardcode** warehouse lists, dates, or KPI values in frontend or backend Python logic.
- UI sends `oerdte`, `oewhse`, `target_db` → API applies filters → PostgreSQL `sptn_sales_data`.
- Warehouse dropdown options come **only** from live `/api/charts/bar` response (`barData`).
- Offline dev fallback: optional `backend/data/warehouse_seed.json` filtered by the same UI params (replace with DB export).
| TC-UNIT-09 | Copilot | Empty `oerdte` returns ≥ dated query results |
| TC-COMP-01 | Global | Date + Submit → KPI matches dated API |

### Run Verification
```bash
python -m pytest tests/unit/test_task19_20_copilot_date_rules.py::test_unit09_copilot_never_uses_date_filter -v
python -m pytest tests/browser/test_full_e2e_component_suite.py::test_tc06_copilot_sends_no_date_in_api_request -v
python -m pytest tests/browser/test_comprehensive_module_suite.py -v
```

---

## ✅ Definition of Done

- [x] Copilot POST always sends `oerdte: ''`
- [x] Global Submit always sends dated API params
- [x] `fetchAll` has separate copilot vs global code paths
- [x] Warehouse table skips date when copilot active
- [x] Clear / Submit exits copilot mode
- [x] Unit + browser tests pass (57 browser, 14 unit copilot rules)
- [x] `TEST_CASES.xlsx` updated via Task 35
