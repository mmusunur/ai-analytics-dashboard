"""MCP registry & health API."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/status")
def mcp_status():
    try:
        from agents.mcp_client import get_mcp_registry
        return JSONResponse({"status": "success", **get_mcp_registry()})
    except Exception as exc:
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)


@router.get("/tools")
def mcp_tools():
    try:
        from agents.mcp_client import load_mcp_config, TOOL_SERVER_MAP
        config = load_mcp_config()
        tools = []
        for sid, meta in config.get("mcpServers", {}).items():
            for tool in meta.get("tools", []):
                name = tool.get("name") if isinstance(tool, dict) else tool
                tools.append({
                    "name": name,
                    "server": sid,
                    "serverName": meta.get("name", sid),
                    "description": tool.get("description", "") if isinstance(tool, dict) else "",
                    "routed": name in TOOL_SERVER_MAP,
                })
        return JSONResponse({"status": "success", "tools": tools, "count": len(tools)})
    except Exception as exc:
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)
