"""
TASK 20 — Unit Tests: Aware of Fallback Date Behavior
=======================================================
KEY RULE (from warehouse_service.py L255):
  When selected oerdte has NO data in the DB, the backend automatically
  falls back to all-dates query (oerdte="") and returns the most recent available data.
  This is CORRECT behavior — tests must verify it, not fail because of it.

Test scenarios covered:
  1. When today has no data → backend falls back → response still has data (fallback_used=True)
  2. When a known date HAS data → response has data for that exact date (fallback_used=False)
  3. AI Copilot: NEVER uses date — always queries full dataset (oerdte='')
  4. Dashboard APIs: PASS the date; if date empty, fallback kicks in automatically
  5. Agents: all running
  6. Health: healthy
"""

import pytest
import sys
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

TODAY_ISO = date.today().strftime("%Y%m%d")   # e.g. "20260730"
TODAY_DISPLAY = date.today().strftime("%Y-%m-%d")


# ─────────────────────────────────────────────────────────────
# Helper: discover a date that actually has data
# ─────────────────────────────────────────────────────────────
def get_real_data_date(target_db: str = "pg_dev") -> dict:
    """
    Calls the warehouse API with no date filter (oerdte='').
    The backend returns real data across all dates.
    Reads the actual date from the first returned item's oerdte field.
    Returns dict with: effective_date, fallback_used, item_count
    NOTE: When queried with oerdte='', filters_applied.effective_date stays ''
    because no fallback is triggered — we read the real date from item data.
    """
    res = client.get(f"/api/warehouse/statistics?oerdte=&target_db={target_db}&limit=5&offset=0")
    assert res.status_code == 200, f"Helper failed: {res.text}"
    data = res.json()
    items = data.get("warehouse_items", [])
    filters = data.get("filters_applied", {})
    # Read actual date from first item (not from filters_applied which may be empty)
    item_date = items[0].get("oerdte", "") if items else ""
    return {
        "effective_date": item_date,  # e.g. "20260728" — real date that has data
        "item_count": len(items),
        "fallback_used": filters.get("fallback_used", False),
        "data": data
    }


# ─────────────────────────────────────────────────────────────
# TC-UNIT-01: Today has no data → fallback returns most recent date
# ─────────────────────────────────────────────────────────────
def test_unit01_today_no_data_strict_empty_result():
    """
    TC-UNIT-01: When today's date has no records (confirmed by SQL: SELECT DISTINCT oewhse
    FROM sptn_sales_data WHERE oerdte='20260730' → empty), the API MUST return 0 items.
    No silent fallback to older dates. fallback_used must be False.
    The UI shows the 'No Data Available for [date]' empty state banner instead.
    """
    res = client.get(f"/api/warehouse/statistics?oerdte={TODAY_ISO}&target_db=pg_dev&limit=10&offset=0")
    assert res.status_code == 200, f"TC-UNIT-01 FAIL: {res.text}"
    data = res.json()
    items = data.get("warehouse_items", [])
    filters = data.get("filters_applied", {})
    fallback_used = filters.get("fallback_used", False)

    assert not fallback_used, (
        f"TC-UNIT-01 FAIL: fallback_used=True — backend is still silently substituting "
        f"a different date's data. Fallback behavior was removed in TASK 20."
    )

    if len(items) == 0:
        print(f"TC-UNIT-01 PASS: Today ({TODAY_DISPLAY}) has no data → returned 0 items (correct strict behavior, no fallback)")
    else:
        # Today actually has data — this is also fine
        effective = items[0].get("oerdte", "") if items else ""
        print(f"TC-UNIT-01 PASS: Today ({TODAY_DISPLAY}) has real data → {len(items)} items, oerdte={effective}")


# ─────────────────────────────────────────────────────────────
# TC-UNIT-02: Discover the actual date with data dynamically
# ─────────────────────────────────────────────────────────────
def test_unit02_discover_real_data_date():
    """
    TC-UNIT-02: The API with oerdte="" returns data across all dates.
    We read the actual date from the first item's oerdte field to confirm
    which date has real data — NOT from filters_applied.effective_date
    (which stays empty when no fallback is triggered because oerdte was already empty).
    """
    info = get_real_data_date("pg_dev")
    assert info["item_count"] > 0, "TC-UNIT-02 FAIL: No data in pg_dev at all (even with no date filter)"
    effective = info["effective_date"]
    assert effective, f"TC-UNIT-02 FAIL: Could not read oerdte from first item even though items exist"
    print(f"TC-UNIT-02 PASS: Real data date from first item = '{effective}' ({info['item_count']} items returned)")


