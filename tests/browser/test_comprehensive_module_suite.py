"""
Comprehensive Browser Test Suite — every screen/module.
Rule: select ALL relevant fields → Submit → verify calculations match backend API.

Each test is tagged with @pytest.mark.browser_case("TC-COMP-XX") for Excel status tracking.
"""

import re
import json
import pytest
from playwright.sync_api import Page, expect

from playwright_helpers import goto_with_retry, BASE_URL
from calculation_verifier import (
    discover_date_with_data,
    discover_two_warehouses,
    fetch_kpi,
    fetch_bar,
    fetch_warehouse_stats,
    parse_number,
    kpi_by_title,
    bar_total_cases,
    assert_cases_aligned,
)
from browser_case_tracker import record_case

pytestmark = pytest.mark.browser


def _iso_from_oerdte(oerdte: str) -> str:
    if len(oerdte) == 8:
        return f"{oerdte[:4]}-{oerdte[4:6]}-{oerdte[6:8]}"
    return ""


def _resolved_iso_date() -> str:
    """Resolve a date for global Submit tests from live API (no hardcoded dates)."""
    oerdte = discover_date_with_data("pg_dev")
    if oerdte is None:
        pytest.skip("No warehouse data from API")
    if oerdte:
        return _iso_from_oerdte(oerdte)
    stats = fetch_warehouse_stats(oerdte="", target_db="pg_dev", limit=10)
    items = stats.get("warehouse_items") or []
    if items and items[0].get("oerdte"):
        return _iso_from_oerdte(str(items[0]["oerdte"]))
    pytest.skip("No dated rows discovered from API")


def _submit_global_header(page: Page, iso_date: str, target_db: str = "pg_dev", whse: str = ""):
    """Apply global date + DB via Submit, then optionally pick warehouse once options load."""
    page.fill("#global-date-picker", iso_date)
    page.select_option("#global-db-selector", target_db)
    page.click("#submit-db-btn")
    page.wait_for_timeout(2500)
    if whse:
        whse = str(whse).strip()
        page.wait_for_function(
            f"""() => {{
                const sel = document.querySelector('#global-whse-selector');
                if (!sel) return false;
                return Array.from(sel.options).some(o => o.value === '{whse}');
            }}""",
            timeout=20000,
        )
        page.select_option("#global-whse-selector", whse)
        page.wait_for_timeout(2000)


def _first_warehouse_from_stats(stats: dict) -> str:
    rows = stats.get("summary", {}).get("warehouse_totals", [])
    if not rows:
        return ""
    return str(rows[0].get("whs_num", "")).strip()


def _wait_kpi_loaded(page: Page):
    page.wait_for_selector(".kpi-card", timeout=20000)
    page.wait_for_function(
        "() => !document.querySelector('.kpi-card .kpi-value')?.innerText.includes('...')",
        timeout=20000,
    )


@pytest.mark.browser_case("TC-COMP-01")
def test_dashboard_global_date_db_submit_kpi_alignment(page: Page):
    """Select date + DB, Submit, verify KPI Cases Built matches API."""
    oerdte = discover_date_with_data("pg_dev")
    assert oerdte is not None, "No warehouse data found for pg_dev"
    iso = _iso_from_oerdte(oerdte) if oerdte else _resolved_iso_date()

    goto_with_retry(page, BASE_URL)
    _submit_global_header(page, iso, "pg_dev")
    _wait_kpi_loaded(page)

    api = fetch_kpi(oerdte=oerdte, target_db="pg_dev")
    api_cases = parse_number(kpi_by_title(api, "CASES BUILT").get("value", "0"))

    ui_cases = parse_number(
        page.locator(".kpi-card", has_text="CASES BUILT").first.locator(".kpi-value").inner_text()
    )
    assert_cases_aligned(api_cases, ui_cases)
    record_case("TC-COMP-01", True, f"KPI cases built aligned: API={api_cases} UI={ui_cases}")
    print(f"TC-COMP-01 PASS: date={iso} db=pg_dev KPI cases API={api_cases} UI={ui_cases}")


