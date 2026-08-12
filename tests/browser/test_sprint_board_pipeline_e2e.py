"""
Sprint Board pipeline E2E — column placement, refresh stability, step checkmarks, feature delivery.

Validates UX fixes from Task 45: active tasks in In Progress (not Backlog with stale badges),
page refresh does not go blank, prior pipeline steps show complete during Test, and
agent-delivered features are findable on the Dashboard.
"""

import json
import urllib.request

import pytest
from playwright.sync_api import Page, expect

from playwright_helpers import goto_with_retry, BASE_URL

API_BASE = "http://localhost:8000"


def _fetch_agent_status() -> dict:
    with urllib.request.urlopen(f"{API_BASE}/api/agents/status", timeout=10) as resp:
        return json.loads(resp.read().decode())


def _pipeline_live(status: dict) -> dict | None:
    pipeline = status.get("pipeline") or {}
    phase = pipeline.get("phase")
    task_id = pipeline.get("task_id")
    if task_id and phase and phase not in ("idle", "done", "failed"):
        return pipeline
    return None


@pytest.mark.browser_case("SB-PIPE-01")
def test_sprint_board_refresh_keeps_kanban_visible(page: Page):
    """Reload must not blank the Sprint Board — columns and pipeline tracker stay visible."""
    goto_with_retry(page, f"{BASE_URL}/sprints")
    page.wait_for_selector("#agent-pipeline-tracker", timeout=20000)
    expect(page.get_by_text("Backlog", exact=True).first).to_be_visible()
    expect(page.get_by_text("In Progress", exact=False).first).to_be_visible()

    page.reload()
    page.wait_for_selector("input[placeholder*='Search sprint tasks']", timeout=20000)

    expect(page.locator("h1")).to_be_visible()
    expect(page.locator("#agent-pipeline-tracker")).to_be_visible()
    expect(page.get_by_text("Backlog", exact=True).first).to_be_visible()
    expect(page.get_by_text("Completed", exact=True).first).to_be_visible()
    expect(page.locator("#sprint-board-loading")).to_have_count(0)


@pytest.mark.browser_case("SB-PIPE-02")
def test_pipeline_active_task_not_in_backlog_with_agent_done(page: Page):
    """Live pipeline task must appear in In Progress, not Backlog with a stale 'Agent done' badge."""
    status = _fetch_agent_status()
    live = _pipeline_live(status)
    if not live:
        pytest.skip("No live pipeline task — run during an active sprint")

    task_title = live.get("task_title") or ""
    if not task_title:
        pytest.skip("Pipeline has no task_title")

    goto_with_retry(page, f"{BASE_URL}/sprints")
    page.wait_for_selector("#agent-pipeline-tracker", timeout=20000)

    backlog = page.locator('[data-testid="sprint-column-backlog"]')
    in_progress = page.locator('[data-testid="sprint-column-in-progress"]')

    expect(backlog.get_by_text("✓ Agent done", exact=False)).to_have_count(0)
    expect(backlog.get_by_text(task_title, exact=False)).to_have_count(0)
    expect(in_progress.get_by_text(task_title, exact=False).first).to_be_visible(timeout=15000)


@pytest.mark.browser_case("SB-PIPE-03")
def test_pipeline_prior_steps_complete_during_testing(page: Page):
    """During Test phase, Pickup and Build steps must show as complete (not empty circles)."""
    status = _fetch_agent_status()
    live = _pipeline_live(status)
    if not live or live.get("phase") != "testing":
        pytest.skip("Pipeline not in testing phase")

    goto_with_retry(page, f"{BASE_URL}/sprints")
    page.wait_for_selector("#agent-pipeline-tracker", timeout=20000)

    pickup = page.locator('[data-testid="pipeline-step-pickup"]')
    build = page.locator('[data-testid="pipeline-step-building"]')
    testing = page.locator('[data-testid="pipeline-step-testing"]')

    expect(pickup).to_have_attribute("data-step-complete", "true")
    expect(build).to_have_attribute("data-step-complete", "true")
    expect(testing).to_have_attribute("data-step-complete", "false")


@pytest.mark.browser_case("SB-PIPE-04")
def test_delivery_notice_and_dashboard_feature_panel(page: Page):
    """Agent-delivered feature must be reachable: delivery notice → Dashboard panel."""
    status = _fetch_agent_status()
    pipeline = status.get("pipeline") or {}
    guide = pipeline.get("build_usage_guide") or {}
    if not guide.get("headline"):
        completed = (status.get("task_queue") or {}).get("completed") or []
        for entry in completed:
            if entry.get("delivery_guide", {}).get("headline"):
                guide = entry["delivery_guide"]
                break
    if not guide.get("headline"):
        pytest.skip("No delivery guide in agent state")

    goto_with_retry(page, f"{BASE_URL}/sprints")
    page.wait_for_selector("#agent-pipeline-tracker", timeout=20000)

    notice = page.locator("#task-delivery-notice")
    if notice.count() > 0:
        expect(notice).to_be_visible()
        notice.get_by_role("link", name=guide.get("route_label", "Open Dashboard")).click()
    else:
        goto_with_retry(page, f"{BASE_URL}/")

    page.wait_for_selector("#data-analytics-panel", timeout=20000)
    expect(page.locator("#data-analytics-panel")).to_be_visible()
    expect(page.get_by_text("Data Analytics", exact=False).first).to_be_visible()


@pytest.mark.browser_case("SB-PIPE-05")
def test_in_progress_column_shows_phase_badge_not_agent_done(page: Page):
    """In Progress cards for live tasks show phase badge (testing/building), not 'Agent done'."""
    status = _fetch_agent_status()
    live = _pipeline_live(status)
    if not live:
        pytest.skip("No live pipeline task")

    task_title = live.get("task_title") or ""
    goto_with_retry(page, f"{BASE_URL}/sprints")
    page.wait_for_selector('[data-testid="sprint-column-in-progress"]', timeout=20000)

    col = page.locator('[data-testid="sprint-column-in-progress"]')
    expect(col.get_by_text(task_title, exact=False).first).to_be_visible()
    expect(col.get_by_text("✓ Agent done", exact=False)).to_have_count(0)
    expect(col.get_by_text("⚡", exact=False).first).to_be_visible()
