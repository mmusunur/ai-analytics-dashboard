# 📌 TASK 26 — Memory Persistence & Sprint Automation (`#memory-sprint-automation`)

## Overview
Governs **persistent agent memory** and **automatic sprint task pickup** integration with the header clear-filter control.

> **Related:** Daily memory rules are fully specified in [`task_28_memory_and_daily_task_updates.md`](task_28_memory_and_daily_task_updates.md). Sprint pickup pipeline is in [`task_29_multi_project_autonomous_execution.md`](task_29_multi_project_autonomous_execution.md) and [`task_32_application_uptime_and_sprint_pipeline.md`](task_32_application_uptime_and_sprint_pipeline.md).

---

## Memory Engine
- **File:** [`agents/memory_manager.py`](../agents/memory_manager.py)
- **Stores:** `memory/agent_state.json`, `memory/conversations/`, `memory/task_history/`
- **Rule:** Update conversation and task history on every user/agent turn.

## Sprint Automation Hook
- **Files:** [`agents/sprint_watcher_agent.py`](../agents/sprint_watcher_agent.py), [`backend/routers/sprints.py`](../backend/routers/sprints.py)
- **Pickup groups:** `unstarted`, `todo`, `triaged` only (not `backlog` or `in_progress` for new pickup).
- **In-progress retry:** Stale `in_progress` tasks may be retried by the watcher when implementation was interrupted.

## Header Clear Filter
- **Component:** `#header-clear-filter` in Dashboard header controls ([`task_1_header_controls.md`](task_1_header_controls.md))
- **Behavior:** Resets global filters to `{}` (not empty string) and reloads all dashboard widgets.