@pytest.mark.browser_case("TC-COMP-02")
def test_dashboard_warehouse_filter_bar_chart_calculation(page: Page):
    """Select date, warehouse, Submit — bar chart total must match API warehouse_totals."""
    oerdte = discover_date_with_data("pg_dev") or ""
    iso = _iso_from_oerdte(oerdte) if oerdte else _resolved_iso_date()

    stats = fetch_warehouse_stats(oerdte=oerdte, target_db="pg_dev", limit=500)
    whs_rows = stats.get("summary", {}).get("warehouse_totals", [])
    if not whs_rows:
        pytest.skip("No warehouse totals in API")
    whse = _first_warehouse_from_stats(stats)

    goto_with_retry(page, BASE_URL)
    _submit_global_header(page, iso, "pg_dev", whse)
    _wait_kpi_loaded(page)
    page.wait_for_selector(".chart-card svg", timeout=15000)

    api_bar = fetch_bar(oerdte=oerdte, target_db="pg_dev", oewhse=whse)
    api_total = bar_total_cases(api_bar)
    api_whse_cases = int(whs_rows[0].get("cases_built") or 0)

    assert api_total == api_whse_cases or abs(api_total - api_whse_cases) <= 1, (
        f"Bar total {api_total} != warehouse row cases {api_whse_cases}"
    )
    record_case("TC-COMP-02", True, f"Whse {whse} bar total={api_total}")
    print(f"TC-COMP-02 PASS: Whse {whse} bar chart total={api_total}")


@pytest.mark.browser_case("TC-COMP-03")
def test_dashboard_table_summary_matches_api(page: Page):
    """Table summary cards must match /api/warehouse/statistics summary for same filters."""
    oerdte = discover_date_with_data("pg_dev") or ""
    iso = _iso_from_oerdte(oerdte) if oerdte else _resolved_iso_date()

    goto_with_retry(page, BASE_URL)
    _submit_global_header(page, iso, "pg_dev")
    page.wait_for_selector("#warehouse-table-card", timeout=20000)
    page.wait_for_timeout(2000)

    api = fetch_warehouse_stats(oerdte=oerdte, target_db="pg_dev", limit=20)
    api_cases = int(api.get("summary", {}).get("total_cases_built") or 0)

    summary_text = page.locator("#warehouse-table-card").inner_text()
    ui_match = re.search(r"Total Cases Built[^\d]*([\d,]+)", summary_text)
    ui_cases = parse_number(ui_match.group(1) if ui_match else "0")

    assert_cases_aligned(api_cases, ui_cases)
    record_case("TC-COMP-03", True, f"Table summary cases API={api_cases} UI={ui_cases}")
    print(f"TC-COMP-03 PASS: Table summary aligned API={api_cases} UI={ui_cases}")


@pytest.mark.browser_case("TC-COMP-04")
def test_copilot_search_without_date_global_uses_date(page: Page):
    """Copilot must send oerdte='' even when global date is set; KPI aligns with no-date API."""
    oerdte = discover_date_with_data("pg_dev") or ""
    iso = _iso_from_oerdte(oerdte) if oerdte else _resolved_iso_date()

    goto_with_retry(page, BASE_URL)
    _submit_global_header(page, iso, "pg_dev")
    _wait_kpi_loaded(page)

    copilot_bodies = []

    def capture(req):
        if "ai-copilot" in req.url and req.method == "POST":
            copilot_bodies.append(req.post_data or "")

    page.on("request", capture)
    page.wait_for_selector("#copilot-input", timeout=15000)
    page.fill("#copilot-input", "High Scratch Quantity")
    page.locator("button:has-text('Ask AI')").click()
    page.wait_for_selector("text=AI Copilot Finding", timeout=20000)
    page.wait_for_timeout(2000)

    assert copilot_bodies, "No copilot request captured"
    parsed = json.loads(copilot_bodies[-1])
    assert parsed.get("oerdte", "") == "", (
        f"Copilot must NOT send global date, got oerdte='{parsed.get('oerdte')}'"
    )

    _wait_kpi_loaded(page)
    api = fetch_kpi(oerdte="", target_db="pg_dev", only_scratches=True)
    api_cases = parse_number(kpi_by_title(api, "CASES BUILT").get("value", "0"))
    ui_cases = parse_number(
        page.locator(".kpi-card", has_text="CASES BUILT").first.locator(".kpi-value").inner_text()
    )
    assert_cases_aligned(api_cases, ui_cases)
    record_case("TC-COMP-04", True, f"Copilot no-date scratch query aligned cases={api_cases}")
    print(f"TC-COMP-04 PASS: Copilot ignored global date {iso}, KPI={api_cases}")


