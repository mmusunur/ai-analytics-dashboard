# 📌 TASK 39 — README Sync on Architecture & Agent Changes (`#readme-architecture-sync`)

## Overview
Whenever **architecture**, **agent behavior**, **pipeline gates**, or **new task specs** change, agents MUST update [`README.md`](../README.md) in the **same work session** — not as a follow-up ticket.

> Complements Task 33 (full doc sync). Task 39 is the **mandatory README + tasks.md index** rule agents read at startup.

---

## When README MUST be updated

| Change type | README sections to update |
|-------------|---------------------------|
| New / changed agent script | Agent Fleet table, project structure |
| Pipeline gate (Task 37, 38, …) | Sprint Pipeline Quick Reference, features list |
| New env vars | Launch commands, env var list |
| New API endpoint | Key API Endpoints table |
| New task spec file | Latest Task Specs table + link to `tasks.md` |
| Architecture layer (MCP, FastAPI router) | Core Features, project structure |
| Test mode (`full` / `fast`) | Features + sprint watcher commands |

---

## Agent workflow (MANDATORY)

1. Implement code / agent change.
2. Add or update spec in `tasks/task_*.md` and index in [`tasks.md`](../tasks.md).
3. **Update `README.md`** — features, agent table, structure, commands (preserve LLM model table unless models changed).
4. If presentation affected: `python scripts/generate_architecture_pptx.py`.
5. Git gate (Task 38) includes `README.md` in commit allowlist.

---

## Trigger phrases (agents MUST recognize)

- "architecture change", "new agent", "pipeline update", "new task in tasks.md"
- After completing Tasks 35–38 class work → README sync required
- User asks "did you update README?" → verify and update if stale

---

## Definition of Done

- [ ] `tasks.md` index lists new task file
- [ ] `README.md` reflects current pipeline, agents, and latest task numbers
- [ ] No README drift vs `tasks.md` mandatory gate table

## Related
- Task 33 — full PPTX/DOCX sync
- Task 38 — README committed via git gate
