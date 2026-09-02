# 📌 TASK 43 — Demo Readiness: Zero Manual Intervention (`#demo-readiness`)

## Goal
The full stack must run **autonomously for a live demo** — Plane pickup → Build → Test → Close → Git → Done — with no Cursor/manual fixes mid-demo.

---

## Mandatory demo checklist

| Area | Requirement | Status |
|------|-------------|--------|
| **Servers** | Backend `:8000` + Frontend `:5173` running before demo | Use `scripts/start_all_services.bat` or watchdog |
| **Sprint watcher** | Single instance polling Plane (`run_sprint_watcher.py --interval 30`) | Restart after agent code changes |
| **Unit tests** | `pytest tests/unit/` — all pass before demo | 86+ tests |
| **Build popup** | Click Build → files + functionality (Task 42) | Persists through Test→Done |
| **Git gate** | Local commit OK when `GIT_PUSH_OPTIONAL=true` (push may defer) | Demo-friendly |
| **Pipeline idle** | After task Done → UI shows idle ○ (not stuck Building) | `_finalize_task` resets |
| **Builder wiring** | Dynamic components auto-wired to `Dashboard.jsx` | `wire_component_to_dashboard()` |
| **No re-pick Done tasks** | Watcher skips verify-close on Plane `completed` group | `stuck_processed` guard |

---

## Agent rules (demo)

1. **Never skip Test** — use `fast` mode for verify-close only.
2. **Never mark Done** without Test pass + Plane close.
3. **Git** — commit meaningful paths; push retries 3× with fetch/rebase; if push fails and `GIT_PUSH_OPTIONAL=true`, gate passes with local commit.
4. **UI** — pipeline goes `idle` after finalize so demo audience sees clean state between tasks.
5. **Memory** — build detail fields persist same task_id (Task 42).

---

## Pre-demo commands

```bash
# Terminal 1 — backend
cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev -- --host 0.0.0.0

# Terminal 3 — sprint watcher
python scripts/run_sprint_watcher.py --interval 30

# Verify
python -m pytest tests/unit/ -q
```

---

## Related
- Task 37 — step gates  
- Task 38 — git allowlist  
- Task 41 — build authenticity  
- Task 42 — build detail persistence  
