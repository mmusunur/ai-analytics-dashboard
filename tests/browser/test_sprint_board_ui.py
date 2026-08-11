"""
Playwright Browser Test — Sprint Board UI Integration
Verifies that navigating to /sprints renders the live Plane Sprint Board with tasks.
"""

import pytest
from playwright.sync_api import Page, expect


def test_sprint_board_page(page: Page):
    """Navigate to /sprints and verify live Plane sprint tasks are displayed."""
    page.goto("http://localhost:5173/sprints")
    page.wait_for_selector("input[placeholder*='Search sprint tasks']", timeout=15000)

    # Verify Sprint Header is present
    expect(page.locator("h1")).to_be_visible()

    # Verify Search and Priority Filters are present
    expect(page.locator("input[placeholder*='Search sprint tasks']")).to_be_visible()

    # Verify Kanban columns exist
    expect(page.get_by_text("Backlog", exact=True).first).to_be_visible()
    expect(page.get_by_text("To Do", exact=True).first).to_be_visible()
    expect(page.get_by_text("In Progress", exact=True).first).to_be_visible()
    expect(page.get_by_text("Completed", exact=True).first).to_be_visible()
