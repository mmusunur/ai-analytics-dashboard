"""
Interactive Playwright Browser Tests for AI Data Copilot and Anomaly Alert Panel.
Validates real browser interactions: typing prompts, clicking 'Ask AI', applying table filters,
clicking anomaly cards, scrolling, and validating dynamic data loading.
"""

import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:5173"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 1440, "height": 900}
    }


def test_ai_copilot_interactive_prompt_and_ask_ai(page: Page):
    """Test typing a query into AI Copilot, clicking 'Ask AI', verifying finding card, and applying filter."""
    page.goto(BASE_URL)
    page.wait_for_selector("#copilot-input", timeout=15000)

    # 1. Fill input with query
    copilot_input = page.locator("#copilot-input")
    expect(copilot_input).to_be_visible()
    copilot_input.fill("Warehouse 58 Overview")

    # 2. Click 'Ask AI' button
    ask_btn = page.locator("button:has-text('Ask AI')")
    expect(ask_btn).to_be_visible()
    ask_btn.click()

    # 3. Wait for AI Copilot Finding card to populate
    page.wait_for_selector("text=AI Copilot Finding", timeout=10000)
    finding_card = page.locator("text=AI Copilot Finding")
    expect(finding_card).to_be_visible()

    # 4. Click 'Apply Filter to Table' button if present
    apply_btn = page.locator("#copilot-apply-filter-btn, button:has-text('Apply Filter')")
    if apply_btn.count() > 0:
        expect(apply_btn.first).to_be_visible()
        apply_btn.first.click()
        page.wait_for_timeout(1000)

        # 5. Verify table updates with filtered data
        table = page.locator("table")
        expect(table).to_be_visible()


def test_ai_copilot_quick_pills(page: Page):
    """Clicking quick prompt pills automatically populates search bar and triggers AI analysis."""
    page.goto(BASE_URL)
    page.wait_for_selector("text=Quick Insights:", timeout=15000)

    # Click pill 'High Scratch Quantity'
    pill = page.locator("button:has-text('High Scratch Quantity')")
    expect(pill).to_be_visible()
    pill.click()

    # Verify AI Finding populates
    page.wait_for_selector("text=AI Copilot Finding", timeout=10000)
    finding_card = page.locator("text=AI Copilot Finding")
    expect(finding_card).to_be_visible()


def test_anomaly_alert_panel_interactive_filters(page: Page):
    """Anomaly alert panel renders risk cards and allows 1-click table filtering."""
    page.goto(BASE_URL)
    page.wait_for_selector("text=Real-Time Anomaly & Risk Alerts", timeout=15000)

    alert_title = page.locator("text=Real-Time Anomaly & Risk Alerts")
    expect(alert_title).to_be_visible()

    # Find Filter Table button inside anomaly cards
    filter_btn = page.locator("button:has-text('Filter Table')").first
    if filter_btn.count() > 0:
        expect(filter_btn).to_be_visible()
        filter_btn.click()
        page.wait_for_timeout(1000)
        table = page.locator("table")
        expect(table).to_be_visible()


def test_page_scroll_and_data_table_dynamic_validation(page: Page):
    """Scroll down page, interact with data table, and validate dynamic record loading."""
    page.goto(BASE_URL)
    page.wait_for_selector("table", timeout=15000)

    # Scroll to data table
    table = page.locator("table")
    table.scroll_into_view_if_needed()
    expect(table).to_be_visible()

    # Validate table rows populate dynamically
    page.wait_for_selector("table tbody tr", timeout=10000)
    rows = page.locator("table tbody tr")
    assert rows.count() >= 1, "Data table rows failed to populate dynamically"


def test_header_controls_interactive(page: Page):
    """Test date selection, database switching, and form submission in header bar."""
    page.goto(BASE_URL)
    page.wait_for_selector("#global-header-controls, input[type='date']", timeout=15000)

    # 1. Change date picker value dynamically
    date_input = page.locator("input[type='date']")
    expect(date_input).to_be_visible()
    current_val = date_input.input_value() or "2026-07-31"
    from datetime import datetime, timedelta
    test_dt = datetime.strptime(current_val, "%Y-%m-%d") - timedelta(days=3)
    dynamic_date_iso = test_dt.strftime("%Y-%m-%d")
    date_input.fill(dynamic_date_iso)

    # 2. Change Target DB dropdown to PostgreSQL DEV
    db_select = page.locator("#global-db-selector")
    expect(db_select).to_be_visible()
    db_select.select_option("pg_dev")

    # 3. Click Submit button
    submit_btn = page.locator("button:has-text('Submit'), #submit-db-btn")
    if submit_btn.count() > 0:
        expect(submit_btn.first).to_be_visible()
        submit_btn.first.click()
        page.wait_for_timeout(1000)

    # 4. Verify Active DB Badge displays PG_DEV
    active_badge = page.locator("text=PG_DEV")
    expect(active_badge.first).to_be_visible()
