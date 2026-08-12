# 📌 TASK 42 — Build Detail Popup Persistence (End-to-End) (`#build-detail-popup`)

## Problem
The **Build Details** popup showed empty placeholders ("No build recorded", "No files listed") even while the task was in **Testing** or later phases — after Build had already completed with real file changes.

## Root cause
`set_pipeline_status()` rebuilt the entire `pipeline` object on every phase change and only carried over `completed_steps` (and test heartbeat fields). **`build_outcome`, `build_files_modified`, `build_functionality`, and `build_intents` were dropped** when transitioning Build → Test → Close → Git.

## Fix (mandatory)

| Rule | Implementation |
|------|----------------|
| Record at end of Build | `record_build_result()` writes all build detail fields |
| Live during Build | `update_build_progress()` may set `build_files_modified` early |
| **Persist through pipeline** | `_carry_build_fields()` in `set_pipeline_status()` copies `BUILD_DETAIL_KEYS` when `task_id` matches previous pipeline |
| Clear on new task | `reset_pipeline_steps()` clears build detail + progress keys |
| Clear when idle | `set_pipeline_status("idle")` with no `task_id` clears build fields |
| UI popup | `AgentPipelineTracker.jsx` — click Build step anytime Build ✓ through Done |

### Fields that MUST persist (same task)

- `build_outcome` — `code_changed` \| `verify_only`
- `build_files_modified` — list of repo-relative paths
- `build_functionality` — human-readable bullet list
- `build_intents` — NLP intent codes
- `build_duration_seconds`
- `build_detail_updated_at`

### Fields cleared after Build (heartbeat only)

- `build_subphase`, `build_started_at` — via `clear_build_progress()`

## UI behavior (Definition of Done)

- [x] During **Build**: popup shows live sub-phase + files as they appear
- [x] During **Test / Close / Git / Done**: popup still shows outcome, functionality, files for **current task**
- [x] After pipeline goes **idle** (no task): build detail cleared; next task starts fresh
- [x] Documented in `tasks.md` rule #12

## Agent files

| File | Change |
|------|--------|
| `agents/memory_manager.py` | `_carry_build_fields`, `BUILD_DETAIL_KEYS`, `reset_pipeline_steps` |
| `frontend/src/components/AgentPipelineTracker.jsx` | Build detail modal (Task 41) |

## Related
- Task 41 — build authenticity telemetry  
- Task 37 — step gates  
