"""
Unit tests for Sprint Board Screen, Multi-Project Aggregation, Workspaces, and Agent Monitor Screen.
Includes state filtering, cancelled task isolation, and watcher trigger safety tests.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
ROOT_DIR = Path(__file__).parent.parent.parent


def test_sprint_tasks_endpoint():
    """GET /api/sprints/tasks should return live Plane sprint metadata and task lists."""
    response = client.get("/api/sprints/tasks?workspace_slug=agentbuilder&project_id=all")
    assert response.status_code == 200
    data = response.json()
    assert "sprint" in data
    assert "tasks" in data
    assert data["sprint"]["total_tasks"] >= 0
    assert "todo" in data["tasks"]
    assert "in_progress" in data["tasks"]
    assert "completed" in data["tasks"]
    assert "backlog" in data["tasks"]


def test_sprint_workspaces_endpoint():
    """GET /api/sprints/workspaces should return accessible Plane workspaces and projects."""
    response = client.get("/api/sprints/workspaces")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") in ("success", "fallback")
    assert "workspaces" in data
    assert len(data["workspaces"]) >= 1
    first_ws = data["workspaces"][0]
    assert "slug" in first_ws
    assert "projects" in first_ws


def test_sprint_board_multi_project_aggregation():
    """GET /api/sprints/tasks with project_id=all should aggregate tasks across all workspace projects."""
    response = client.get("/api/sprints/tasks?workspace_slug=agentbuilder&project_id=all")
    assert response.status_code == 200
    data = response.json()
    assert data.get("workspace_slug") == "agentbuilder"
    assert data.get("project_id") == "all"
    assert "scanned_projects_count" in data
    assert data["scanned_projects_count"] >= 1
    all_tasks = data.get("tasks", {}).get("all", [])
    if len(all_tasks) > 0:
        first_task = all_tasks[0]
        assert "project_name" in first_task
        assert "project_id" in first_task


def test_sprint_board_page_component_file():
    """Verify SprintBoard.jsx component file exists and contains workspace/project dropdown selectors."""
    comp_path = ROOT_DIR / "frontend" / "src" / "pages" / "SprintBoard.jsx"
    assert comp_path.exists(), "SprintBoard.jsx page should exist"
    content = comp_path.read_text(encoding="utf-8")
    assert "sprint-board-workspace-select" in content or "selectedWorkspace" in content
    assert "sprint-board-project-select" in content or "selectedProject" in content
    assert "Backlog" in content
    assert "To Do" in content
    assert "In Progress" in content
    assert "Completed" in content


def test_agent_monitor_page_component_file():
    """Verify AgentMonitor.jsx and AgentTaskActivityTracker.jsx files exist and render agent fleet monitoring."""
    comp_path = ROOT_DIR / "frontend" / "src" / "pages" / "AgentMonitor.jsx"
    assert comp_path.exists(), "AgentMonitor.jsx page should exist"
    tracker_path = ROOT_DIR / "frontend" / "src" / "components" / "AgentTaskActivityTracker.jsx"
    assert tracker_path.exists(), "AgentTaskActivityTracker.jsx component should exist"
    content = tracker_path.read_text(encoding="utf-8")
    assert "plane-workspace-selector" in content or "selectedWorkspace" in content
    assert "plane-project-selector" in content or "selectedProject" in content
    assert "Autonomous Agent Task Pickup" in content


# --------------------------------------------------------------------------
# NEW: State Filtering & Cancelled Task Isolation Tests (Bug Fix Verification)
# --------------------------------------------------------------------------

def test_sprint_tasks_response_includes_cancelled_field():
    """
    BUG FIX TC-01: Cancelled tasks must NOT bleed into the backlog column.
    The API response must contain a 'cancelled' key separate from 'backlog'.
    """
    response = client.get("/api/sprints/tasks?workspace_slug=agentbuilder&project_id=all")
    assert response.status_code == 200
    data = response.json()
    tasks = data.get("tasks", {})
    assert "cancelled" in tasks, (
        "API must return a 'cancelled' task list. "
        "Cancelled tasks were incorrectly showing in Backlog column."
    )


def test_cancelled_tasks_not_in_backlog():
    """
    BUG FIX TC-02: Cancelled tasks (state_group='cancelled') must NEVER appear in backlog list.
    Previously the else-clause in state classification caught 'cancelled' as backlog.
    """
    response = client.get("/api/sprints/tasks?workspace_slug=agentbuilder&project_id=all")
    assert response.status_code == 200
    data = response.json()
    tasks = data.get("tasks", {})
    backlog_ids = {t["id"] for t in tasks.get("backlog", [])}
    cancelled_ids = {t["id"] for t in tasks.get("cancelled", [])}
    overlap = backlog_ids & cancelled_ids
    assert len(overlap) == 0, (
        f"Tasks found in BOTH backlog and cancelled columns (IDs: {overlap}). "
        "Cancelled tasks must not bleed into the Backlog."
    )


def test_state_group_column_mapping():
    """
    TC-03: Verify each state_group maps to the correct kanban column.
    Tests the classification logic that caused 'Remove Unwanted Content' to show in wrong column.
    """
    response = client.get("/api/sprints/tasks?workspace_slug=agentbuilder&project_id=all")
    assert response.status_code == 200
    data = response.json()
    tasks = data.get("tasks", {})
    cancelled_groups = {"cancelled", "wont_fix", "rejected", "duplicate"}

    for task in tasks.get("cancelled", []):
        sg = task.get("state_group", "").lower()
        assert sg in cancelled_groups or sg == "", (
            f"Task '{task['name']}' in cancelled list has wrong state_group: {sg}"
        )

    for task in tasks.get("backlog", []):
        sg = task.get("state_group", "").lower()
        assert sg not in cancelled_groups, (
            f"Task '{task['name']}' with state_group='{sg}' is cancelled but appeared in backlog"
        )


def test_sprint_metadata_includes_cancelled_count():
    """TC-04: Sprint metadata must include cancelled_tasks count so UI can display it accurately."""
    response = client.get("/api/sprints/tasks?workspace_slug=agentbuilder&project_id=all")
    assert response.status_code == 200
    data = response.json()
    sprint = data.get("sprint", {})
    assert "cancelled_tasks" in sprint, "Sprint metadata must include cancelled_tasks count"
    assert isinstance(sprint["cancelled_tasks"], int)


def test_completion_percentage_excludes_cancelled():
    """
    TC-05: Completion % must NOT count cancelled tasks in the denominator.
    A sprint with 10 done, 5 open, 3 cancelled => 10/15 = 67%, not 10/18 = 56%.
    """
    response = client.get("/api/sprints/tasks?workspace_slug=agentbuilder&project_id=all")
    assert response.status_code == 200
    data = response.json()
    sprint = data.get("sprint", {})
    tasks = data.get("tasks", {})
    completed = len(tasks.get("completed", []))
    cancelled = len(tasks.get("cancelled", []))
    total = sprint.get("total_tasks", 0)
    open_tasks = total - cancelled
    reported_pct = sprint.get("completion_percentage", 0)
    if open_tasks > 0:
        expected_pct = round((completed / open_tasks * 100), 1)
        assert abs(reported_pct - expected_pct) < 1.0, (
            f"Completion % {reported_pct} is wrong. Expected {expected_pct} "
            f"(completed={completed}, open={open_tasks}, cancelled={cancelled} excluded)"
        )


def test_agent_status_endpoint():
    """TC-06: GET /api/sprints/agent-status must return sprint_watcher, builder, and tester statuses."""
    response = client.get("/api/sprints/agent-status")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") in ("success", "error")
    if data.get("status") == "success":
        assert "sprint_watcher" in data
        assert "builder" in data
        assert "tester" in data
        assert "status" in data["sprint_watcher"]
        assert "current_task" in data["sprint_watcher"]


def test_watcher_trigger_excludes_backlog_tasks():
    """
    TC-07: Backlog tasks must NOT trigger the sprint watcher.
    Only 'unstarted'/'todo'/'triaged' tasks should auto-trigger the agent.
    """
    sprints_router_path = ROOT_DIR / "backend" / "routers" / "sprints.py"
    assert sprints_router_path.exists()
    content = sprints_router_path.read_text(encoding="utf-8")
    assert "TRIGGER_GROUPS" in content, "TRIGGER_GROUPS constant must exist in sprints.py"
    trigger_lines = [line for line in content.splitlines() if "TRIGGER_GROUPS" in line and "=" in line]
    assert len(trigger_lines) > 0, "TRIGGER_GROUPS assignment not found"
    # Strip inline comments (everything after #) before checking value
    trigger_value = trigger_lines[0].split("#")[0]
    assert "backlog" not in trigger_value, (
        f"'backlog' must NOT be in TRIGGER_GROUPS value (found: {trigger_value.strip()}). "
        "Backlog is a holding area and must not auto-trigger the agent."
    )


def test_sprint_watcher_uses_correct_failure_state():
    """
    TC-08: When agent tests fail, task must move back to To Do ('unstarted') NOT to 'cancelled'.
    Cancelled is a deliberate human action, not an agent failure outcome.
    """
    watcher_path = ROOT_DIR / "agents" / "sprint_watcher_agent.py"
    assert watcher_path.exists()
    content = watcher_path.read_text(encoding="utf-8")
    assert "STATE_DONE    = \"completed\"" in content or "STATE_DONE = \"completed\"" in content, \
        "STATE_DONE must be 'completed' (correct Plane group name)"
    assert "STATE_TODO" in content, \
        "STATE_TODO must be used on test failure to move task back to To Do (not cancelled)"
    assert "_processed_task_ids.discard" in content, \
        "Failed tasks must be removed from _processed_task_ids so they can be retried"


def test_builder_agent_has_rollback_logic():
    """
    TC-09: Builder agent must backup files before LLM changes and rollback if tests fail.
    This prevents broken LLM code from staying in the codebase.
    """
    builder_path = ROOT_DIR / "agents" / "builder_agent.py"
    assert builder_path.exists()
    content = builder_path.read_text(encoding="utf-8")
    assert "file_backups" in content, "Builder must create file backups before LLM changes"
    assert "rolled_back" in content or "Rolled back" in content, \
        "Builder must rollback modified files when tests fail"


def test_pickup_groups_excludes_backlog():
    """
    TC-10: Sprint watcher PICKUP_GROUPS must NOT include 'backlog'.
    Backlog is a holding area; developer must promote to 'To Do' before agent picks up.
    """
    watcher_path = ROOT_DIR / "agents" / "sprint_watcher_agent.py"
    assert watcher_path.exists()
    content = watcher_path.read_text(encoding="utf-8")
    pickup_lines = [line for line in content.splitlines() if "PICKUP_GROUPS" in line and "=" in line]
    assert len(pickup_lines) > 0, "PICKUP_GROUPS assignment must exist in sprint_watcher_agent.py"
    # Strip inline comments before checking the set value
    pickup_value = pickup_lines[0].split("#")[0]
    assert "backlog" not in pickup_value, (
        f"'backlog' must NOT be in PICKUP_GROUPS value. "
        f"Found: {pickup_value.strip()}"
    )
