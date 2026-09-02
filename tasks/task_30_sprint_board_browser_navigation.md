# 📌 TASK 30 — Sprint Board Real Browser Navigation & Dynamic Dropdown Testing (`#sprint-board-browser`)

## 📋 Overview
This task specification governs the **Real Browser End-to-End Navigation & Interactive Verification** for the Sprint Board page (`http://localhost:5173/sprints`).

It enforces automated browser verification via Playwright to guarantee that upon opening, refreshing, and interacting with the UI, the Workspace Selector and Project Scope Dropdown dynamically fetch, render, and filter live workspace projects from the Plane REST API.

---

## 🔍 Detailed Test Case & User Navigation Procedure

### 1. Cold Browser Launch & Route Navigation
1. Launch Chromium browser in 1440x900 viewport.
2. Navigate directly to `http://localhost:5173/sprints`.
3. Assert page title contains `"Sprint"` and Sprint Header Banner renders cleanly.

### 2. Browser Page Refresh Scenario
1. Trigger browser page reload (`page.reload()` / `F5`).
2. Assert `#sprint-board-workspace-select` element mounts cleanly.
3. Assert `#sprint-board-project-select` element mounts cleanly.

### 3. Dynamic Dropdown Population & Option Verification
1. Locate `#sprint-board-workspace-select` and verify selected workspace is `"agentbuilder"`.
2. Locate `#sprint-board-project-select` dropdown.
3. Extract all `<option>` elements from DOM.
4. Verify all dynamic project choices exist:
   - `⚡ All Projects (Aggregate Workspace Tasks)`
   - `AgenticOps AI - Enterprise Control Plane`
   - `AI Analytics Dashboard`
   - `agentbuilder`

### 4. Interactive Project Selection & Kanban Task Card Filtering
1. Click `#sprint-board-project-select` and select `AI Analytics Dashboard`.
2. Verify Kanban columns (**Backlog**, **To Do**, **In Progress**, **Completed**) update automatically.
3. Verify task cards display project badge tags (`🏷️ AI Analytics Dashboard`).

---

## 🤖 Automated Execution & Quality Gate

- **Playwright Test File:** [`tests/browser/test_sprint_board_browser.py`](file:///c:/Users/manik/Downloads/c&s/mani_personal/ai_analytics_dashboard/tests/browser/test_sprint_board_browser.py)
- **Execution Command:** `python -m pytest tests/browser/test_sprint_board_browser.py -v -s`
- **Visual Artifact Evidence:** `sprint_board_browser_verification.png`

---

## 📊 Summary Matrix Entry
- **Category:** `📋 Plane Sprint Board Screen & Multi-Project Kanban`
- **Case ID:** `TC-SPRINT-05`
- **Expected Result:** "Navigating to Sprint Board and selecting workspace/project dropdowns dynamically reloads sprint board tasks and populates all workspace project choices."
- **Actual Result:** "Successfully verified Playwright browser opens Sprint Board, refreshes page, and populates project dropdown options ('All Projects', 'AgenticOps AI', 'AI Analytics Dashboard', 'agentbuilder')."
