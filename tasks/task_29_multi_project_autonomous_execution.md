# 📋 Task 29: Multi-Project Workspace Task Scanning & End-to-End Execution Mandate

## Overview
This task specification enforces **Multi-Project Workspace Scanning** for workspace `agentbuilder` and strictly mandates **End-to-End Code Implementation & Automated Testing** before any Plane task is closed.

---

## 🏢 1. Workspace & Multi-Project Configuration

### Target Workspaces & Dynamic New Workspace Rule
- **Primary Workspace:** `agentbuilder`
- **Dynamic Auto-Discovery Rule:** If the user creates **ANY NEW WORKSPACE** in Plane under the API key, `list_workspaces()` and `/api/sprints/workspaces` automatically detect and list the new workspace. Selecting the new workspace immediately scans all projects and tasks within it.

### Monitored Projects (Auto-Discovered)
1. **`agentbuilder`** (Project Identifier: `AGENT`)
2. **`AI Analytics Dashboard`** (Project Identifier: `AAD`)
3. **`AgenticOps AI - Enterprise Control Plane`** (Project Identifier: `AGENTICOPS`)
4. *Any newly created projects inside any existing or new Plane workspace.*

---

## 🔄 2. Multi-Project Scanning Policy

- **Workspace-Wide Aggregation:** `SprintWatcherAgent` and FastAPI backend router (`/api/sprints/tasks`) automatically query `list_projects("agentbuilder")` and scan open work items across **ALL 3 projects** simultaneously.
- **Actionable States Filtered:**
  - 📥 **Backlog** (`unstarted`, `backlog`)
  - 📝 **To Do** (`todo`, `to_do`, `triaged`)
  - ⚡ **In Progress** (`started`, `in_progress`, `active`)

---

## 🚨 3. Mandatory End-to-End Implementation & Testing Pipeline Rule

> [!IMPORTANT]
> **STRICT EXECUTION DIRECTIVE:** Agents are strictly forbidden from simply changing a task status to `completed` without doing the work. Every picked-up task MUST go through real code implementation, bug fixing, and automated test validation before state transition to `completed`.

```
┌──────────────────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│ 1. Multi-Workspace & Project Pickup  │ ───► │ 2. Code Implementation  │ ───► │ 3. Automated Test Gate  │
│ (sprint_watcher_agent scanner)       │      │ (builder_agent patch)   │      │ (pytest & playwright)   │
└──────────────────────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
                                                                               │
                                                                               ▼
┌─────────────────────────┐                                       ┌─────────────────────────┐
│ 5. Auto EOD Git Push    │ ◄──────────────────────────────────── │ 4. Finalize & Close     │
│ (git_agent / origin)    │                                       │ (Plane REST API status) │
└─────────────────────────┘                                       └─────────────────────────┘
```

### Mandatory Execution Steps:
1. **Pickup & In-Progress State:** Mark task as `in_progress` in the specific target project where the issue resides.
2. **Real Code Modifications (`builder_agent.py`):** Analyze task title and description requirements, locate affected source files, and apply real code patches (FastAPI router endpoints, React frontend components, styling, or service layers).
3. **Quality Gate Testing (`tester_agent.py`):** Execute pytest unit test suite (`pytest tests/unit/`) and Playwright browser E2E suite (`pytest tests/browser/`).
4. **Conditional Task Completion:**
   - **If Tests PASS:** Update task status to `completed` on Plane REST API and append test execution log comment.
   - **If Tests FAIL:** Keep task open, mark as `failed` / `cancelled`, and log failure output so Builder Agent can attempt fixes.

---

## 🖥️ 4. Sprint Board UI Telemetry & Navigation

- **Sprint Board UI (`/sprints` & Dashboard Component):**
  - Displays 4 Kanban columns (**Backlog**, **To Do**, **In Progress**, **Completed**).
  - Renders project badges (`🏷️ agentbuilder`, `🏷️ AI Analytics Dashboard`, `🏷️ AgenticOps AI`) on every task card.
  - Features Workspace Dropdown (`agentbuilder`) and Project Scope Selector (`⚡ All Projects`).
