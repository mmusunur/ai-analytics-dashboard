"""
FastAPI Backend — AI Analytics Dashboard
Main application entry point with CORS, routes, and health check.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import uvicorn
from dotenv import load_dotenv
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from routers import data, analytics, charts, sprints, mcp

load_dotenv()

# ── App Setup ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AgenticOps AI API",
    description="Backend API for AgenticOps AI — MCP-Driven Autonomous Enterprise Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
    from app.warehouse_service import get_warehouse_statistics
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


# ── Agents Status Endpoint ───────────────────────────────────────────────────────
@app.get("/api/agents/status", tags=["Agents"])
def get_agents_status():
    from agents.memory_manager import get_dynamic_agent_statuses, load_state, get_pipeline_status, is_agent_working, get_task_queue
    try:
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
        print(f"[Agents API] Failed to compute dynamic agent status: {e}")
        state = load_state()
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
