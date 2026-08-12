# 📌 TASK 34 — Sprint Task Close on Test Pass Quality Gate (`#sprint-close-on-test-pass`)

## Overview
When a Plane sprint task finishes implementation **and all sprint test cases pass**, the agent pipeline **must mark the task Completed on Plane**. Tasks must never remain stuck in **In Progress** after a successful quality gate.

---

## 🎯 Mandatory Rule

```
IF sprint_task_tests_pass == TRUE:
    → update_task_status(project_id, task_id, "completed")
    → add Plane comment with test summary
    → complete_queue_task()
ELSE IF builder_made_changes AND tests_fail:
    → move task back to To Do (unstarted)
ELSE:
    → leave In Progress for manual review
```

> **Verify-only close:** If requirements are already satisfied in the codebase (builder makes no new changes) but **all tests still pass**, the task **must still be closed** as Completed on Plane.

---

## 🧪 Test Coverage Required

| Case | Builder | Tests | Plane Result |
|------|---------|-------|--------------|
| Full pipeline success | changes made | PASS | **Completed** |
| Verify-only success | no changes | PASS | **Completed** |
| Regression after build | changes made | FAIL | **To Do** |
| Not ready | no changes | FAIL | **In Progress** |
| Stuck in progress | any | PASS on re-verify | **Completed** |

### Dynamic sprint test cases
- Generated from Plane task title/description via `tests/sprint_task_test_generator.py`
- Registered in `memory/sprint_test_registry.json`
- Executed by `tester_agent.py` during quality gate

---

## 🛠️ Implementation Files

| File | Role |
|------|------|
| [`agents/sprint_watcher_agent.py`](../agents/sprint_watcher_agent.py) | Always runs tests; `_finalize_task()` closes on pass; `_verify_close_in_progress_task()` for stuck tasks |
| [`agents/sprint_watcher_helpers.py`](../agents/sprint_watcher_helpers.py) | `quality_gate_action()` decision helper |
| [`agents/tester_agent.py`](../agents/tester_agent.py) | Full unit + browser + dynamic sprint tests |
| [`tests/unit/test_sprint_close_on_test_pass.py`](../tests/unit/test_sprint_close_on_test_pass.py) | Unit tests for quality gate logic |

---

## ⚙️ Environment

```env
SPRINT_VERIFY_CLOSE_COOLDOWN=120   # seconds between verify-close attempts for stuck In Progress tasks
```

---

## 🔄 Stuck Task Recovery

Each watcher cycle:
1. **Unprocessed In Progress** → full retry pipeline (builder + tests + close)
2. **Processed but still In Progress on Plane** → verify-close (tests only; close if pass)

Example: **"Remove Unwanted Content"** stuck in In Progress → verify-close runs sprint tests → on PASS → moves to Completed column.
