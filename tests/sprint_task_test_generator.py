"""
Sprint Task Test Case Generator — dynamically creates browser test cases and Excel rows
from Plane sprint task title, description, and matching tasks/*.md specifications.
No user interaction required; invoked automatically by tester_agent / sprint_watcher.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).parent.parent
REGISTRY_PATH = ROOT_DIR / "memory" / "sprint_test_registry.json"
TASKS_DIR = ROOT_DIR / "tasks"

BASE_URL = "http://localhost:5173"


def _short_id(task_id: str) -> str:
    return (task_id or "unknown")[:8].upper()


def _load_task_spec_snippets(task_title: str, description: str) -> str:
    keywords = [w.lower() for w in re.findall(r"[a-zA-Z]{4,}", f"{task_title} {description}")][:10]
    if not keywords or not TASKS_DIR.exists():
        return ""
    chunks: list[str] = []
    for md in sorted(TASKS_DIR.glob("*.md")):
        try:
            text = md.read_text(encoding="utf-8")
            if any(kw in text.lower() for kw in keywords):
                chunks.append(text[:1500])
        except OSError:
            pass
    return "\n".join(chunks[:2])


def _match_patterns(text: str, patterns: list[str]) -> bool:
    t = text.lower()
    return any(p in t for p in patterns)


def _build_cases_for_task(
    task_id: str,
    task_title: str,
    description: str,
    project_name: str = "",
) -> list[dict[str, Any]]:
    """Rule-based browser verification cases derived from sprint task content."""
    combined = f"{task_title} {description}".lower()
    spec = _load_task_spec_snippets(task_title, description)
    if spec:
        combined = f"{combined} {spec.lower()}"

    tid = _short_id(task_id)
    cases: list[dict[str, Any]] = []

    def add(suffix: str, name: str, area: str, expected: str, **browser: Any) -> None:
        cases.append({
            "case_id": f"TC-TASK-{tid}-{suffix}",
            "task_id": task_id,
            "task_title": task_title,
            "project_name": project_name,
            "name": name,
            "functionality": area,
            "expected": expected,
            "url": browser.get("url", BASE_URL),
            "must_be_visible": browser.get("must_be_visible", []),
            "must_be_hidden_text": browser.get("must_be_hidden_text", []),
            "must_contain_text": browser.get("must_contain_text", []),
            "actions": browser.get("actions", []),
        })

    add(
        "SMOKE",
        f"Dashboard smoke after sprint task: {task_title[:60]}",
        "Sprint Task Regression Smoke Test",
        f"After implementing the sprint task '{task_title}', the main dashboard loads with KPI cards and global header controls working.",
        must_be_visible=[".kpi-card", "#global-date-picker", "#global-db-selector", "#submit-db-btn"],
    )

    if _match_patterns(combined, [
        "remove unwanted", "hide items", "hide unwanted", "copilot search fixes",
        "warehouse level statistics", "agent monitor", "agent task activity",
    ]):
        add(
            "HIDE-UI",
            "Unwanted dashboard widgets remain hidden",
            "Remove Unwanted Content Task Verification",
            "The dashboard will not show Copilot Search Fixes, Warehouse Level Statistics, or Agent Task Activity Tracker widgets.",
            must_be_visible=[".kpi-card", "#global-db-selector"],
            must_be_hidden_text=[
                "Copilot Search Fixes",
                "Warehouse Level Statistics",
                "Agent Task Activity Tracker",
            ],
        )

    if _match_patterns(combined, ["sprint board", "kanban", "plane sprint", "workspace select"]):
        add(
            "SPRINT-UI",
            "Sprint board page loads with workspace and project selectors",
            "Sprint Board Browser Verification",
            "The Sprint Board page displays workspace and project dropdowns and kanban column headers.",
            url=f"{BASE_URL}/sprints",
            must_be_visible=[
                "select#sprint-board-workspace-select",
                "select#sprint-board-project-select",
                "h1",
            ],
            must_contain_text=["Backlog", "To Do"],
        )

    if _match_patterns(combined, ["copilot", "ai data", "natural language", "ask ai"]):
        add(
            "COPILOT",
            "AI Data Copilot accepts prompts and shows results",
            "AI Data Copilot Sprint Task Verification",
            "The AI Data Copilot search box and Ask AI control are visible and a quick insight pill triggers an analysis result card.",
            must_be_visible=["#copilot-input", "button:has-text('Ask AI')", "text=Quick Insights:"],
            actions=[{"type": "click", "selector": "button:has-text('High Scratch Quantity')"}],
            must_contain_text=["AI Copilot Finding"],
        )

    if _match_patterns(combined, ["warehouse", "data table", "invoice", "statistics", "table row"]):
        add(
            "TABLE",
            "Warehouse sales table loads with data rows",
            "Warehouse Analytics Table Verification",
            "Selecting the development database and submitting loads the warehouse item table with visible rows.",
            actions=[
                {"type": "select", "selector": "#global-db-selector", "value": "pg_dev"},
                {"type": "click", "selector": "#submit-db-btn"},
            ],
            must_be_visible=["table", "#warehouse-analytics-table"],
        )

    if _match_patterns(combined, ["clear filter", "header control", "global date", "submit"]):
        add(
            "HEADER",
            "Global header controls and clear filter work",
            "Header Controls Sprint Task Verification",
            "Global date picker, database selector, submit button, and clear filter control are visible on the dashboard.",
            must_be_visible=[
                "#global-date-picker",
                "#global-db-selector",
                "#submit-db-btn",
                "#header-clear-filter-btn",
            ],
            actions=[{"type": "click", "selector": "button:has-text('High Scratch Quantity')"}],
        )

    if _match_patterns(combined, ["agent monitor", "agent status", "agent fleet", "telemetry"]):
        add(
            "AGENTS",
            "Agent status telemetry visible in sidebar",
            "Agent Fleet Monitoring Verification",
            "The dashboard sidebar shows agent status information for the autonomous agent fleet.",
            must_be_visible=[".sidebar", "text=AGENT STATUS"],
        )

    if _match_patterns(combined, ["anomaly", "risk alert", "scratch rate"]):
        add(
            "ANOMALY",
            "Real-time anomaly alert panel renders",
            "Anomaly Alert Panel Verification",
            "The Real-Time Anomaly and Risk Alerts panel is visible on the dashboard.",
            must_contain_text=["Real-Time Anomaly"],
        )

    if _match_patterns(combined, ["uptime", "watchdog", "server health", "keep running", "start_all"]):
        add(
            "UPTIME",
            "Application servers respond for browser testing",
            "Application Uptime Verification",
            "The dashboard and sprint board pages load in the browser confirming frontend and backend services are running.",
            url=f"{BASE_URL}/sprints",
            must_be_visible=["select#sprint-board-workspace-select"],
        )

    return cases


def load_registry() -> dict[str, Any]:
    if REGISTRY_PATH.exists():
        try:
            return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"tasks": {}, "active_task_id": None, "history": []}


def save_registry(data: dict[str, Any]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def register_sprint_task(
    task_id: str,
    task_title: str,
    description: str = "",
    project_name: str = "",
) -> list[dict[str, Any]]:
    """Generate browser cases for a sprint task, persist to registry, set as active."""
    cases = _build_cases_for_task(task_id, task_title, description, project_name)
    registry = load_registry()
    registry.setdefault("tasks", {})[task_id] = {
        "task_id": task_id,
        "task_title": task_title,
        "description": description,
        "project_name": project_name,
        "registered_at": datetime.now().isoformat(),
        "cases": cases,
    }
    registry["active_task_id"] = task_id
    history = [task_id] + [h for h in registry.get("history", []) if h != task_id]
    registry["history"] = history[:50]
    save_registry(registry)
    return cases


def load_active_browser_cases() -> list[dict[str, Any]]:
    registry = load_registry()
    active = registry.get("active_task_id")
    if not active:
        return []
    return registry.get("tasks", {}).get(active, {}).get("cases", [])


def load_all_registered_cases() -> list[dict[str, Any]]:
    registry = load_registry()
    all_cases: list[dict[str, Any]] = []
    for tid in registry.get("history", []):
        all_cases.extend(registry.get("tasks", {}).get(tid, {}).get("cases", []))
    return all_cases


def get_excel_dynamic_category(
    task_id: str | None = None,
    case_results: dict[str, str] | None = None,
) -> tuple[str, list[tuple]]:
    """Returns (category_title, rows) for Excel. Row: (case_id, name, area, expected, actual, status)."""
    registry = load_registry()
    case_results = case_results or registry.get("last_case_results", {})
    cases: list[dict[str, Any]] = []

    if task_id and task_id in registry.get("tasks", {}):
        task = registry["tasks"][task_id]
        category = f"📋 Sprint Task: {task.get('task_title', 'Sprint Task')[:50]}"
        cases = task.get("cases", [])
    elif registry.get("active_task_id"):
        task = registry["tasks"].get(registry["active_task_id"], {})
        category = f"📋 Sprint Task: {task.get('task_title', 'Active Task')[:50]}"
        cases = task.get("cases", [])
    else:
        category = "📋 Sprint Task Dynamic Verification"
        cases = load_all_registered_cases()

    rows: list[tuple] = []
    for c in cases:
        cid = c["case_id"]
        status = case_results.get(cid, "PENDING")
        if status == "PASS":
            actual = f"Successfully verified in browser: {c['expected'][:120]}"
        elif status == "FAIL":
            actual = f"Browser verification failed for sprint task requirement: {c['name']}"
        else:
            actual = "Awaiting browser test execution for this sprint task case."
        rows.append((
            cid,
            c["name"],
            c["functionality"],
            c["expected"],
            actual,
            status if status in ("PASS", "FAIL") else "PENDING",
        ))
    return category, rows


def record_case_results(results: dict[str, str]) -> None:
    registry = load_registry()
    registry["last_case_results"] = results
    registry["last_results_at"] = datetime.now().isoformat()
    save_registry(registry)