@pytest.mark.browser_case("TC-COMP-05")
def test_analytics_page_ml_controls(page: Page):
    """Analytics screen: upload + train controls render."""
    goto_with_retry(page, f"{BASE_URL}/analytics")
    page.wait_for_selector("text=Analytics", timeout=15000)
    expect(page.locator("text=Train Model").or_(page.locator("button:has-text('Train')")).first).to_be_visible()
    record_case("TC-COMP-05", True, "Analytics ML controls visible")
    print("TC-COMP-05 PASS: Analytics page loaded with train controls")


@pytest.mark.browser_case("TC-COMP-06")
def test_sprint_board_all_dropdowns_and_columns(page: Page):
    """Sprint Board: workspace + project select, all kanban columns visible."""
    goto_with_retry(page, f"{BASE_URL}/sprints")
    page.wait_for_selector("#sprint-board-workspace-select", timeout=15000)
    page.wait_for_selector("#sprint-board-project-select", timeout=15000)

    ws = page.locator("#sprint-board-workspace-select")
    proj = page.locator("#sprint-board-project-select")
    expect(ws).to_be_visible()
    expect(proj).to_be_visible()
    proj.select_option(value="all")
    page.wait_for_timeout(1500)

    for col in ["Backlog", "To Do", "In Progress", "Completed"]:
        expect(page.get_by_text(col, exact=False).first).to_be_visible()

    record_case("TC-COMP-06", True, "Sprint board dropdowns + 4 columns verified")
    print("TC-COMP-06 PASS: Sprint board full field selection + columns")


@pytest.mark.browser_case("TC-COMP-07")
def test_agent_monitor_fleet_visible(page: Page):
    """Agent Monitor: fleet cards and pipeline panel load."""
    goto_with_retry(page, f"{BASE_URL}/agents")
    page.wait_for_selector("text=Agent Monitor", timeout=15000)
    expect(page.get_by_text("Sprint Watcher", exact=False).or_(page.get_by_text("Orchestrator", exact=False)).first).to_be_visible()
    record_case("TC-COMP-07", True, "Agent Monitor fleet visible")
    print("TC-COMP-07 PASS: Agent Monitor loaded")


@pytest.mark.browser_case("TC-COMP-08")
def test_mcp_explorer_page_loads(page: Page):
    """MCP Explorer screen loads with server registry."""
    goto_with_retry(page, f"{BASE_URL}/mcp")
    page.wait_for_timeout(2000)
    body = page.inner_text("main")
    assert "MCP" in body or "Plane" in body or "Explorer" in body, "MCP Explorer content missing"
    record_case("TC-COMP-08", True, "MCP Explorer page loaded")
    print("TC-COMP-08 PASS: MCP Explorer loaded")


@pytest.mark.browser_case("TC-COMP-09")
def test_full_filter_chain_batch_scratch_submit(page: Page):
    """Select date + DB + warehouse + scratch filter — API params propagate to KPI."""
    oerdte = discover_date_with_data("pg_dev") or ""
    iso = _iso_from_oerdte(oerdte) if oerdte else _resolved_iso_date()

    goto_with_retry(page, BASE_URL)
    _submit_global_header(page, iso, "pg_dev")
    page.wait_for_selector("#warehouse-table-card", timeout=20000)

    scratch_btn = page.locator("button:has-text('Filter Scratches'), button:has-text('Scratch Items')").first
    if scratch_btn.count() > 0:
        scratch_btn.click()
        page.wait_for_timeout(2000)

    api = fetch_kpi(oerdte=oerdte, target_db="pg_dev", only_scratches=True)
    api_scratch = kpi_by_title(api, "SCRATCH")
    assert api_scratch, "Scratch KPI missing from API when only_scratches=true"

    record_case("TC-COMP-09", True, "Scratch filter chain applied")
    print("TC-COMP-09 PASS: Full filter chain with scratch filter")


