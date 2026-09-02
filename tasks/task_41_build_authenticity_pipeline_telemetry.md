# 📌 TASK 41 — Build Authenticity & End-to-End Pipeline Telemetry (`#build-authenticity`)

## Problem
Users saw Pickup + Build checkmarks appear in **seconds** for new Plane tasks and could not tell whether the agent actually changed code or only skipped work. A task is **not complete** when Build shows ✓ — only when **Test → Close → Git → Done** all pass.

---

## Root causes fixed

| Issue | Fix |
|-------|-----|
| Build ✓ with no visible work | **Build heartbeat** sub-phases + elapsed timer in UI |
| `already_applied` looked like full build | **Verify-only** badge (amber ✓v) vs **code changed** (green ✓ + file count) |
| Test exception treated as pass | Builder unit verify returns **False** on pytest errors |
| No duration shown | `build_duration_seconds` in pipeline state |
| User thinks task is done at Build | UI message: *"Build ✓ — starting Test gate"* until Test passes |

---

## Build sub-phases (mandatory telemetry)

| Sub-phase | Agent action | Typical time |
|-----------|--------------|--------------|
| `starting` | Load task context | ~1s |
| `classifying` | NLP intent + rules | ~2–5s |
| `spec_load` | Read `tasks/*.md` spec | ~1–3s |
| `patching` | LLM + rule-based file edits | ~5–60s |
| `unit_verify` | pytest `tests/unit/` in builder | ~8–15s |
| `done` | Record outcome → Test gate | — |

**Functions:** `update_build_progress()`, `record_build_result()`, `clear_build_progress()` in `memory_manager.py`.

---

## Build outcomes (UI MUST show)

| Outcome | Meaning | Build step icon |
|---------|---------|-----------------|
| `code_changed` | N files modified | Green ✓ + "N file(s) changed (Xs)" |
| `verify_only` | Requirements already in codebase | Amber ✓v + "Verify-only (Xs)" |

Verify-only still runs **full Test gate** — it is not task completion.

---

## End-to-end completion definition

A Plane task is **fully complete** only when:

1. **Pickup** — In Progress on Plane  
2. **Build** — Builder exit 0 + unit verify pass  
3. **Test** — Tester full/fast gate pass  
4. **Close** — Plane Completed  
5. **Git** — Meaningful files committed (Task 38)  
6. **Done** — UI pipeline Done + task in Recently Completed  

---

## Agent files

| File | Role |
|------|------|
| `agents/builder_agent.py` | Build heartbeat + `record_build_result` |
| `agents/sprint_watcher_agent.py` | Messages after build; Test only after Build |
| `agents/memory_manager.py` | Build/test telemetry fields |
| `frontend/src/components/AgentPipelineTracker.jsx` | Build + test sub-phase chips, elapsed, outcomes |

---

## Definition of Done

- [x] Build sub-phases visible in Sprint Board UI
- [x] Verify-only vs code-changed distinguished
- [x] Builder pytest failure blocks Build gate
- [x] **Click Build step** → popup with files changed + functionality summary (`build_functionality`, `build_files_modified`)
- [x] Documented in `tasks.md` mandatory rules

## Related
- Task 37 — step gates  
- Task 40 — daily memory logs build duration in task_history  
