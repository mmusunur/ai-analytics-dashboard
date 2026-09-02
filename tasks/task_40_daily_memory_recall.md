# 📌 TASK 40 — Daily Memory Recall & Previous-Day Context (`#daily-memory-recall`)

## Overview
Agents MUST **read memory** at the start of a new day (or new session) to understand what happened **yesterday** — completed tasks, failures, pipeline state, and conversation context — before picking new Plane work.

> Extends Task 28 (daily persistence). Task 40 is the **recall / read-back** mandate.

---

## Memory locations (read order)

| Priority | Path | Purpose |
|----------|------|---------|
| 1 | `memory/task_history/YYYY-MM-DD_task_history.jsonl` | Yesterday's task completions, failures, durations |
| 2 | `memory/agent_state.json` | Last pipeline phase, queue, agent statuses |
| 3 | `memory/conversations/assistant_conversation.jsonl` | Recent user intent and decisions |
| 4 | `memory/sprint_test_registry.json` | Dynamic browser cases from prior sprint tasks |
| 5 | `tasks.md` | Current mandatory rules (always authoritative) |

---

## Agent workflow (MANDATORY)

### At session start / watcher boot / orchestrator wake

1. Call `get_previous_day_context()` from [`agents/memory_manager.py`](../agents/memory_manager.py).
2. Log summary to console: tasks completed, failed, still In Progress on Plane.
3. If yesterday had **failed** tasks or **git sweep** pending → prioritize retry or git sync before new pickups.
4. Append session-start note via `log_task_result("SESSION", "Daily recall", "memory", "recall", summary)`.

### During each user conversation turn

- Call `update_conversation_memory()` (Task 28) — append query + response summary.
- Update `agent_state.json` timestamps via `update_agent_status()`.

### End of day

- Task history file rotates automatically (`YYYY-MM-DD_task_history.jsonl`).
- Retention: 30 days (`memory_helpers.cleanup_old_memory`).

---

## API / helper functions

```python
from agents.memory_manager import (
    get_previous_day_context,   # yesterday + today-so-far summary
    load_task_history_for_date, # read specific date JSONL
    update_conversation_memory,
    log_task_result,
)
```

---

## Example recall output (agent should produce)

```
📅 Memory recall — previous day 2026-08-11
  ✅ Completed: Data Analytics, Remove Unwanted Content
  ❌ Failed: (none)
  🔄 Pipeline last: idle, git sweep pending: 0 files
  💬 Last conversation: 2026-08-11T18:30:00
```

---

## Definition of Done

- [x] `get_previous_day_context()` in memory_manager
- [x] Sprint Watcher calls recall on startup
- [ ] Orchestrator calls recall on startup (recommended)

## Related
- Task 28 — write path (persistence)
- Task 39 — README reflects memory/recall docs after changes
