"""
FastAPI Backend — AI Analytics Dashboard
Main application entry point with CORS, routes, and health check.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import uvicorn
from dotenv import load_dotenv
import sys
import threading
from pathlib import Path
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR / "agents") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "agents"))
if str(ROOT_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "scripts"))

from routers import data, analytics, charts, sprints, mcp

load_dotenv()


def _auto_launch_fleet():
    """Launch the full agent fleet in the background when the backend starts."""
    try:
        # Warn early if Anthropic key is missing — builder agent will fail without it
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not anthropic_key or anthropic_key.startswith("<"):
            print("[backend] WARNING: ANTHROPIC_API_KEY is not set in .env — Builder agent will fail when picking tasks.")
        else:
            print(f"[backend] Anthropic API key detected ({anthropic_key[:10]}...).")

        from fleet_health import ensure_fleet_running
        from server_health import ensure_servers_running
        import time
        # Small delay so uvicorn fully binds port 8000 first
        time.sleep(3)
        print("[backend] Auto-launching agent fleet...")
        restarted = ensure_fleet_running(include_orchestrator=True)
        if restarted:
            print(f"[backend] Started agents: {', '.join(restarted)}")
        else:
            print("[backend] Agent fleet already running.")
    except Exception as e:
        print(f"[backend] Fleet auto-launch error (non-fatal): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup: launch agents in a background thread so uvicorn isn't blocked ──
    t = threading.Thread(target=_auto_launch_fleet, daemon=True, name="fleet-launcher")
    t.start()
    yield
    # ── Shutdown (nothing to clean up) ──────────────────────────────────────────

# ── App Setup ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AgenticOps AI API",
    description="Backend API for AgenticOps AI — MCP-Driven Autonomous Enterprise Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────────
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(data.router, prefix="/api/data", tags=["Data"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(charts.router, prefix="/api/charts", tags=["Charts"])
app.include_router(sprints.router, prefix="/api/sprints", tags=["Sprints"])
app.include_router(mcp.router, prefix="/api/mcp", tags=["MCP"])


# ── Warehouse Statistics Endpoint (AAD-5 Specification) ─────────────────────────
@app.get("/api/warehouse/statistics", tags=["Warehouse"])
def warehouse_statistics(
    target_db: str = "pg_dev",
    oerdte: str = "",
    batch_id: str = "",
    oewhse: str = "",
    oeinv: str = "",
    from_date: str = "",
    to_date: str = "",
    only_scratches: bool = False,
    limit: int = 20,
    offset: int = 0
):
    try:
        from app.warehouse_service import get_warehouse_statistics
    except ImportError as ie:
        return JSONResponse(
            {"status": "error", "message": f"Warehouse service not available: {ie}"},
            status_code=503
        )
    try:
        return get_warehouse_statistics(
            target_db=target_db,
            oerdte=oerdte,
            batch_id=batch_id,
            oewhse=oewhse,
            oeinv=oeinv,
            from_date=from_date,
            to_date=to_date,
            only_scratches=only_scratches,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


# ── Agents Status Endpoint ───────────────────────────────────────────────────────
@app.get("/api/agents/status", tags=["Agents"])
def get_agents_status():
    # agents/ is already on sys.path (injected at startup) — import directly,
    # NOT as "agents.memory_manager" which requires an agents package on PYTHONPATH.
    try:
        from memory_manager import (
            get_dynamic_agent_statuses, load_state,
            get_pipeline_status, is_agent_working, get_task_queue,
        )
        dynamic_agents = get_dynamic_agent_statuses()
        state = load_state()
        pipeline = get_pipeline_status()
        return JSONResponse({
            "status": "success",
            "agents": dynamic_agents,
            "last_active": state.get("last_active"),
            "pipeline": pipeline,
            "task_queue": get_task_queue(),
            "agent_working": is_agent_working(),
            "agent_working_task": state.get("agent_working_task", ""),
            "agent_working_since": state.get("agent_working_since"),
        })
    except Exception as e:
        print(f"[Agents API] Error: {e}")
        try:
            from memory_manager import load_state
            state = load_state()
        except Exception:
            state = {}
        return JSONResponse({
            "status": "success",
            "agents": state.get("agents", {}),
            "last_active": state.get("last_active"),
            "pipeline": state.get("pipeline", {}),
            "task_queue": state.get("task_queue", {}),
            "agent_working": state.get("agent_working", False),
            "agent_working_task": state.get("agent_working_task", ""),
            "agent_working_since": state.get("agent_working_since"),
        })


# ── Health Check ───────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["Health"])
async def health_check():
    return JSONResponse({
        "status": "healthy",
        "version": "1.0.0",
        "service": "AI Analytics Dashboard API"
    })


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "AI Analytics Dashboard API",
        "docs": "/docs",
        "health": "/api/health"
    }


# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
