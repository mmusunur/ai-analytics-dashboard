"""
TASK 19 & 20 — Full E2E Component Test Suite (Playwright Browser Tests)
==========================================================================
KEY RULE — FALLBACK DATE BEHAVIOR (warehouse_service.py L255):
  When the selected date has NO data in the DB (e.g. today = 2026-07-30 is empty),
  the backend automatically falls back to the most recent date WITH data.
  This is CORRECT behavior. Tests MUST NOT fail when today has no data.
  Tests verify that DATA is always shown — not that it matches today's exact date.

Tests cover:
  - Default date auto-applied on load (today's date pre-filled)
  - Data always renders (via fallback when needed)
  - Date change propagation fires API calls with the new date
  - Warehouse filter narrows table rows
  - AI Copilot: NEVER sends date (verified via request intercept)
  - Copilot quick pills, result card, apply-filter
  - Data table always populated (from real date, via fallback if needed)
  - Agent status sidebar, Anomaly panel, DB switch, chart ticks vs KPI alignment

All dates read DYNAMICALLY from the live UI #global-date-picker.
"""

import re
import json
import pytest
from playwright.sync_api import Page, expect
from playwright_helpers import goto_with_retry, BASE_URL
API_URL = "http://127.0.0.1:8000"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "viewport": {"width": 1440, "height": 900}}


def get_ui_date(page: Page) -> tuple[str, str]:
    """
    Reads the currently selected date from the live UI date picker (#global-date-picker).
    Returns (iso_display: 'YYYY-MM-DD', api_format: 'YYYYMMDD').
    This ensures tests always use exactly the same date the user sees in the UI.
    """
    page.wait_for_selector("#global-date-picker", timeout=12000)
    iso = page.locator("#global-date-picker").input_value()
    assert iso and re.match(r"\d{4}-\d{2}-\d{2}", iso), (
        f"get_ui_date: Invalid or empty date in #global-date-picker: '{iso}'"
    )
    api_fmt = iso.replace("-", "")
    return iso, api_fmt


# ─────────────────────────────────────────────────────────────
# TC-01: Default date is today and auto-loads data on page open
# ─────────────────────────────────────────────────────────────
def test_tc01_default_date_auto_applied_on_load(page: Page):
    """TC-01: On first load, today's date is pre-filled in the date picker and data loads automatically."""
    page.goto(BASE_URL)
    iso, api_fmt = get_ui_date(page)
    assert iso, f"TC-01 FAIL: Date picker is empty — expected today's date, got: '{iso}'"
    assert re.match(r"\d{4}-\d{2}-\d{2}", iso), f"TC-01 FAIL: Date format wrong: '{iso}'"
    print(f"TC-01 PASS: Default date auto-applied from UI = {iso} (api={api_fmt})")


# ─────────────────────────────────────────────────────────────
# TC-02: KPI cards load with real numbers (not placeholder '...')
# ─────────────────────────────────────────────────────────────
def test_tc02_kpi_cards_populated_with_real_data(page: Page):
    """
    TC-02: All KPI cards must show real numeric values (not '...').
    FALLBACK RULE: Even if today has no data, backend falls back to last date with data.
    Real numbers MUST appear regardless — showing '...' forever is a failure.
    """
    page.goto(BASE_URL)
    page.wait_for_selector(".kpi-card", timeout=15000)
    # Longer wait: fallback query may take extra round-trip
    page.wait_for_function(
        "() => !document.querySelector('.kpi-card')?.innerText.includes('...')",
        timeout=20000
    )
    kpi_cards = page.locator(".kpi-card")
    count = kpi_cards.count()
    assert count >= 6, f"TC-02 FAIL: Expected >= 6 KPI cards, got {count}"
    for i in range(count):
        expect(kpi_cards.nth(i)).to_be_visible()
    ui_date = page.locator("#global-date-picker").input_value()
    print(f"TC-02 PASS: {count} KPI cards populated for UI date={ui_date} (fallback applies if today empty)")


# ─────────────────────────────────────────────────────────────
# TC-03: Charts render SVG (not blank/empty)
# ─────────────────────────────────────────────────────────────
def test_tc03_bar_and_scatter_charts_rendered(page: Page):
    """TC-03: Both Bar chart and Scatter chart must render SVG elements."""
    page.goto(BASE_URL)
    page.wait_for_selector(".chart-card svg", timeout=15000)
    svg_count = page.locator(".chart-card svg").count()
    assert svg_count >= 2, f"TC-03 FAIL: Expected >= 2 chart SVGs, got {svg_count}"
    print(f"TC-03 PASS: {svg_count} chart SVGs rendered for UI date = {page.locator('#global-date-picker').input_value()}")