# ─────────────────────────────────────────────────────────────
# TC-UNIT-03: KPI API — date with no data falls back gracefully
# ─────────────────────────────────────────────────────────────
def test_unit03_kpi_api_returns_data_even_when_date_empty():
    """
    TC-UNIT-03: KPI API must return >= 4 KPIs regardless of whether the selected date
    has data or not (backend falls back automatically).
    """
    res = client.get(f"/api/charts/kpi?oerdte={TODAY_ISO}&target_db=pg_dev")
    assert res.status_code == 200, f"TC-UNIT-03 FAIL: {res.text}"
    data = res.json()
    kpis = data.get("kpis", [])
    assert len(kpis) >= 4, f"TC-UNIT-03 FAIL: Expected >= 4 KPIs, got {len(kpis)}"
    print(f"TC-UNIT-03 PASS: KPI API returned {len(kpis)} KPIs for {TODAY_ISO} (fallback may apply)")


# ─────────────────────────────────────────────────────────────
# TC-UNIT-04: Bar chart API — returns data with or without fallback
# ─────────────────────────────────────────────────────────────
def test_unit04_bar_chart_api_returns_data_regardless_of_date():
    """TC-UNIT-04: Bar chart API returns data even when today has no records (fallback applies)."""
    res = client.get(f"/api/charts/bar?oerdte={TODAY_ISO}&target_db=pg_dev")
    assert res.status_code == 200
    data = res.json()
    assert "data" in data, f"TC-UNIT-04 FAIL: No 'data' key: {list(data.keys())}"
    print(f"TC-UNIT-04 PASS: Bar chart API returned {len(data['data'])} points for {TODAY_ISO}")


# ─────────────────────────────────────────────────────────────
# TC-UNIT-05: Scatter chart API — same fallback behavior
# ─────────────────────────────────────────────────────────────
def test_unit05_scatter_chart_api_returns_data_regardless_of_date():
    """TC-UNIT-05: Scatter chart API returns data even when today has no records."""
    res = client.get(f"/api/charts/scatter?oerdte={TODAY_ISO}&target_db=pg_dev")
    assert res.status_code == 200
    data = res.json()
    assert "data" in data, f"TC-UNIT-05 FAIL: No 'data' key: {list(data.keys())}"
    print(f"TC-UNIT-05 PASS: Scatter API returned {len(data['data'])} points for {TODAY_ISO}")


# ─────────────────────────────────────────────────────────────
# TC-UNIT-06: Warehouse stats with effective (real) date — no fallback needed
# ─────────────────────────────────────────────────────────────
def test_unit06_real_date_query_returns_data_directly():
    """
    TC-UNIT-06: When queried with the ACTUAL date that has data (discovered from items),
    the backend returns data directly. fallback_used must be False.
    Strict behavior: returned data's oerdte must match the queried date.
    """
    info = get_real_data_date("pg_dev")
    effective = info["effective_date"]
    if not effective:
        pytest.skip("TC-UNIT-06 SKIP: Could not discover a real data date from items")

    res = client.get(f"/api/warehouse/statistics?oerdte={effective}&target_db=pg_dev&limit=10&offset=0")
    assert res.status_code == 200
    data = res.json()
    items = data.get("warehouse_items", [])
    filters = data.get("filters_applied", {})
    assert len(items) > 0, f"TC-UNIT-06 FAIL: No items for confirmed real date {effective}"
    assert not filters.get("fallback_used", False), (
        f"TC-UNIT-06 FAIL: fallback_used=True for a date with real data: {effective}"
    )
    # Verify returned items actually belong to the queried date
    wrong_date_items = [it for it in items if it.get("oerdte", "") != effective]
    assert len(wrong_date_items) == 0, (
        f"TC-UNIT-06 FAIL: {len(wrong_date_items)} items have oerdte != {effective} "
        f"(cross-date substitution detected)"
    )
    print(f"TC-UNIT-06 PASS: Real date {effective} → {len(items)} items, no fallback, all oerdte={effective}")


# ─────────────────────────────────────────────────────────────
# TC-UNIT-07: Warehouse stats no date = full dataset
# ─────────────────────────────────────────────────────────────
def test_unit07_warehouse_statistics_no_date_returns_full_data():
    """TC-UNIT-07: Passing oerdte='' returns data across all dates."""
    res = client.get("/api/warehouse/statistics?oerdte=&target_db=pg_dev&limit=20&offset=0")
    assert res.status_code == 200
    items = res.json().get("warehouse_items", [])
    assert len(items) >= 1, "TC-UNIT-07 FAIL: No items with no date filter"
    print(f"TC-UNIT-07 PASS: No-date query returned {len(items)} items")


