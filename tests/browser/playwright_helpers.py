"""Playwright navigation helpers for browser tests."""

import time
from playwright.sync_api import Page

BASE_URL = "http://localhost:5173"


def goto_with_retry(page: Page, url: str, retries: int = 3, wait_until: str = "load") -> None:
    """Navigate with retries — handles transient ERR_NETWORK_CHANGED after Vite restarts."""
    last_error = None
    for attempt in range(retries):
        try:
            page.goto(url, wait_until=wait_until)
            return
        except Exception as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(2)
    raise last_error
