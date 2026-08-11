@echo off
TITLE "AI Analytics Dashboard — Autonomous Agent & Deployment Fleet"
echo =========================================================================
echo ⚡ AI Analytics Dashboard — Comprehensive Autonomous Deployment Launcher
echo =========================================================================

set "APP_ROOT=%~dp0.."
cd /d "%APP_ROOT%"

echo.
echo [STEP 1/6] 📦 Checking ^& Installing Python Dependencies...
pip install -r requirements.txt

echo.
echo [STEP 2/6] 🟢 Checking ^& Installing Node.js Frontend Dependencies...
cd /d "%APP_ROOT%\frontend"
if not exist "node_modules" (
    echo Installing node_modules...
    npm install
) else (
    echo node_modules verified!
)
cd /d "%APP_ROOT%"

echo.
echo [STEP 3/6] 🎭 Installing Playwright E2E Browser Testing Binaries...
python -m playwright install chromium

echo.
echo [STEP 4/6] 🔀 Synchronizing Git Repository...
git pull origin main

echo.
echo [STEP 5/5] 🚀 Launching All Autonomous Fleet Services, Agents, Memory ^& Watchdog...

echo 1. Launching FastAPI Backend API Server (Port 8000)...
start "FastAPI Backend Server" /D "%APP_ROOT%\backend" cmd /k python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

echo 2. Launching Vite Frontend Dev Server (Port 5173)...
start "Vite Frontend Dev Server" /D "%APP_ROOT%\frontend" cmd /k npm run dev -- --host 0.0.0.0

echo 3. Launching Sprint Watcher Continuous Agent Loop (15s Interval)...
start "Sprint Watcher Agent" /D "%APP_ROOT%" cmd /k python agents/sprint_watcher_agent.py --interval 15

echo 4. Launching Orchestrator Agent Fleet Supervisor...
start "Orchestrator Agent" /D "%APP_ROOT%" cmd /k python agents/orchestrator_agent.py --supervise

echo 5. Launching Agent ^& Server Health Watchdog Supervisor...
start "Agent Watchdog Supervisor" /D "%APP_ROOT%" cmd /k python scripts/agent_watchdog.py

echo 6. Launching Builder Agent System Builder...
start "Builder Agent" /D "%APP_ROOT%" cmd /k python agents/builder_agent.py --task-id AAD-AUTO --task-title System_Integrity_Verification --description Autonomous_Fleet_Worker

echo 7. Launching Tester Agent Test Suite Runner (Unit + Playwright E2E)...
start "Tester Agent" /D "%APP_ROOT%" cmd /k python agents/tester_agent.py

echo 8. Launching Memory Agent Persistent State Manager...
start "Memory Agent" /D "%APP_ROOT%" cmd /k python agents/memory_manager.py --daemon

echo 8. Launching MCP Server Fleet (Plane, GitHub, Memory, Browser)...
start "MCP Plane Agent" /D "%APP_ROOT%" cmd /k python -m agents.plane_agent
start "MCP Git Agent" /D "%APP_ROOT%" cmd /k python agents/git_agent.py --standby

echo =========================================================================
echo 🎉 Autonomous Agent Fleet, Watchdog, Memory ^& MCP Servers Fully Active!
echo -------------------------------------------------------------------------
echo 🌐 Frontend UI:     http://localhost:5173
echo ⚙️ Backend API:     http://localhost:8000 (Swagger docs: http://localhost:8000/docs)
echo 🛡️ Watchdog:        Agent Watchdog Supervisor monitoring servers ^& agents (auto-restarting on failure)
echo 🧠 Memory Agent:    Persistent State ^& Context Storage active
echo 🧪 Tester Agent:    Automated Pytest Unit + Playwright Browser E2E Runner active
echo 🔌 MCP Servers:     Plane, GitHub, Memory, Browser MCP Servers active
echo 🤖 Active Agents:   Sprint Watcher (60s), Builder Agent, Tester Agent, Orchestrator
echo 🌙 EOD Push Script: python scripts/end_of_day.py executed automatically!
echo 🔄 Auto-Git Push:   Enabled background auto-commit ^& push to origin/main
echo =========================================================================
pause
