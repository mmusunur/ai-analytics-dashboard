# 📌 TASK 37 — Mandatory Step Gates & Auto-Retry Until Pass (`#sprint-step-gates`)

## Overview
The sprint pipeline has **6 mandatory gated steps**. **A step MUST fully pass before the next step runs.** If any step fails, the agent **retries that same step** (or returns to Build for Test failures) — **never skip ahead**.

> Example: If **Builder fails**, **Tester must NOT run**. The agent stays on the **Build** step, reads the error, fixes, and retries Build.

---

## 🚦 Mandatory Step Gate Rules

```
STEP 1 PICKUP (Sprint Watcher)
  → Move Plane task to In Progress
  → IF fail: retry on next poll
  → IF pass: mark completed_steps += pickup → GO TO STEP 2

STEP 2 BUILD (Builder Agent)  ⛔ GATE
  → Implement / fix code
  → Builder exit code MUST be 0
  → IF fail: retry BUILD (same step, up to SPRINT_MAX_RETRY_ATTEMPTS)
  → IF fail all retries: DO NOT run Test → outer re-pick cycle
  → IF pass: mark completed_steps += building → GO TO STEP 3

STEP 3 TEST (Tester Agent)  ⛔ GATE — ONLY AFTER BUILD PASSED
  → Run unit + browser + sprint task tests
  → IF fail: return to STEP 2 with test failure log (do NOT go to Close)
  → IF pass: mark completed_steps += testing → GO TO STEP 4

STEP 4 CLOSE (Plane Agent) — ONLY AFTER TEST PASSED
  → Mark task Completed on Plane

STEP 5 GIT PUSH — ONLY AFTER CLOSE
  → Commit meaningful file changes

STEP 6 DONE
  → UI shows Done, Task Queue → Recently Completed
```

### ⛔ FORBIDDEN behaviors

| Forbidden | Required instead |
|-----------|------------------|
| Run Test when Build failed | Stay on Build, retry with error context |
| Show ✓ on Build when builder exit ≠ 0 | Only mark `building` in `completed_steps` on success |
| Skip to Close when tests fail | Return to Build with test output |
| Ask human to move To Do between retries | Agent auto To Do + re-pick (outer cycle) |

---

## 🔄 Outer auto re-pick (after all inner retries exhausted)

```
IF all Build/Test cycles fail:
  → UI phase = failed (temporary)
  → Plane: move To Do + comment
  → Clear processed_task_id
  → Next watcher poll OR outer cycle: auto re-pick → Step 1 again
```

**Human action: NONE** between retries.

---

## 🖥️ UI Requirements

| State | Pipeline phase | Build ✓ | Test ✓ |
|-------|----------------|---------|--------|
| Building (1st try) | `building` | ○ | ○ |
| Build failed, retrying | `retry` | ○ | ○ |
| Build passed, testing | `testing` | ✓ | ○ |
| Test failed, back to build | `retry` | ○ (cleared on new cycle) | ○ |
| All passed | `done` | ✓ | ✓ |

Checkmarks come from `pipeline.completed_steps` in `memory/agent_state.json` — **not** from phase index alone.

---

## ⚙️ Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `SPRINT_MAX_RETRY_ATTEMPTS` | `10` | Retries per step gate (Build retries, Build↔Test cycles) |
| `SPRINT_MAX_OUTER_CYCLES` | `50` | Full re-pick cycles before temporary failed UI |
| `SPRINT_TEST_MODE` | `full` | Tester default: `full` or `fast` (watcher sets per step) |
| `SPRINT_VERIFY_CLOSE_COOLDOWN` | `45` | Seconds between verify-close retries when tests fail |
| `SPRINT_ACTIVE_POLL_INTERVAL` | `15` | Faster Plane poll when tasks are active |

---

## ⚡ Smart test modes (performance)

| Mode | When | Runs |
|------|------|------|
| **`full`** | Step 3 Test after Build (code changed) | All `tests/unit/` + all `tests/browser/` + sprint cases |
| **`fast`** | Step 3b Verify-close (Build already passed) | All unit (no HTML report) + dashboard smoke (2 tests) + sprint dynamic cases |

Verify-close must **not** re-run the full 39+ scenario browser suite — only targeted validation + task acceptance cases.

---

## 📁 Files

| File | Role |
|------|------|
| `agents/sprint_watcher_agent.py` | Step gates, no skip to Test on build fail |
| `agents/memory_manager.py` | `completed_steps`, `mark_pipeline_step_complete()` |
| `frontend/src/components/AgentPipelineTracker.jsx` | ✓ only for completed steps |
| `tasks.md` | Master mandatory gate table |

---

## 🧪 Definition of Done

- [x] Build failure blocks Test from running
- [x] Build retries same step with failure context
- [x] Test failure returns to Build (not Close)
- [x] UI checkmarks reflect actual step completion
- [x] Documented in `tasks.md` as mandatory rules

---

## Related Tasks
- Task 34 — Close on test pass
- Section 1 — 6-stage lifecycle pipeline