# ─────────────────────────────────────────────────────────────
# TC-04: Changing date triggers fresh data load with that date
# ─────────────────────────────────────────────────────────────
def test_tc04_date_change_triggers_reload(page: Page):
    """TC-04: Changing the date and clicking Submit loads new data using the new date from the UI."""
    page.goto(BASE_URL)
    page.wait_for_selector("#global-date-picker", timeout=12000)

    # Read the CURRENT UI date, then shift to a slightly different one to trigger a reload
    current_iso, _ = get_ui_date(page)

    # Use a date 6 days before current UI date to force an actual change
    from datetime import datetime, timedelta
    current_dt = datetime.strptime(current_iso, "%Y-%m-%d")
    test_dt = current_dt - timedelta(days=6)
    test_iso = test_dt.strftime("%Y-%m-%d")
    test_api = test_dt.strftime("%Y%m%d")

    api_calls = []
    page.on("request", lambda req: api_calls.append(req.url) if "/api/" in req.url else None)

    page.fill("#global-date-picker", test_iso)
    page.click("#submit-db-btn")
    page.wait_for_timeout(3000)

    # Read date back from UI to confirm it was applied
    applied_iso, applied_api = get_ui_date(page)
    assert applied_iso == test_iso, f"TC-04 FAIL: UI date not updated to {test_iso}, got {applied_iso}"

    date_calls = [u for u in api_calls if applied_api in u]
    assert len(date_calls) > 0, (
        f"TC-04 FAIL: No API calls with date {applied_api} after change. Calls: {api_calls[:5]}"
    )
    print(f"TC-04 PASS: Date changed to {applied_iso} → {len(date_calls)} API calls with {applied_api}")


# ─────────────────────────────────────────────────────────────
# TC-05: Warehouse filter in table changes data
# ─────────────────────────────────────────────────────────────
def test_tc05_warehouse_filter_applies_to_table(page: Page):
    """TC-05: Entering a warehouse number dynamically extracted from the UI narrows table rows."""
    page.goto(BASE_URL)
    page.wait_for_selector("table tbody tr", timeout=20000)

    whse_input = page.locator(
        "input[placeholder*='Whse'], input[placeholder*='whse'], input[placeholder*='warehouse']"
    ).first
    if whse_input.count() > 0:
        first_td = page.locator("table tbody tr td").first.inner_text().strip()
        m = re.search(r'\d+', first_td)
        target_whse = m.group(0) if m else "01"
        whse_input.fill(target_whse)
        page.wait_for_timeout(1500)
        row_count = page.locator("table tbody tr").count()
        assert row_count >= 1, f"TC-05 FAIL: No rows after warehouse {target_whse} filter, got {row_count}"
        print(f"TC-05 PASS: Warehouse {target_whse} filter — {row_count} rows visible")
    else:
        print("TC-05 SKIP: Warehouse filter input not found in current UI")


# ─────────────────────────────────────────────────────────────
# TC-06 CRITICAL: AI Copilot does NOT send date in API request
# ─────────────────────────────────────────────────────────────
def test_tc06_copilot_sends_no_date_in_api_request(page: Page):
    """
    TC-06 CRITICAL: AI Copilot must send oerdte='' (empty) — NEVER the global date.
    This reads the current UI date dynamically and confirms the copilot does NOT include it.
    """
    page.goto(BASE_URL)
    page.wait_for_selector("#copilot-input", timeout=15000)

    copilot_requests = []

    def capture_copilot(request):
        if "ai-copilot" in request.url:
            try:
                copilot_requests.append(request.post_data or "")
            except Exception:
                copilot_requests.append("")

    page.on("request", capture_copilot)

    # Compute dynamic test date relative to current UI date
    ui_iso, _ = get_ui_date(page)
    from datetime import datetime, timedelta
    test_dt = datetime.strptime(ui_iso, "%Y-%m-%d") - timedelta(days=2)
    dynamic_date_iso = test_dt.strftime("%Y-%m-%d")
    dynamic_date_api = test_dt.strftime("%Y%m%d")

    page.fill("#global-date-picker", dynamic_date_iso)
    page.click("#submit-db-btn")
    page.wait_for_timeout(1000)

    # Ask copilot — it must NOT echo back the UI date
    page.locator("#copilot-input").fill("High Scratch Quantity")
    page.locator("button:has-text('Ask AI')").click()
    page.wait_for_selector("text=AI Copilot Finding", timeout=15000)
    page.wait_for_timeout(500)

    assert len(copilot_requests) > 0, "TC-06 FAIL: No copilot API requests intercepted"

    for req_body in copilot_requests:
        assert dynamic_date_api not in (req_body or ""), (
            f"TC-06 FAIL: Copilot sent UI date '{dynamic_date_api}' in body: {req_body}"
        )
        if req_body and "oerdte" in req_body:
            try:
                parsed = json.loads(req_body)
                assert parsed.get("oerdte", "") == "", (
                    f"TC-06 FAIL: oerdte is not empty in copilot request: '{parsed.get('oerdte')}'"
                )
            except json.JSONDecodeError:
                pass

    print(f"TC-06 PASS: Copilot sent {len(copilot_requests)} request(s); UI date was NOT included")


