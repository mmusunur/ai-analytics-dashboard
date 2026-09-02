"""Unit tests for MCP client registry."""

from agents.mcp_client import load_mcp_config, TOOL_SERVER_MAP, get_mcp_registry


def test_mcp_config_loads_four_servers():
    config = load_mcp_config()
    assert len(config.get("mcpServers", {})) == 4
    assert "plane" in config["mcpServers"]
    assert "browser" in config["mcpServers"]


def test_tool_server_map_has_plane_tools():
    assert TOOL_SERVER_MAP["update_task_status"] == "plane"
    assert TOOL_SERVER_MAP["git_commit"] == "github"
    assert TOOL_SERVER_MAP["get_task_queue"] == "memory"


def test_mcp_registry_structure():
    reg = get_mcp_registry()
    assert reg["serverCount"] == 4
    assert reg["toolCount"] >= 16
    assert all("health" in s for s in reg["servers"])
    assert all("tools" in s for s in reg["servers"])
