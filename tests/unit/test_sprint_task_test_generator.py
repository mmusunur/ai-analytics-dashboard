"""Unit tests for dynamic sprint task test case generation."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
_gen_path = ROOT / "tests" / "sprint_task_test_generator.py"
_spec = importlib.util.spec_from_file_location("sprint_task_test_generator", _gen_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

register_sprint_task = _mod.register_sprint_task
load_active_browser_cases = _mod.load_active_browser_cases
get_excel_dynamic_category = _mod.get_excel_dynamic_category


def test_register_sprint_task_generates_smoke_case():
    cases = register_sprint_task(
        "test-task-id-001",
        "Remove Unwanted Content",
        "Hide Copilot Search Fixes and Agent Monitor from dashboard",
        "AI Analytics Dashboard",
    )
    assert len(cases) >= 2
    ids = [c["case_id"] for c in cases]
    assert any("SMOKE" in i for i in ids)
    assert any("HIDE-UI" in i for i in ids)
    assert load_active_browser_cases()[0]["task_id"] == "test-task-id-001"


def test_excel_dynamic_category_includes_task_rows():
    register_sprint_task("test-task-excel-002", "Sprint Board Navigation", "Verify kanban columns")
    category, rows = get_excel_dynamic_category("test-task-excel-002")
    assert "Sprint Task" in category
    assert len(rows) >= 1
    assert rows[0][0].startswith("TC-TASK-")


def test_sprint_board_task_adds_sprint_ui_case():
    cases = register_sprint_task(
        "test-task-sprint-003",
        "Sprint Board Browser Navigation",
        "Workspace dropdown and kanban",
    )
    assert any("SPRINT-UI" in c["case_id"] for c in cases)
