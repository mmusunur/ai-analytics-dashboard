#!/usr/bin/env bash
# AI Analytics Dashboard — Autonomous Agent & Deployment Fleet (Linux/macOS)

set -e

APP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_ROOT"

echo "========================================================================="
echo "⚡ AI Analytics Dashboard — Autonomous Deployment Launcher (Linux/macOS)"
echo "========================================================================="

# Detect Python binary
if [ -f "$APP_ROOT/.venv/Scripts/python.exe" ]; then
    PYTHON="$APP_ROOT/.venv/Scripts/python.exe"
elif [ -f "$APP_ROOT/.venv/bin/python" ]; then
    PYTHON="$APP_ROOT/.venv/bin/python"
elif command -v python3 &>/dev/null && python3 --version &>/dev/null; then
    PYTHON=python3
else
    PYTHON=python
fi

echo "[1/6] 📦 Checking Python Dependencies..."
"$PYTHON" -c "import fastapi, uvicorn, pandas, plotly, anthropic" 2>/dev/null || "$PYTHON" -m pip install -r requirements.txt

echo "[2/6] 🟢 Checking Node.js Frontend Dependencies..."
cd "$APP_ROOT/frontend"
if [ ! -d "node_modules" ]; then
    npm install
fi
cd "$APP_ROOT"

echo "[3/6] 🎭 Checking Playwright Browser Binaries..."
"$PYTHON" -c "import playwright" 2>/dev/null || "$PYTHON" -m playwright install chromium

echo "[4/6] 🔀 Synchronizing Git Repository..."
git pull origin main || true

echo "[5/6] 🌙 Running End of Day Push Script..."
"$PYTHON" scripts/end_of_day.py || true

echo "[6/6] 🚀 Launching All Background Agent Fleet, Watchdog, Memory & MCP Services..."

# Run FastAPI backend in background
cd "$APP_ROOT/backend"
"$PYTHON" -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Run Vite frontend in background
cd "$APP_ROOT/frontend"
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!

# Run Sprint Watcher agent loop in background
cd "$APP_ROOT"
"$PYTHON" scripts/run_sprint_watcher.py --interval 60 &
WATCHER_PID=$!

# Run Agent Watchdog Supervisor
"$PYTHON" scripts/agent_watchdog.py &
WATCHDOG_PID=$!

# Run Builder agent
"$PYTHON" agents/builder_agent.py --task-id AAD-AUTO --task-title System_Integrity_Verification &
BUILDER_PID=$!

# Run Tester agent
"$PYTHON" agents/tester_agent.py &
TESTER_PID=$!

# Run Memory agent
"$PYTHON" -m agents.memory_manager &
MEMORY_PID=$!

# Run MCP Server Fleet
"$PYTHON" -m agents.plane_agent &
PLANE_MCP_PID=$!

"$PYTHON" -m agents.git_agent &
GIT_MCP_PID=$!

echo "========================================================================="
echo "🎉 Autonomous Agent Fleet, Watchdog, Memory & MCP Servers Fully Active!"
echo "Backend PID:  $BACKEND_PID (http://localhost:8000)"
echo "Frontend PID: $FRONTEND_PID (http://localhost:5173)"
echo "Watcher PID:  $WATCHER_PID (60s poll interval)"
echo "Watchdog PID: $WATCHDOG_PID"
echo "Memory PID:   $MEMORY_PID"
echo "========================================================================="

wait
