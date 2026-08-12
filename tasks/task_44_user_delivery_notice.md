# 📌 TASK 44 — User Delivery Notice (`#user-delivery-guide`)

## Problem
Users only submit tasks in Plane — the agent writes all code. After Done, users had **no clue what was added, where to find it, or how to use it**.

## Solution
Every completed build MUST produce a **delivery guide** shown in three places:

| Surface | When |
|---------|------|
| **Sprint Board banner** | `TaskDeliveryNotice` — headline, where, steps, “Open feature” button |
| **Build detail popup** | Click Build step → “How to use (for you)” section |
| **Recently Completed queue** | Each task shows compact guide + link |
| **Plane task comment** | On close — same guide posted automatically |

---

## Data model

Stored in pipeline as `build_usage_guide`:

```json
{
  "headline": "Data Analytics — upload CSV/Excel and train",
  "where": "Dashboard — Data Analytics panel",
  "route": "/",
  "route_label": "Open Dashboard",
  "steps": ["Go to Dashboard", "Upload file", "Click Train"],
  "task_title": "Data Analytics",
  "verify_only": false
}
```

Copied to `task_queue.completed[].delivery_guide` on task close.

---

## Agent implementation

| File | Role |
|------|------|
| `agents/memory_manager.py` | `BUILD_USAGE_GUIDES`, `_build_usage_guide()`, `format_delivery_comment()` |
| `agents/builder_agent.py` | Via `record_build_result()` |
| `agents/sprint_watcher_agent.py` | Plane comment on close includes delivery text |
| `frontend/.../TaskDeliveryNotice.jsx` | User-facing banner + compact mode |
| `frontend/.../SprintBoard.jsx` | Shows latest delivery after task completes |
| `frontend/.../AgentPipelineTracker.jsx` | Build popup “How to use” section |

---

## Rules (mandatory)

1. **Every intent** in `BUILD_USAGE_GUIDES` MUST have: headline, where, route, steps.
2. **Unknown intents** — infer route from changed files (`Dashboard.jsx` → `/`, `SprintBoard` → `/sprints`, etc.).
3. **Verify-only** — guide says “already in codebase — verified”.
4. **Never skip** delivery guide on `record_build_result()`.

---

## Definition of Done

- [x] `build_usage_guide` in pipeline state
- [x] Sprint Board banner with link to feature
- [x] Build popup shows how-to-use
- [x] Completed queue entries include guide
- [x] Plane comment includes delivery text
- [x] Documented in `tasks.md` rule #14

## Related
- Task 41 — build authenticity  
- Task 42 — build detail persistence  
- Task 43 — demo readiness  
