# 📌 TASK 27 — Single-Warehouse Chart Filtering (`#single-warehouse-filter`)

## Overview
When a single warehouse facility is selected (via header, Copilot, or table filter), **all chart widgets** must filter to that warehouse only.

---

## Backend
- **Endpoints:** `/api/charts/bar`, `/api/charts/scatter`, `/api/charts/kpi`
- **Parameter:** `oewhse` — when set, aggregate and return data for that facility only.
- **Tests:** `test_task27_single_warehouse_chart_filtering` in [`tests/unit/test_charts.py`](../tests/unit/test_charts.py)

## Frontend
- **Components:** Dashboard header controls, `WarehouseSalesAnalytics`, bar/scatter chart containers
- **Rule:** Propagate `oewhse` from global filter state to every chart fetch call.

## Browser Validation
- Copilot warehouse extraction updates charts and table ([`tests/browser/test_ai_copilot_and_anomalies.py`](../tests/browser/test_ai_copilot_and_anomalies.py))
- Interactive warehouse dropdown filter ([`tests/browser/test_interactive_ui_copilot_flow.py`](../tests/browser/test_interactive_ui_copilot_flow.py))
