# Task 45 — Sprint Board UX Consistency (Column Placement, Checkmarks, Refresh)

## Problem

Users reported confusing Sprint Board behavior:

1. **Wrong column** — Active agent task (e.g. "Add Aditional Features") appears in **Backlog** with a green **"✓ Agent done"** badge while the pipeline is in Build or Test.
2. **Blank page on refresh** — Full Sprint Board goes empty during reload while Plane/fleet APIs are fetching.
3. **Empty pipeline checkmarks** — During Test, **Pickup** and **Build** show ○ (empty) even though those steps already passed.
4. **Feature discoverability** — Delivery notice says what was built but the Dashboard panel is hard to find / lacks clear usage cues.

## Root causes

| Issue | Cause |
|-------|--------|
| Backlog + "Agent done" | `task_queue.completed` contained the task while `task_queue.active` was null; Plane API still listed task in backlog/unstarted |
| Blank refresh | `sprintData` and `fleetData` reset to `null` on remount; no stale-data fallback |
| Empty checkmarks | `completed_steps` dropped on test heartbeats; UI only read explicit array, not current phase |
| Feature hidden | `AddAditionalFeatures.jsx` had placeholder text only; no stable DOM id for tests/delivery guide |

## Required fixes

### Backend (`agents/memory_manager.py`)

- `update_queue_progress()` — re-hydrate `active` from pipeline when queue active is null; remove task from `completed` list.
- `update_test_progress()` / `update_build_progress()` — preserve `completed_steps`; infer pickup + building complete during Test.
- `set_pipeline_status()` — infer completed steps when entering Test+ phases.

### Frontend

- **`SprintBoard.jsx`**
  - Stale-data fallback for sprint tasks and fleet/pipeline on refresh.
  - Pipeline-live task excluded from Backlog/To Do/Completed; injected into **In Progress** column.
  - `queueMap` overlays pipeline as source of truth (active beats stale completed).
  - `data-testid` on Backlog and In Progress columns.

- **`AgentPipelineTracker.jsx`**
  - Infer step complete from current phase when `completed_steps` is incomplete.
  - `data-testid="pipeline-step-{key}"` and `data-step-complete` attributes.

- **`DataAnalytics.jsx`** on Dashboard — stable `#data-analytics-panel` id for delivery guide and browser tests.

### Browser tests (`tests/browser/test_sprint_board_pipeline_e2e.py`)

| Case | Assertion |
|------|-----------|
| Refresh stability | After `page.reload()`, kanban columns and pipeline tracker remain visible (not blank) |
| Column placement | When pipeline has live task, task title in In Progress column, NOT in Backlog with "Agent done" |
| Pipeline checkmarks | During `testing` phase, Pickup + Build steps have `data-step-complete="true"` |
| Feature delivery | Dashboard shows `#data-analytics-panel`; delivery notice "Open Dashboard" navigates to it |

## Definition of Done

- [ ] Active pipeline task never shows "✓ Agent done" in Backlog
- [ ] Page refresh keeps last-known sprint + pipeline data visible while reloading
- [ ] Pickup ✓ and Build ✓ visible when Test is active
- [ ] Additional Features panel findable on Dashboard with stable id
- [ ] Browser E2E tests pass in `test_sprint_board_pipeline_e2e.py`
- [ ] Rule #15 added to `tasks.md`

## Agent MUST

After implementing: run unit tests + targeted browser E2E; restart sprint watcher if `memory_manager.py` changed.