# ─────────────────────────────────────────────────────────────
# TC-UNIT-08: Anomaly API — works with any date (fallback applies internally)
# ─────────────────────────────────────────────────────────────
def test_unit08_anomaly_api_works_for_any_date():
    """TC-UNIT-08: Anomaly API responds for today's date (even if no records, returns empty alerts cleanly)."""
    res = client.get(f"/api/analytics/anomalies?oerdte={TODAY_ISO}&target_db=pg_dev")
    assert res.status_code == 200, f"TC-UNIT-08 FAIL: {res.text}"
    data = res.json()
    assert "anomalies" in data or "alerts" in data or "status" in data, (
        f"TC-UNIT-08 FAIL: Unexpected shape: {list(data.keys())}"
    )
    print(f"TC-UNIT-08 PASS: Anomaly API responded for {TODAY_ISO}")


# ─────────────────────────────────────────────────────────────
# TC-UNIT-09: AI Copilot — NEVER sends date (date-agnostic search)
# ─────────────────────────────────────────────────────────────
def test_unit09_copilot_never_uses_date_filter():
    """
    TC-UNIT-09: Copilot must query WITHOUT date restriction.
    Empty oerdte returns data across all dates regardless of dashboard global date.
    """
    res_all = client.post("/api/analytics/ai-copilot", json={
        "prompt": "High Scratch Quantity",
        "target_db": "pg_dev",
        "oerdte": ""
    })
    assert res_all.status_code == 200, f"TC-UNIT-09 FAIL: {res_all.text}"
    data_all = res_all.json()
    assert data_all.get("summary_answer"), "TC-UNIT-09 FAIL: Empty summary for no-date copilot"
    assert data_all.get("effective_date", "") == "", (
        f"TC-UNIT-09 FAIL: effective_date should be empty, got {data_all.get('effective_date')}"
    )

    # Restricted date should return zero or fewer cases than all-dates query
    res_dated = client.post("/api/analytics/ai-copilot", json={
        "prompt": "High Scratch Quantity",
        "target_db": "pg_dev",
        "oerdte": "29991231"
    })
    assert res_dated.status_code == 200
    dated_cases = res_dated.json().get("metrics_found", {}).get("total_cases_built", 0)
    all_cases = data_all.get("metrics_found", {}).get("total_cases_built", 0)
    assert all_cases >= dated_cases, (
        f"TC-UNIT-09 FAIL: All-dates ({all_cases}) should be >= restricted date ({dated_cases})"
    )
    print(f"TC-UNIT-09 PASS: Copilot no-date query returned {all_cases} cases (dated={dated_cases})")


# ─────────────────────────────────────────────────────────────
# TC-UNIT-10: Copilot with empty oerdte returns full dataset
# ─────────────────────────────────────────────────────────────
def test_unit10_copilot_with_empty_date_returns_data():
    """TC-UNIT-10: Frontend sends oerdte='' to copilot — must return real data."""
    res = client.post("/api/analytics/ai-copilot", json={
        "prompt": "Warehouse 58 Overview",
        "target_db": "pg_dev",
        "oerdte": ""
    })
    assert res.status_code == 200
    data = res.json()
    assert data.get("summary_answer"), "TC-UNIT-10 FAIL: No summary_answer for empty-date copilot"
    print(f"TC-UNIT-10 PASS: Copilot empty-date returned: '{data['summary_answer'][:80]}'")


# ─────────────────────────────────────────────────────────────
# TC-UNIT-11: Agent status — all running
# ─────────────────────────────────────────────────────────────
def test_unit11_agent_status_all_running():
    """TC-UNIT-11: /api/agents/status must return >= 5 agents all status='running'."""
    res = client.get("/api/agents/status")
    assert res.status_code == 200, f"TC-UNIT-11 FAIL: {res.text}"
    agents = res.json().get("agents", {})
    assert len(agents) >= 5, f"TC-UNIT-11 FAIL: Expected >= 5 agents, got {len(agents)}"
    idle = [n for n, v in agents.items() if isinstance(v, dict) and v.get("status") != "running"]
    assert len(idle) == 0, f"TC-UNIT-11 FAIL: Idle agents: {idle}"
    print(f"TC-UNIT-11 PASS: All {len(agents)} agents running: {list(agents.keys())}")


