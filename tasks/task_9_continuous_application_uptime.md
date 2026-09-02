# 📌 TASK 9 — Continuous Application Server Uptime (`#application-uptime`)

## 🖥️ Server Launchers & Mandatory Execution Scripts
- 💻 **Windows Launcher:** [`scripts/start_all_services.bat`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/scripts/start_all_services.bat)
- 🐧 **Linux / macOS Launcher:** [`scripts/start_all_services.sh`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/scripts/start_all_services.sh)

## 🖥️ Server Configurations & Endpoints
- **Backend API Server:**
  - **Command:** `python -m uvicorn main:app --host 127.0.0.1 --port 8000` (inside `backend/`)
  - **URL:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
  - **Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
  - **Health Check:** `GET /api/health`
- **Frontend Dashboard Dev Server:**
  - **Command:** `npm run dev` (inside `frontend/`)
  - **URL:** [http://localhost:5173](http://localhost:5173)

---

## 🎯 Sub-Task Breakdown

### Sub-Task 9.1: 🚀 Backend FastAPI Server Continuous Background Execution
- **Behavior:** Runs continuously in the background on port `8000`. Exposes REST API endpoints for KPI cards, bar charts, scatter plots, correlation heatmaps, and PostgreSQL warehouse sales analytics.

### Sub-Task 9.2: 💻 Frontend Vite Dev Server Continuous Background Execution
- **Behavior:** Runs continuously in the background on port `5173`. Serves the React + Vite dashboard UI with real-time parameter controls, KPI cards, charts, and warehouse data table.

### Sub-Task 9.3: 🩺 Continuous Uptime Monitoring & Auto-Restart Directive
- **Rule:** The USER will NOT start servers manually. The system MUST keep both frontend and backend servers continuously active. If either server goes offline or crashes, the agent MUST automatically relaunch it using [`scripts/start_all_services.bat`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/scripts/start_all_services.bat) / [`scripts/start_all_services.sh`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/scripts/start_all_services.sh), [`scripts/server_health.py`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/scripts/server_health.py), or [`scripts/agent_watchdog.py`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/scripts/agent_watchdog.py) immediately.

### Sub-Task 9.4: 🧪 Pre-Test Server Gate
- Before any Playwright browser test or sprint task closure, call `ensure_servers_running()` from [`scripts/server_health.py`](../scripts/server_health.py). Quality gates MUST fail fast with a clear message if servers cannot be reached within 25 seconds.
