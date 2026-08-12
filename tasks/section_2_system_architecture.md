# 🖥️ Section 2: System Architecture & Data Flow

This document details the core architecture, framework dependencies, and data flow pipelines of the **AI Analytics Dashboard**.

---

## 1. Stack Architecture
- **Frontend**: React + Vite (ESBuild), TailwindCSS / Vanilla CSS, Lucide Icons, Recharts, Framer Motion.
- **Backend API**: Python 3.10 FastAPI (`backend/main.py`), Uvicorn on `http://localhost:8000`.
- **Database Layer**: PostgreSQL (`sptnintgdb`), Oracle DEV/F1, and CSV Mock Fallback.
- **Plane PM Integration**: Plane REST API (`plane_agent.py`) synchronized with `SprintWatcherAgent`.

---

## 2. Dynamic Data Flow Rules

### 2.1 Dual Search Architecture (Task 36)
The dashboard operates in one of two mutually exclusive search modes:

| Mode | Trigger | Date (`oerdte`) | Source |
|------|---------|-----------------|--------|
| **Global Header** | `#submit-db-btn` or global whse change | Selected order date | Task 1 |
| **AI Copilot** | `#copilot-input` + Ask AI | Empty (`''`) — all dates | Task 14 |

See [`tasks/task_36_dual_search_global_vs_copilot.md`](task_36_dual_search_global_vs_copilot.md) for full specification.

### 2.2 Parameter Propagation
1. **Global Mode:** Header controls (`#global-date-picker`, `#global-db-selector`, `#global-whse-selector`) propagate `oerdte`, `target_db`, and `oewhse` to `/api/charts/*` and `/api/warehouse/statistics`.
2. **Copilot Mode:** Copilot POST sends `oerdte=""`. Dashboard widgets sync to no-date queries until Submit or Clear restores global mode.
3. **Single Warehouse Filtering Rule:** When a warehouse filter is active, Bar Chart and Scatter Plot display data ONLY for that selected warehouse facility.