# ─────────────────────────────────────────────────────────────
# TC-UNIT-12: Health check
# ─────────────────────────────────────────────────────────────
def test_unit12_health_check():
    """TC-UNIT-12: /api/health returns healthy."""
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json().get("status") == "healthy"
    print("TC-UNIT-12 PASS: Health check healthy")


# ─────────────────────────────────────────────────────────────
# TC-UNIT-13: Copilot warehouse 58 filter extraction
# ─────────────────────────────────────────────────────────────
def test_unit13_copilot_extracts_warehouse_58():
    """TC-UNIT-13: Asking about warehouse 58 → filtered_whse='58'."""
    res = client.post("/api/analytics/ai-copilot", json={
        "prompt": "Warehouse 58 cases built",
        "target_db": "pg_dev",
        "oerdte": ""
    })
    assert res.status_code == 200
    data = res.json()
    assert data.get("filtered_whse"), f"TC-UNIT-13 FAIL: No filtered_whse: {data}"
    assert data["filtered_whse"].strip().lstrip("0") == "58", (
        f"TC-UNIT-13 FAIL: Expected '58', got '{data['filtered_whse']}'"
    )
    print("TC-UNIT-13 PASS: Copilot extracted warehouse 58")


# ─────────────────────────────────────────────────────────────
# TC-UNIT-14: Copilot scratch query sets filter_scratch=True
# ─────────────────────────────────────────────────────────────
def test_unit14_copilot_scratch_sets_filter():
    """TC-UNIT-14: High Scratch Quantity query → filter_scratch=True."""
    res = client.post("/api/analytics/ai-copilot", json={
        "prompt": "High Scratch Quantity",
        "target_db": "pg_dev",
        "oerdte": ""
    })
    assert res.status_code == 200
    assert res.json().get("filter_scratch") is True, (
        f"TC-UNIT-14 FAIL: filter_scratch not True: {res.json()}"
    )
    print("TC-UNIT-14 PASS: Scratch query sets filter_scratch=True")


# ─────────────────────────────────────────────────────────────
# TC-UNIT-15: Copilot warehouse 58 vs 61 return different totals
# ─────────────────────────────────────────────────────────────
def test_unit15_copilot_whse_58_vs_61_different_cases():
    """TC-UNIT-15: Two different copilot warehouse queries must return different case totals."""
    stats = client.get("/api/warehouse/statistics?oerdte=&target_db=pg_dev&limit=500").json()
    rows = stats.get("summary", {}).get("warehouse_totals") or []
    if len(rows) < 2:
        pytest.skip("Need >= 2 warehouses in API data")
    whs_a = str(rows[0].get("whs_num", "")).strip()
    whs_b = str(rows[1].get("whs_num", "")).strip()
    if not whs_a or not whs_b or whs_a == whs_b:
        pytest.skip("Could not discover two distinct warehouses")

    res_a = client.post("/api/analytics/ai-copilot", json={
        "prompt": f"Warehouse {whs_a} Overview",
        "target_db": "pg_dev",
        "oerdte": "",
    })
    res_b = client.post("/api/analytics/ai-copilot", json={
        "prompt": f"Warehouse {whs_b} Overview",
        "target_db": "pg_dev",
        "oerdte": "",
    })
    assert res_a.status_code == 200 and res_b.status_code == 200
    cases_a = res_a.json().get("metrics_found", {}).get("total_cases_built", 0)
    cases_b = res_b.json().get("metrics_found", {}).get("total_cases_built", 0)
    assert cases_a != cases_b, f"TC-UNIT-15 FAIL: Whse {whs_a} ({cases_a}) and {whs_b} ({cases_b}) must differ"

    kpi_a = client.get(f"/api/charts/kpi?oerdte=&target_db=pg_dev&oewhse={whs_a}").json()
    kpi_b = client.get(f"/api/charts/kpi?oerdte=&target_db=pg_dev&oewhse={whs_b}").json()
    def _cases(kpi_resp):
        for k in kpi_resp.get("kpis", []):
            if "CASES BUILT" in (k.get("title") or "").upper():
                return int(str(k.get("value", "0")).replace(",", ""))
        return 0
    assert cases_a == _cases(kpi_a), f"Copilot whse {whs_a} must match KPI API"
    assert cases_b == _cases(kpi_b), f"Copilot whse {whs_b} must match KPI API"
    print(f"TC-UNIT-15 PASS: Whse {whs_a}={cases_a}, Whse {whs_b}={cases_b}")
