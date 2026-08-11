"""Unit tests for Task 34 — sprint task closes on Plane when tests pass."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agents"))

from sprint_watcher_helpers import quality_gate_action, IN_PROGRESS_GROUPS


def test_quality_gate_complete_when_tests_pass_with_builder():
    assert quality_gate_action(test_passed=True, builder_ran=True) == "complete"


def test_quality_gate_complete_when_tests_pass_verify_only():
    """Requirements already in codebase — tests pass, no new builder changes."""
    assert quality_gate_action(test_passed=True, builder_ran=False) == "complete"


def test_quality_gate_revert_todo_when_tests_fail_after_build():
    assert quality_gate_action(test_passed=False, builder_ran=True) == "revert_todo"


def test_quality_gate_leave_in_progress_when_tests_fail_no_build():
    assert quality_gate_action(test_passed=False, builder_ran=False) == "leave_in_progress"


def test_in_progress_groups_include_started():
    assert "started" in IN_PROGRESS_GROUPS
    assert "in_progress" in IN_PROGRESS_GROUPS


def test_task_34_spec_file_exists():
    spec = Path(__file__).parent.parent.parent / "tasks" / "task_34_sprint_close_on_test_pass.md"
    assert spec.exists()
    text = spec.read_text(encoding="utf-8")
    assert "completed" in text.lower()
    assert "test pass" in text.lower() or "tests pass" in text.lower()