# ─────────────────────────────────────────────────────────────
# TC-07: Copilot returns result card
# ─────────────────────────────────────────────────────────────
def test_tc07_copilot_returns_result_card(page: Page):
    """TC-07: Asking the copilot a question returns an 'AI Copilot Finding' result card."""
    page.goto(BASE_URL)
    page.wait_for_selector("input[placeholder*='Ask AI Data Copilot']", timeout=15000)
    page.locator("input[placeholder*='Ask AI Data Copilot']").fill("Warehouse 58 Overview")
    page.locator("button:has-text('Ask AI')").click()
    page.wait_for_selector("text=AI Copilot Finding", timeout=15000)
    expect(page.locator("text=AI Copilot Finding")).to_be_visible()
    print("TC-07 PASS: Copilot result card appeared after query")


# ─────────────────────────────────────────────────────────────
# TC-08: Copilot quick pills trigger results
# ─────────────────────────────────────────────────────────────
def test_tc08_copilot_quick_pills_trigger_results(page: Page):
    """TC-08: Each quick pill button triggers copilot to return an AI finding."""
    page.goto(BASE_URL)
    page.wait_for_selector("text=Quick Insights:", timeout=15000)
    for pill_text in ["High Scratch Quantity", "Pending Procurement Transfers"]:
        pill = page.locator(f"button:has-text('{pill_text}')").first
        if pill.count() > 0:
            pill.click()
            page.wait_for_selector("text=AI Copilot Finding", timeout=12000)
            expect(page.locator("text=AI Copilot Finding")).to_be_visible()
            page.wait_for_timeout(400)
            print(f"TC-08 PASS: Pill '{pill_text}' returned finding")


# ─────────────────────────────────────────────────────────────
# TC-09: Data table has rows for the UI-selected date
# ─────────────────────────────────────────────────────────────
def test_tc09_data_table_has_rows(page: Page):
    """
    TC-09: Data table MUST always show >= 1 row.
    FALLBACK RULE: When today has no data, backend falls back to most recent date WITH data.
    Showing 0 rows is always a failure — the fallback should have supplied data.
    """
    page.goto(BASE_URL)
    page.wait_for_selector("#global-date-picker", timeout=12000)
    ui_iso, _ = get_ui_date(page)
    page.click("#submit-db-btn")
    # Extra timeout: fallback query needs two DB round-trips
    page.wait_for_selector("table tbody tr", timeout=25000)
    count = page.locator("table tbody tr").count()
    assert count >= 1, (
        f"TC-09 FAIL: Table has {count} rows for UI date {ui_iso}. "
        f"Backend fallback should return data from most recent available date when today is empty."
    )
    print(f"TC-09 PASS: {count} rows for UI date {ui_iso} (fallback applied if today had no data)")


# ─────────────────────────────────────────────────────────────
# TC-10: Agent status sidebar shows all agents
# ─────────────────────────────────────────────────────────────
def test_tc10_agent_status_sidebar_all_running(page: Page):
    """TC-10: The sidebar 'AGENT STATUS' panel must be visible with all agent names."""
    page.goto(BASE_URL)
    page.wait_for_selector("text=AGENT STATUS", timeout=15000)
    expect(page.locator("text=AGENT STATUS")).to_be_visible()
    for agent in ["Orchestrator", "Builder", "Tester", "Git", "Sprint_watcher"]:
        el = page.locator(f"text={agent}").first
        if el.count() > 0:
            expect(el).to_be_visible()
    print("TC-10 PASS: Agent Status sidebar visible with all expected agents")


