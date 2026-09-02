"""Shared Playwright fixtures and browser case tracking hooks."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from browser_case_tracker import record_case, sync_excel_from_registry

BASE_URL = "http://localhost:5173"


def pytest_configure(config):
    config.addinivalue_line("markers", "browser_case(id): track case ID for TEST_CASES.xlsx")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 1440, "height": 900},
    }


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    marker = item.get_closest_marker("browser_case")
    if marker and rep.when == "call":
        case_id = marker.args[0]
        if rep.passed:
            record_case(case_id, True, "PASS")
        elif rep.failed:
            msg = str(rep.longrepr)[:500] if rep.longrepr else "FAIL"
            record_case(case_id, False, msg)


def pytest_sessionfinish(session, exitstatus):
    """After browser suite, refresh TEST_CASES.xlsx with per-case statuses."""
    if any("browser" in str(arg) for arg in (session.config.args or [])):
        try:
            sync_excel_from_registry()
        except Exception:
            pass
