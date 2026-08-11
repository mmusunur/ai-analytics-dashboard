"""
Builder LLM — LLM Task Comprehension Engine and Code Patch Generator for Builder Agent.
Keeps agents/builder_agent.py lightweight (< 250 lines).
"""

import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console(legacy_windows=False)


def llm_generate_code_patch(root_dir: Path, codebase_map: dict, task_title: str, description: str, file_key: str, file_content: str) -> str:
    """
    Call the Anthropic LLM to generate a real targeted code patch.
    Returns modified file content (full file), or empty string on failure.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or not api_key.startswith("sk-"):
        return ""

    file_path = str(codebase_map.get(file_key, file_key))
    console.print(f"[magenta]🤖 Calling LLM to patch {file_key} for: {task_title}[/magenta]")

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        tasks_md_path = root_dir / "tasks.md"
        tasks_context = tasks_md_path.read_text(encoding="utf-8")[:3000] if tasks_md_path.exists() else ""

        prompt = f"""You are an expert full-stack developer working on an AI Analytics Dashboard (React + FastAPI + PostgreSQL).

## Task to implement:
Title: {task_title}
Description: {description or "See title"}

## File to modify: {file_path}
## Current content:
```
{file_content[:6000]}
```

## Architecture context (from tasks.md):
{tasks_context}

## Your job:
1. Carefully read the task title and description.
2. Identify EXACTLY what code changes are needed in this specific file.
3. Return the COMPLETE modified file with all necessary changes applied.
4. Do NOT add placeholder comments. Make real, working code changes.
5. Preserve all existing functionality — only change what the task requires.
6. If no changes are needed in this file for this task, return the word UNCHANGED.

Return ONLY the complete modified file content (no markdown fences, no explanation).
If no changes needed, return exactly: UNCHANGED"""

        resp = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        result = resp.content[0].text.strip()
        if result == "UNCHANGED" or len(result) < 50:
            return ""
        console.print(f"[green]✅ LLM generated real code patch for {file_key}[/green]")
        return result
    except Exception as e:
        console.print(f"[yellow]⚠️ LLM patch generation error: {e}[/yellow]")
        return ""


def apply_intent_fixes(root_dir: Path, codebase_map: dict, task_title: str, description: str, intents: list) -> list:
    """
    For each detected intent, read target file, attempt LLM patch, and write back.
    Returns list of files actually modified.
    """
    modified_files = []
    full_text = f"{task_title} {description}".lower()

    intent_file_map = {
        "PAGINATION_AND_TOTAL_RECORDS":        ["table", "dashboard"],
        "DATE_PARAMETER_FILTERING":            ["dashboard", "warehouse_svc"],
        "AI_COPILOT_DATE_AGNOSTIC_QUERY":      ["copilot", "analytics_py", "dashboard"],
        "SCRATCH_QUANTITY_ANOMALY_ALERTS":     ["anomaly", "analytics_py"],
        "CHARTS_AND_VISUALIZATION_ALIGNMENT":  ["charts_py", "dashboard"],
        "NAVBAR_AND_SIDEBAR_NAVIGATION":       ["navbar", "dashboard"],
        "MULTI_TARGET_DATABASE_ARCHITECTURE":  ["warehouse_svc", "analytics_py"],
        "SPRINT_AGENT_FIX":                    ["dashboard"],
        "SPRINT_BOARD_STYLING_AND_DROPDOWNS":  ["dashboard"],
        "UI_PERFORMANCE_AND_REFRESH":          ["dashboard"],
        "ROUTE_AND_NAVIGATION_FIX":            ["navbar", "dashboard"],
        "BACKEND_QUERY_FIX":                   ["warehouse_svc", "analytics_py"],
        "API_ENDPOINT_FIX":                    ["analytics_py", "charts_py"],
        "HIDE_UI_CONTENT":                     ["dashboard", "navbar"],
        "REMOVE_UNWANTED_CONTENT":             ["dashboard", "navbar"],
        "TEST_COVERAGE_AND_EXCEL":             ["dashboard"],
    }

    files_to_patch = []
    for intent in intents:
        if intent in intent_file_map:
            for fk in intent_file_map[intent]:
                if fk not in files_to_patch:
                    files_to_patch.append(fk)

    if not files_to_patch or "GENERAL" in (intents[0] if intents else ""):
        if any(k in full_text for k in ["table", "row", "column", "pagination", "page"]):
            files_to_patch.append("table")
        if any(k in full_text for k in ["chart", "bar", "graph", "kpi", "plot"]):
            files_to_patch.append("charts_py")
            files_to_patch.append("dashboard")
        if any(k in full_text for k in ["copilot", "search", "nlp", "ai"]):
            files_to_patch.append("copilot")
            files_to_patch.append("analytics_py")
        if any(k in full_text for k in ["date", "oerdte", "header", "filter"]):
            files_to_patch.append("dashboard")
            files_to_patch.append("warehouse_svc")
        if any(k in full_text for k in ["scratch", "anomaly", "alert", "missing"]):
            files_to_patch.append("anomaly")
            files_to_patch.append("analytics_py")
        if not files_to_patch:
            files_to_patch = ["dashboard", "table"]

    seen = set()
    files_to_patch = [f for f in files_to_patch if not (f in seen or seen.add(f))]

    for file_key in files_to_patch:
        target_path = codebase_map.get(file_key)
        if not target_path or not target_path.exists():
            continue

        current_content = target_path.read_text(encoding="utf-8")
        patched = llm_generate_code_patch(root_dir, codebase_map, task_title, description, file_key, current_content)
        if patched and patched != current_content:
            target_path.write_text(patched, encoding="utf-8")
            console.print(f"[green]✅ Written: {target_path.name}[/green]")
            modified_files.append(str(target_path.name))

    return modified_files
