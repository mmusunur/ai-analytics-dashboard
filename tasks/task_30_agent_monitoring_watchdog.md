# 📌 TASK 30 — Real-Time Agent Monitoring & Watchdog Supervisor (`#agent-monitoring`)

## 📋 Task Overview
This task specification governs the **Real-Time Agent Monitoring, Health Status Reporting, and Self-Healing Watchdog Engine**.

---

## 🛠️ Architecture & Core Components

### 1. Watchdog Process Supervisor (`scripts/agent_watchdog.py`)
- **Script:** [`scripts/agent_watchdog.py`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/scripts/agent_watchdog.py)
- **Helper:** [`scripts/server_health.py`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/scripts/server_health.py) — `ensure_servers_running()`, port checks
- **Role:** Continuously inspects port availability (`8000`, `5173`) and sprint watcher process (`run_sprint_watcher.py` or `sprint_watcher_agent.py`).
- **Self-Healing Directive:** If backend, frontend, or sprint watcher crashes, `agent_watchdog.py` automatically restarts the process immediately without user intervention.

### 2. Backend Agent Status API (`/api/agents/status`)
- **Router:** [`backend/main.py`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/backend/main.py)
- **Role:** Returns JSON status objects for all 6 autonomous agents (`status: "running"`, `current_task`, `last_heartbeat`, `tasks_completed`).

### 3. Frontend Agent Activity Tracker (`AgentTaskActivityTracker.jsx`)
- **Component:** [`frontend/src/components/AgentTaskActivityTracker.jsx`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/frontend/src/components/AgentTaskActivityTracker.jsx)
- **Sidebar Integration:** Embedded into [`frontend/src/pages/Dashboard.jsx`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/frontend/src/pages/Dashboard.jsx) & Sidebar. Displays real-time task pickup stream, active agent phases (`1. Picked Up` ➔ `2. Building` ➔ `3. Testing` ➔ `4. Done`), and working indicators.
