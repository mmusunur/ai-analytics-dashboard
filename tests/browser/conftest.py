"""Shared Playwright fixtures for browser tests."""

import sys
from pathlib import Path

import pytest

# Allow `from playwright_helpers import ...` in browser test modules
sys.path.insert(0, str(Path(__file__).resolve().parent))

BASE_URL = "http://localhost:5173"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 1440, "height": 900},
    }
