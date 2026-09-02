# 📌 TASK 35 — Comprehensive Browser Testing & Excel Status Sync

## 📋 Status
- **Status:** ✅ IMPLEMENTED
- **Depends On:** [Task 36 — Dual Search Global vs Copilot](task_36_dual_search_global_vs_copilot.md)

---

## 🎯 Objective

Every screen and module must be browser-tested by **selecting all relevant fields**, clicking **Submit**, and **cross-checking calculations** against the backend API. Each test case status is recorded and synced to `tests/TEST_CASES.xlsx`.

---

## Mandatory Test Procedure (Every Screen)

1. Select all applicable fields (date, DB, warehouse, scratch where relevant)
2. Click **Submit** (global) or **Ask AI** (copilot)
3. Verify calculations — UI KPI / bar / table vs API
4. Record PASS/FAIL in `memory/browser_test_registry.json`
5. Regenerate Excel: `python tests/generate_test_excel.py --browser-passed true`

---

## Test Files

| File | Purpose |
|------|---------|
| [`tests/browser/test_comprehensive_module_suite.py`](../tests/browser/test_comprehensive_module_suite.py) | TC-COMP-01 … TC-COMP-11 |
| [`tests/browser/calculation_verifier.py`](../tests/browser/calculation_verifier.py) | API cross-check helpers |
| [`tests/browser/browser_case_tracker.py`](../tests/browser/browser_case_tracker.py) | PASS/FAIL registry |
| [`tests/browser/conftest.py`](../tests/browser/conftest.py) | Pytest hooks + Excel sync |

---

## TC-COMP Coverage Matrix

| Case | Screen | Mode | Verification |
|------|--------|------|--------------|
| TC-COMP-01 | Dashboard | Global | Date + DB Submit → KPI vs API |
| TC-COMP-02 | Dashboard | Global | Warehouse + date → bar chart vs API |
| TC-COMP-03 | Dashboard | Global | Table summary vs API |
| TC-COMP-04 | Dashboard | **Copilot** | Global date set → copilot sends `oerdte=''` |
| TC-COMP-05 | Analytics | Smoke | ML train controls load |
| TC-COMP-06 | Sprint Board | Smoke | Workspace + project + 4 columns |
| TC-COMP-07 | Agent Monitor | Smoke | Fleet cards visible |
| TC-COMP-08 | MCP Explorer | Smoke | Page loads |
| TC-COMP-09 | Dashboard | Global | Scratch filter chain |
| TC-COMP-10 | Dashboard | Global | Single whse: KPI = bar chart |
| TC-COMP-11 | Dashboard | **Global** | Submit sends `oerdte` in KPI API |

---

## Run Command

```bash
python -m pytest tests/browser/test_comprehensive_module_suite.py -v
python -m pytest tests/browser/ -v
python tests/generate_test_excel.py --browser-passed true
```
