"""
Builder Rules — Deterministic code changes when LLM is unavailable or as primary handlers.
Ensures the sprint pipeline can implement common Plane tasks end-to-end without an API key.
"""

import re
from pathlib import Path
from rich.console import Console

console = Console(legacy_windows=False)


def _write_if_changed(path: Path, new_content: str) -> bool:
    if not path.exists():
        return False
    old = path.read_text(encoding="utf-8")
    if old == new_content:
        return False
    path.write_text(new_content, encoding="utf-8")
    return True


def _verify_hide_already_applied(root_dir: Path) -> bool:
    dashboard = root_dir / "frontend" / "src" / "pages" / "Dashboard.jsx"
    if dashboard.exists():
        dash = dashboard.read_text(encoding="utf-8")
        if "<CopilotSearchFixes" in dash or "<WarehouseAnalytics" in dash or "<AgentTaskActivityTracker" in dash:
            return False
    return True


def _hide_dashboard_extras(root_dir: Path) -> list:
    """Hide copilot fixes, warehouse stats widgets, and agent tracker from dashboard page only."""
    modified = []
    dashboard = root_dir / "frontend" / "src" / "pages" / "Dashboard.jsx"
    if dashboard.exists():
        content = dashboard.read_text(encoding="utf-8")
        new_content = content
        for block in [
            r"\s*<CopilotSearchFixes\s*/>\n",
            r"\s*<WarehouseAnalytics\s*/>\n",
            r"\s*<AgentTaskActivityTracker\s*/>\n",
        ]:
            new_content = re.sub(block, "\n", new_content)
        if _write_if_changed(dashboard, new_content):
            modified.append("Dashboard.jsx")
            console.print("[green]OK: Removed CopilotSearchFixes, WarehouseAnalytics, AgentTaskActivityTracker from Dashboard[/green]")

        # Remove now-unused imports
        content = dashboard.read_text(encoding="utf-8")
        for imp in [
            "import CopilotSearchFixes from '../components/CopilotSearchFixes';\n",
            "import WarehouseAnalytics from '../components/WarehouseAnalytics'\n",
            "import AgentTaskActivityTracker from '../components/AgentTaskActivityTracker'\n",
        ]:
            content = content.replace(imp, "")
        _write_if_changed(dashboard, content)

    return modified


def _load_task_spec_context(root_dir: Path, task_title: str, description: str) -> str:
    """Load matching task spec from tasks/ folder to enrich builder context."""
    tasks_dir = root_dir / "tasks"
    if not tasks_dir.exists():
        return ""
    keywords = [w.lower() for w in re.findall(r"[a-zA-Z]{4,}", f"{task_title} {description}")][:8]
    if not keywords:
        return ""
    chunks = []
    for md in sorted(tasks_dir.glob("*.md")):
        try:
            text = md.read_text(encoding="utf-8")
            if any(kw in text.lower() for kw in keywords):
                chunks.append(f"--- {md.name} ---\n{text[:2000]}")
        except Exception:
            pass
    return "\n\n".join(chunks[:3])


def apply_rule_based_fixes(root_dir: Path, task_title: str, description: str, intents: list) -> list:
    """
    Apply deterministic code changes for known task patterns.
    Returns list of modified file names.
    """
    modified = []
    text = f"{task_title} {description}".lower()

    hide_intents = {
        "HIDE_UI_CONTENT", "REMOVE_UNWANTED_CONTENT", "HIDE_ITEMS_FROM_UI",
    }
    hide_matched = bool(hide_intents & set(intents)) or any(
        p in text
        for p in [
            "remove unwanted", "hide items", "hide unwanted", "remove the unwanted",
            "copilot search fixes", "warehouse level statistics", "agent monitor",
            "sprint board",
        ]
    )
    if hide_matched:
        modified.extend(_hide_dashboard_extras(root_dir))
        if not modified and _verify_hide_already_applied(root_dir):
            console.print("[green]OK: Hide-unwanted-content task already applied in codebase[/green]")
            modified.append("already_applied")
        return modified

    if "BROWSER_HEADER_TITLE" in intents or "browser heading" in text or "tab title" in text:
        index_html = root_dir / "frontend" / "index.html"
        if index_html.exists():
            content = index_html.read_text(encoding="utf-8")
            new_content = re.sub(r"<title>.*?</title>", "<title>AgenticOps AI</title>", content)
            if _write_if_changed(index_html, new_content):
                modified.append("index.html")

    if "SPRINT_AGENT_FIX" in intents:
        # Ensure agent entrypoints have ROOT_DIR on sys.path for memory imports
        for agent_file in ["sprint_watcher_agent.py", "builder_agent.py", "tester_agent.py"]:
            path = root_dir / "agents" / agent_file
            if path.exists():
                content = path.read_text(encoding="utf-8")
                if 'sys.path.insert(0, str(ROOT_DIR))' not in content and "ROOT_DIR = Path" in content:
                    new_content = content.replace(
                        'ROOT_DIR = Path(__file__).parent.parent\n',
                        'ROOT_DIR = Path(__file__).parent.parent\n'
                        'if str(ROOT_DIR) not in sys.path:\n    sys.path.insert(0, str(ROOT_DIR))\n',
                        1,
                    )
                    if _write_if_changed(path, new_content):
                        modified.append(agent_file)

    if "DATA_ANALYTICS_ML" in intents or re.search(r"\bdata analytics\b", text):
        from builder_helpers import build_data_analytics
        modified.extend(build_data_analytics(root_dir))
        if modified:
            return modified

    if "ADDITIONAL_FEATURES" in intents or re.search(r"additional features|aditional features", text):
        from builder_helpers import build_dynamic_component, wire_component_to_dashboard
        comp_name = build_dynamic_component(root_dir, task_title, description)
        if comp_name:
            modified.append(f"{comp_name}.jsx")
            if wire_component_to_dashboard(root_dir, comp_name):
                modified.append("Dashboard.jsx")
        if modified:
            return modified

    # General fallback: scaffold a component + unit test when nothing else matched
    if not modified:
        from builder_helpers import build_dynamic_component, wire_component_to_dashboard
        comp_name = build_dynamic_component(root_dir, task_title, description)
        if comp_name:
            comp_path = root_dir / "frontend" / "src" / "components" / f"{comp_name}.jsx"
            if comp_path.exists():
                modified.append(f"{comp_name}.jsx")
            if wire_component_to_dashboard(root_dir, comp_name):
                modified.append("Dashboard.jsx")

    spec = _load_task_spec_context(root_dir, task_title, description)
    if spec:
        console.print(f"[dim]Loaded task spec context ({len(spec)} chars) from tasks/[/dim]")

    return modified
