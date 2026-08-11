# 🚨 Section 1: Mandatory Tasks & Autonomous Execution

This document outlines the mandatory operational requirements, launch scripts, anti-spam git commit directives, README updates, conversation memory rules, and autonomous workflow rules for the AI Analytics Dashboard project.

---

## 1. Mandatory Services & Agent Fleet Launchers (.bat / .sh)
The application system provides mandatory platform-specific execution launcher scripts to start all backend servers, frontend UI, background agents, watchdog supervisor, and memory managers in one command:

- 💻 **Windows Batch Execution Script:** [`scripts/start_all_services.bat`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/scripts/start_all_services.bat)
- 🐧 **Linux / macOS Shell Execution Script:** [`scripts/start_all_services.sh`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/scripts/start_all_services.sh)

---

## 🔄 2. End-to-End Autonomous Task Lifecycle Pipeline (Pickup → Understand → Build → Test → Close → Git Push)

The agent network executes the complete 6-stage task workflow autonomously:

```
┌──────────────────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│ 1. Multi-Workspace & Project Pickup  │ ───► │ 2. Title & NLP Parsing  │ ───► │ 3. Real Code Building   │
│ (sprint_watcher_agent scanner)       │      │ (builder_agent classifier)     │ (React & FastAPI edit)  │
└──────────────────────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
             │                                                                 │
             ▼                                                                 ▼
┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│ 6. Autonomous Git Push  │ ◄─── │ 5. Close Task on Plane  │ ◄─── │ 4. Pytest & Playwright  │
│ (git_agent / EOD push)  │      │ (plane_agent REST API)  │      │ (tester_agent runner)   │
└─────────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
```

### Stage 1: Sprint Task Pickup
- **Files:** [`agents/sprint_watcher_agent.py`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/agents/sprint_watcher_agent.py), [`backend/routers/sprints.py`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/backend/routers/sprints.py)
- **Behavior:** Polls Plane REST API every 15s or triggers via non-blocking background thread whenever `/api/sprints/tasks` is called. Detects tasks in `ACTIONABLE_STATES` (`unstarted`, `todo`, `started`, `in_progress`).

### Stage 2: Task Comprehension & Intent Classification
- **File:** [`agents/builder_agent.py`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/agents/builder_agent.py)
- **Behavior:** Runs `classify_task_intent_and_intent_map()` and LLM task analyzer (`llm_analyze_and_implement_task()`) to understand title, description, typos, and specific requirement statements.

### Stage 3: Real Code Modifications & Feature Implementation
- **File:** [`agents/builder_agent.py`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/agents/builder_agent.py)
- **Behavior:** Dynamically reads target React frontend components (`frontend/src/`) and FastAPI routers (`backend/routers/`), generating and applying code patches.

### Stage 4: Automated Testing & Playwright Verification
- **Files:** [`agents/tester_agent.py`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/agents/tester_agent.py), [`tests/unit/`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tests/unit/), [`tests/browser/`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tests/browser/)
- **Behavior:** Executes 51 pytest unit tests (`pytest tests/unit/`) and 14 Playwright browser E2E tests (`pytest tests/browser/`) to verify quality gates.

### Stage 5: Closing Sprint Task on Plane
- **Files:** [`agents/sprint_watcher_agent.py`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/agents/sprint_watcher_agent.py), [`agents/plane_agent.py`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/agents/plane_agent.py)
- **Behavior:** Updates Plane REST API task state to `Completed` (`state_group = "completed"`).

### Stage 6: Autonomous Git Commit & Push (With Anti-Spam Guard)
- **Files:** [`agents/git_agent.py`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/agents/git_agent.py), [`scripts/end_of_day.py`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/scripts/end_of_day.py)
- **Behavior:** Stages modified source files ONLY if meaningful changes exist (`get_meaningful_changed_files()`), skipping useless log/cache spam commits.

---

## 🚫 3. Mandatory Zero Unnecessary / Spam Git Commit Directive
- **Strict Anti-Spam Policy:**
  - DO NOT commit when only `.log` files, `.system_generated/` brain logs, caches (`__pycache__`, `.pytest_cache`), or background poll ticks change.
  - ONLY commit and push when real, functional source code (`frontend/`, `backend/`, `agents/`, `scripts/`) or documentation (`tasks/`, `README.md`, `tasks.md`) has been modified.

---

## 4. Daily Git Synchronization & Automatic Conflict Resolution
- **Morning (Start of Day):** Run `python scripts/start_of_day.py` or `git pull origin main` to pull latest remote changes before work begins.
- **Automatic Merge Conflict Resolution:** If any git merge or rebase conflicts occur during pull, automatically analyze conflicting files, resolve all conflicts cleanly, stage changes (`git add .`), and complete the commit.

---

## 📝 5. Automatic README.md Maintenance & Per-Turn Conversation Memory Directives
- **Automatic README Updates:** Whenever new features, components, or services are added, automatically update [`README.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/README.md).
- **Per-Turn Memory Logging:** Update `memory/conversations/assistant_conversation.jsonl`, `memory/task_history/YYYY-MM-DD_task_history.jsonl`, and `memory/agent_state.json` on every user interaction turn.

---

## 🤖 6. Mandatory README Agent LLM Model Allocation Table Preservation Rule
- **Strict Preservation Mandate:** Whenever modifying or updating [`README.md`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/README.md), **DO NOT remove, delete, or modify** the `## 🤖 Autonomous Agent Fleet & LLM Model Allocation` table.
- The table must permanently preserve the assigned model for each agent:
  - **Orchestrator Agent**: `Claude 3.5 Opus` (`claude-opus-4-5`)
  - **Builder Agent**: `Claude 3.5 Opus` (`claude-opus-4-5`)
  - **Tester Agent**: `Claude 3.5 Sonnet` (`claude-sonnet-4-5`)
  - **Sprint Watcher**: `Claude 3.5 Haiku` (`claude-haiku-4-5`)
  - **Git Agent**: `Claude 3.5 Haiku` (`claude-haiku-4-5`)
  - **Plane Agent**: `Claude 3.5 Haiku` (`claude-haiku-4-5`)

---

## 🧠 7. Mandatory Per-Turn Conversation Memory Update Directive
- **Mandatory Memory Sync Rule:**
  - On every user conversation exchange, the agent MUST automatically invoke `update_conversation_memory()` in [`agents/memory_manager.py`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/agents/memory_manager.py).
  - Appends query and response summaries to `memory/conversations/assistant_conversation.jsonl`, updates daily task logs in `memory/task_history/YYYY-MM-DD_task_history.jsonl`, and updates `memory/agent_state.json`.
