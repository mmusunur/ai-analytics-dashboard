"""
Dynamic Sprint Task Browser Tests — auto-generated from Plane sprint tasks.
Runs without user interaction as part of the full browser quality gate.
"""

import sys
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from playwright_helpers import goto_with_retry, BASE_URL

sys.path.insert(0, str(Path(__file__).parent.parent))
from sprint_task_test_generator import load_active_browser_cases, record_case_results


def _run_actions(page: Page, actions: list) -> None:
    for action in actions:
        kind = action.get("type")
        sel = action.get("selector", "")
        if kind == "click" and sel:
            page.locator(sel).first.click()
            page.wait_for_timeout(1200)
        elif kind == "select" and sel:
            page.select_option(sel, action.get("value", ""))
            page.wait_for_timeout(500)
        elif kind == "fill" and sel:
            page.locator(sel).fill(action.get("value", ""))


def pytest_generate_tests(metafunc):
    if "sprint_case" in metafunc.fixturenames:
        cases = load_active_browser_cases()
        if not cases:
            pytest.skip("No active sprint task test cases registered")
        ids = [c.get("case_id", "case") for c in cases]
        metafunc.parametrize("sprint_case", cases, ids=ids)


@pytest.fixture(scope="module", autouse=True)
def _collect_sprint_results(request):
    request.module._sprint_results = {}
    yield
    if getattr(request.module, "_sprint_results", None):
        record_case_results(request.module._sprint_results)


def test_sprint_task_browser_verification(page: Page, sprint_case, request):
    """Verify sprint task acceptance criteria in the browser (no user interaction)."""
    case_id = sprint_case["case_id"]
    url = sprint_case.get("url", BASE_URL)

    try:
        goto_with_retry(page, url)

        for action in sprint_case.get("actions", []):
            _run_actions(page, [action])

        for sel in sprint_case.get("must_be_visible", []):
            expect(page.locator(sel).first).to_be_visible(timeout=20000)

        for text in sprint_case.get("must_contain_text", []):
            expect(page.get_by_text(text, exact=False).first).to_be_visible(timeout=15000)

        for text in sprint_case.get("must_be_hidden_text", []):
            expect(page.get_by_text(text, exact=False)).to_have_count(0)

        request.module._sprint_results[case_id] = "PASS"
    except Exception:
        request.module._sprint_results[case_id] = "FAIL"
        raise