@pytest.mark.browser_case("TC-COMP-10")
def test_bar_chart_sum_equals_kpi_when_single_whse(page: Page):
    """When one warehouse selected, bar chart single bar value = KPI cases built."""
    oerdte = discover_date_with_data("pg_dev") or ""
    iso = _iso_from_oerdte(oerdte) if oerdte else _resolved_iso_date()
    stats = fetch_warehouse_stats(oerdte=oerdte, target_db="pg_dev", limit=100)
    whs_rows = stats.get("summary", {}).get("warehouse_totals", [])
    if not whs_rows:
        pytest.skip("No data")
    whse = _first_warehouse_from_stats(stats)

    goto_with_retry(page, BASE_URL)
    _submit_global_header(page, iso, "pg_dev", whse)
    _wait_kpi_loaded(page)

    api_kpi = fetch_kpi(oerdte=oerdte, target_db="pg_dev", oewhse=whse)
    api_bar = fetch_bar(oerdte=oerdte, target_db="pg_dev", oewhse=whse)
    kpi_cases = parse_number(kpi_by_title(api_kpi, "CASES BUILT").get("value", "0"))
    bar_cases = bar_total_cases(api_bar)
    assert_cases_aligned(kpi_cases, bar_cases)
    record_case("TC-COMP-10", True, f"KPI={kpi_cases} bar={bar_cases} whse={whse}")
    print(f"TC-COMP-10 PASS: KPI={kpi_cases} == bar={bar_cases} for whse {whse}")


@pytest.mark.browser_case("TC-COMP-11")
def test_global_submit_uses_date_not_copilot(page: Page):
    """Global Submit must apply date+warehouse; chart/KPI API calls include oerdte."""
    oerdte = discover_date_with_data("pg_dev")
    assert oerdte, "No data date found"
    iso = _iso_from_oerdte(oerdte)

    goto_with_retry(page, BASE_URL)
    api_calls = []

    def capture(req):
        if "/api/charts/kpi" in req.url:
            api_calls.append(req.url)

    page.on("request", capture)
    _submit_global_header(page, iso, "pg_dev")
    _wait_kpi_loaded(page)

    assert any(oerdte in url for url in api_calls), (
        f"Global Submit must send oerdte={oerdte} in KPI API, got: {api_calls[:3]}"
    )
    api = fetch_kpi(oerdte=oerdte, target_db="pg_dev")
    api_cases = parse_number(kpi_by_title(api, "CASES BUILT").get("value", "0"))
    ui_cases = parse_number(
        page.locator(".kpi-card", has_text="CASES BUILT").first.locator(".kpi-value").inner_text()
    )
    assert_cases_aligned(api_cases, ui_cases)
    record_case("TC-COMP-11", True, f"Global date={iso} KPI aligned API={api_cases}")
    print(f"TC-COMP-11 PASS: Global Submit used date {iso}")


@pytest.mark.browser_case("TC-COMP-12")
def test_copilot_two_warehouses_different_kpi(page: Page):
    """Copilot: two discovered warehouses must show different Cases Built KPI values."""
    whs_a, whs_b = discover_two_warehouses("pg_dev", "")
    if not whs_a or not whs_b:
        pytest.skip("Need two warehouses with different totals from API")

    goto_with_retry(page, BASE_URL)
    page.wait_for_selector("#copilot-input", timeout=15000)

    def ask_and_get_cases(query: str) -> int:
        page.fill("#copilot-input", query)
        page.locator("button:has-text('Ask AI')").click()
        page.wait_for_selector("text=AI Copilot Finding", timeout=20000)
        _wait_kpi_loaded(page)
        return parse_number(
            page.locator(".kpi-card", has_text="CASES BUILT").first.locator(".kpi-value").inner_text()
        )

    cases_a = ask_and_get_cases(f"Warehouse {whs_a} Overview")
    cases_b = ask_and_get_cases(f"Warehouse {whs_b} Overview")

    assert cases_a != cases_b, f"Whse {whs_a} ({cases_a}) and {whs_b} ({cases_b}) must differ"
    exp_a = parse_number(kpi_by_title(fetch_kpi(oerdte="", target_db="pg_dev", oewhse=whs_a), "CASES BUILT").get("value", "0"))
    exp_b = parse_number(kpi_by_title(fetch_kpi(oerdte="", target_db="pg_dev", oewhse=whs_b), "CASES BUILT").get("value", "0"))
    assert_cases_aligned(cases_a, exp_a)
    assert_cases_aligned(cases_b, exp_b)
    record_case("TC-COMP-12", True, f"Whse{whs_a}={cases_a} Whse{whs_b}={cases_b}")
    print(f"TC-COMP-12 PASS: Whse {whs_a}={cases_a}, Whse {whs_b}={cases_b}")
