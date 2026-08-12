"""
Cross-check dashboard UI calculations against backend API responses.
Used by comprehensive browser tests to verify KPI, bar chart, and table totals align.
"""

import re
import urllib.request
import urllib.parse
import json
from typing import Optional

API_URL = "http://127.0.0.1:8000"


def _get(path: str) -> dict:
    with urllib.request.urlopen(f"{API_URL}{path}", timeout=15) as resp:
        return json.loads(resp.read().decode())


def discover_date_with_data(target_db: str = "pg_dev") -> Optional[str]:
    """Find a YYYYMMDD date from API data (reads first item oerdte — no hardcoded dates)."""
    try:
        data = fetch_warehouse_stats(oerdte="", target_db=target_db, limit=50)
        items = data.get("warehouse_items") or []
        dates = sorted({str(it.get("oerdte", "")).strip() for it in items if it.get("oerdte")}, reverse=True)
        for oerdte in dates:
            check = fetch_warehouse_stats(oerdte=oerdte, target_db=target_db, limit=1)
            if (check.get("total_count") or 0) > 0:
                return oerdte
        if (data.get("total_count") or 0) > 0:
            return ""
    except Exception:
        pass
    return None


def discover_two_warehouses(target_db: str = "pg_dev", oerdte: str = "") -> tuple[str, str]:
    """Pick two warehouses with different case totals from live API (UI-driven discovery)."""
    stats = fetch_warehouse_stats(oerdte=oerdte, target_db=target_db, limit=500)
    rows = stats.get("summary", {}).get("warehouse_totals") or []
    if len(rows) < 2:
        return ("", "")
    sorted_rows = sorted(rows, key=lambda r: int(r.get("cases_built") or 0))
    low = str(sorted_rows[0].get("whs_num", "")).strip()
    high = str(sorted_rows[-1].get("whs_num", "")).strip()
    if low and high and low != high:
        return (low, high)
    return ("", "")


def build_query(
    oerdte: str = "",
    target_db: str = "pg_dev",
    oewhse: str = "",
    batch_id: str = "",
    oeinv: str = "",
    only_scratches: bool = False,
) -> str:
    params = {"oerdte": oerdte, "target_db": target_db}
    if oewhse:
        params["oewhse"] = oewhse
    if batch_id:
        params["batch_id"] = batch_id
    if oeinv:
        params["oeinv"] = oeinv
    if only_scratches:
        params["only_scratches"] = "true"
    return "?" + urllib.parse.urlencode(params)


def fetch_kpi(**filters) -> dict:
    return _get("/api/charts/kpi" + build_query(**filters))


def fetch_bar(**filters) -> dict:
    return _get("/api/charts/bar" + build_query(**filters))


def fetch_warehouse_stats(limit: int = 20, offset: int = 0, **filters) -> dict:
    q = build_query(**filters)
    sep = "&" if "?" in q else "?"
    return _get(f"/api/warehouse/statistics{q}{sep}limit={limit}&offset={offset}")


def parse_number(text: str) -> int:
    """Parse '8,500' or '8500' to int."""
    if not text:
        return 0
    cleaned = re.sub(r"[^\d]", "", str(text))
    return int(cleaned) if cleaned else 0


def parse_percent(text: str) -> float:
    m = re.search(r"([\d.]+)\s*%", str(text))
    return float(m.group(1)) if m else 0.0


def kpi_by_title(kpi_response: dict, title_fragment: str) -> dict:
    for k in kpi_response.get("kpis", []):
        if title_fragment.upper() in (k.get("title") or "").upper():
            return k
    return {}


def bar_total_cases(bar_response: dict) -> int:
    return sum(int(d.get("value") or 0) for d in bar_response.get("data", []))


def assert_cases_aligned(api_summary_cases: int, ui_cases: int, tolerance_pct: float = 0.01) -> None:
    if api_summary_cases == 0 and ui_cases == 0:
        return
    diff = abs(api_summary_cases - ui_cases)
    allowed = max(1, int(api_summary_cases * tolerance_pct))
    assert diff <= allowed, (
        f"Cases built mismatch: API={api_summary_cases:,} UI={ui_cases:,} (diff={diff:,})"
    )
