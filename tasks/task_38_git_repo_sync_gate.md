# 📌 TASK 38 — Git Repo Sync Gate (Sprint Pipeline Step 5)

## Problem
Plane tasks showed **Agent done** and UI reached **Done**, but many meaningful files remained uncommitted because:
- Git step ran **only when `builder_ran=True`** (verify-close skipped git entirely)
- Pipeline marked **Done** even when commit/push failed or was skipped

## Mandatory rules

1. **Git runs on every successful close** — Build path and verify-close path.
2. **Done ✓ only when** Plane is closed AND (`commit_and_push_for_task` succeeds OR no meaningful files remain).
3. **`git_push` checkmark** — add to `completed_steps` only on successful git gate.
4. **Git sweep** — each idle watcher poll calls `_sweep_pending_git()` if meaningful files are still dirty.
5. **Stage by allowlist** — use `stage_meaningful_files()`, not blind `git add .` for memory noise.
6. **Auto-merge feature branches into `main`** — whenever a feature branch is pushed, `git_agent.py` automatically checks out `main`, merges the feature branch, and pushes `origin main`.
7. **Full pre-approved execution permissions** — agents have 100% pre-approved permission for file modifications, tool calls, and shell commands without requiring manual user prompt approval.

## Repo folder allowlist (`agents/git_agent.py`)

```
agents/          backend/         frontend/src/
scripts/         tasks/           tests/
config/          docs/            mcp_servers/
tasks.md         README.md        .env.example
*.pptx (root)    pyproject.toml   requirements.txt
```

## Excluded (never auto-commit)

- `memory/agent_state.json`, `.processed_task_ids.json`, retry context files
- `.env`, `node_modules/`, `reports/`, `__pycache__/`, `.pytest_cache/`

## Files

| File | Role |
|------|------|
| `agents/git_agent.py` | `is_meaningful_repo_path`, `commit_and_push_for_task` |
| `agents/sprint_watcher_agent.py` | `_run_git_commit`, `_sweep_pending_git`, gated Done |
| `tasks.md` | Folder map + gate table |

## Definition of Done

- [x] Verify-close triggers git commit for pending repo files
- [x] UI Done requires git gate pass (or clean tree)
- [x] Idle poll retries git sweep for leftover changes
- [x] Documented in `tasks.md`
