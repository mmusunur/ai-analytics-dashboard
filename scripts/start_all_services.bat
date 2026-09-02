@echo off
TITLE "AgenticOps AI — Full Stack Launcher"
echo =========================================================================
echo  AgenticOps AI Dashboard — One-Click Startup
echo =========================================================================

set "APP_ROOT=%~dp0.."
set "VENV_PY=%APP_ROOT%\.venv\Scripts\python.exe"
cd /d "%APP_ROOT%"

:: Verify venv exists
if not exist "%VENV_PY%" (
    echo [ERROR] Virtual environment not found at .venv\Scripts\python.exe
    echo Please run: python -m venv .venv  and then  .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo [1/2] Launching FastAPI Backend (port 8000) — agents auto-start with it...
start "AgenticOps Backend + Agents" /D "%APP_ROOT%\backend" cmd /k "%VENV_PY%" -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

echo Waiting 4 seconds for backend to bind...
timeout /t 4 /nobreak >nul

echo.
echo [2/2] Launching Vite Frontend (port 5173)...
start "AgenticOps Frontend" /D "%APP_ROOT%\frontend" cmd /k npm run dev -- --host 0.0.0.0

echo.
echo =========================================================================
echo  All services launched!
echo.
echo   Frontend UI  : http://localhost:5173
echo   Backend API  : http://localhost:8000
echo   API Docs     : http://localhost:8000/docs
echo.
echo  Agents (Sprint Watcher, Orchestrator, Memory, Git) start automatically
echo  3 seconds after the backend is ready — no manual steps needed.
echo =========================================================================
pause
