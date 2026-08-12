"""Regression: build detail fields survive set_pipeline_status phase transitions (Task 42)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "agents"))

import memory_manager as mm


def test_build_detail_persists_into_testing(tmp_path, monkeypatch):
    state_file = tmp_path / "agent_state.json"
    monkeypatch.setattr(mm, "STATE_FILE", state_file)
    monkeypatch.setattr(mm, "MEMORY_DIR", tmp_path)
    monkeypatch.setattr(
        mm, "update_queue_progress", lambda *a, **k: None
    )

    tid = "task-abc"
    mm.save_state({
        "pipeline": {
            "phase": "building",
            "task_id": tid,
            "task_title": "Sample Task",
            "build_outcome": "code_changed",
            "build_files_modified": ["frontend/src/components/Foo.jsx"],
            "build_functionality": ["Foo panel added"],
            "build_intents": ["FOO_INTENT"],
            "build_usage_guide": {"headline": "Foo feature", "route": "/", "steps": ["Open Dashboard"]},
            "build_duration_seconds": 12.5,
            "completed_steps": ["pickup", "building"],
        }
    })

    mm.set_pipeline_status(
        "testing", tid, "Sample Task", "tester", "Running tests"
    )
    pipeline = mm.get_pipeline_status()

    assert pipeline["phase"] == "testing"
    assert pipeline["build_outcome"] == "code_changed"
    assert pipeline["build_files_modified"] == ["frontend/src/components/Foo.jsx"]
    assert pipeline["build_functionality"] == ["Foo panel added"]
    assert pipeline["build_intents"] == ["FOO_INTENT"]
    assert pipeline["build_duration_seconds"] == 12.5
    assert pipeline["build_usage_guide"]["headline"] == "Foo feature"


def test_build_snapshot_survives_testing_phase(tmp_path, monkeypatch):
    state_file = tmp_path / "agent_state.json"
    monkeypatch.setattr(mm, "STATE_FILE", state_file)
    monkeypatch.setattr(mm, "MEMORY_DIR", tmp_path)
    monkeypatch.setattr(mm, "update_queue_progress", lambda *a, **k: None)

    tid = "task-live"
    mm.save_state({
        "pipeline": {
            "phase": "building",
            "task_id": tid,
            "task_title": "Live Task",
            "build_outcome": "code_changed",
            "build_files_modified": ["Foo.jsx"],
            "build_functionality": ["Foo added"],
            "build_intents": ["FOO_INTENT"],
            "build_usage_guide": {"headline": "Foo", "route": "/"},
        }
    })
    mm._persist_build_snapshot(tid, mm.load_state()["pipeline"])
    mm.set_pipeline_status("testing", tid, "Live Task", "tester", "Running tests")

    pipeline = mm.get_pipeline_status()
    assert pipeline["phase"] == "testing"
    assert pipeline["build_files_modified"] == ["Foo.jsx"]
    assert pipeline["build_usage_guide"]["headline"] == "Foo"


def test_build_detail_cleared_on_new_pickup(tmp_path, monkeypatch):
    state_file = tmp_path / "agent_state.json"
    monkeypatch.setattr(mm, "STATE_FILE", state_file)
    monkeypatch.setattr(mm, "MEMORY_DIR", tmp_path)

    mm.save_state({
        "pipeline": {
            "phase": "done",
            "task_id": "old-task",
            "build_outcome": "code_changed",
            "build_files_modified": ["a.py"],
            "completed_steps": ["pickup", "building", "testing", "closing", "git_push", "done"],
        }
    })

    mm.reset_pipeline_steps("new-task", "New Task")
    pipeline = mm.load_state()["pipeline"]

    assert pipeline["task_id"] == "new-task"
    assert "build_outcome" not in pipeline
    assert "build_files_modified" not in pipeline