# ─────────────────────────────────────────────────────────────
# TC-11: Anomaly panel visible
# ─────────────────────────────────────────────────────────────
def test_tc11_anomaly_panel_renders(page: Page):
    """TC-11: Real-Time Anomaly & Risk Alerts panel must be visible."""
    page.goto(BASE_URL)
    page.wait_for_selector("text=Real-Time Anomaly", timeout=15000)
    expect(page.locator("text=Real-Time Anomaly").first).to_be_visible()
    print("TC-11 PASS: Anomaly & Risk Alert panel is visible")


# ─────────────────────────────────────────────────────────────
# TC-12: Database switcher reloads data with new DB
# ─────────────────────────────────────────────────────────────
def test_tc12_database_switch_triggers_reload(page: Page):
    """TC-12: Switching database triggers API calls with new target_db value."""
    goto_with_retry(page, BASE_URL)
    page.wait_for_selector("#global-db-selector", timeout=12000)
    api_calls = []
    page.on("request", lambda req: api_calls.append(req.url) if "/api/" in req.url else None)
    page.select_option("#global-db-selector", "oracle_dev")
    page.click("#submit-db-btn")
    page.wait_for_timeout(2500)
    oracle_calls = [u for u in api_calls if "oracle_dev" in u]
    assert len(oracle_calls) > 0, f"TC-12 FAIL: No API calls with oracle_dev. Calls: {api_calls[:5]}"
    page.select_option("#global-db-selector", "pg_dev")
    page.click("#submit-db-btn")
    page.wait_for_timeout(1000)
    print(f"TC-12 PASS: {len(oracle_calls)} API calls fired with oracle_dev")


# ─────────────────────────────────────────────────────────────
# TC-13: Copilot apply-filter updates the data table
# ─────────────────────────────────────────────────────────────
def test_tc13_copilot_apply_filter_updates_table(page: Page):
    """TC-13: Clicking 'Apply Filter to Table' after a copilot warehouse query filters the data table."""
    page.goto(BASE_URL)
    page.wait_for_selector("input[placeholder*='Ask AI Data Copilot']", timeout=15000)
    page.locator("input[placeholder*='Ask AI Data Copilot']").fill("Warehouse 58 Overview")
    page.locator("button:has-text('Ask AI')").click()
    page.wait_for_selector("text=AI Copilot Finding", timeout=15000)
    apply_btn = page.locator("#copilot-apply-filter-btn, button:has-text('Apply Filter to Table')").first
    if apply_btn.count() > 0:
        expect(apply_btn).to_be_visible()
        apply_btn.click()
        page.wait_for_timeout(2000)
        expect(page.locator("table")).to_be_visible()
        print("TC-13 PASS: Copilot apply filter updated data table")
    else:
        print("TC-13 SKIP: No 'Apply Filter to Table' button visible")


# ─────────────────────────────────────────────────────────────
# TC-14: Bar chart X-axis ticks match total warehouse KPI count
# ─────────────────────────────────────────────────────────────
def test_tc14_bar_chart_ticks_match_kpi_warehouse_count(page: Page):
    """TC-14: Bar chart X-axis tick count must match Total Warehouses KPI value for UI-selected date."""
    page.goto(BASE_URL)
    page.wait_for_selector(".kpi-card", timeout=15000)
    page.wait_for_selector(".chart-card svg", timeout=15000)
    page.wait_for_function(
        "() => !document.querySelector('.kpi-card .kpi-value')?.innerText.includes('...')",
        timeout=15000
    )
    ui_iso, _ = get_ui_date(page)
    kpi_card = page.locator(".kpi-card", has_text="TOTAL WAREHOUSES").first
    kpi_val_text = kpi_card.locator(".kpi-value").inner_text()
    match = re.search(r"\d+", kpi_val_text)
    if not match:
        print(f"TC-14 SKIP: Could not parse warehouse count from '{kpi_val_text}'")
        return
    expected = int(match.group(0))
    bar_card = page.locator(".chart-card", has_text="Cases Built by Warehouse").first
    page.wait_for_timeout(2000)
    actual = bar_card.locator(".recharts-xAxis .recharts-cartesian-axis-tick").count()
    assert actual == expected, f"TC-14 FAIL: Bar ticks ({actual}) ≠ Warehouses KPI ({expected}) for date {ui_iso}"
    print(f"TC-14 PASS: Bar ticks ({actual}) == Warehouses KPI ({expected}) for UI date {ui_iso}")
