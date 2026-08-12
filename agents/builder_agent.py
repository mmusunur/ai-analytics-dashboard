"""
Builder Agent — Receives tasks from Sprint Watcher, generates/updates component code,
and verifies build health. Modularized & lightweight (< 150 lines).
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "agents"))
import utf8_fix

from memory_manager import update_agent_status, log_task_result, update_build_progress, record_build_result, clear_build_progress
from builder_nlp import classify_task_intent_and_intent_map
from builder_llm import apply_intent_fixes
from builder_helpers import build_navbar, build_warehouse_analytics, build_dynamic_component, build_data_analytics
from builder_rules import apply_rule_based_fixes, _load_task_spec_context

console = Console(legacy_windows=False)

CODEBASE_MAP = {
    "table":        ROOT_DIR / "frontend" / "src" / "components" / "WarehouseSalesAnalytics.jsx",
    "dashboard":    ROOT_DIR / "frontend" / "src" / "pages" / "Dashboard.jsx",
    "copilot":      ROOT_DIR / "frontend" / "src" / "components" / "AiDataCopilot.jsx",
    "anomaly":      ROOT_DIR / "frontend" / "src" / "components" / "AnomalyAlertPanel.jsx",
    "charts_py":    ROOT_DIR / "backend" / "routers" / "charts.py",
    "analytics_py": ROOT_DIR / "backend" / "routers" / "analytics.py",
    "warehouse_svc":ROOT_DIR / "backend" / "app" / "warehouse_service.py",
    "navbar":       ROOT_DIR / "frontend" / "src" / "components" / "Navbar.jsx",
}


def run_builder_test_verification() -> bool:
    """Run pytest unit tests to verify codebase health after code modifications."""
    console.print("[cyan]🧪 Running core unit tests to verify build integrity...[/cyan]")
    try:
        res = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/unit/", "-v", "--tb=no", "-q"],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            timeout=60
        )
        if res.returncode == 0:
            console.print("[green]✅ Unit test suite PASSED[/green]")
            return True
        else:
            console.print(f"[red]❌ Unit test failure:\n{res.stdout[:300]}[/red]")
            return False
    except Exception as e:
        console.print(f"[yellow]⚠️ Test execution failed: {e}[/yellow]")
        return False


def handle_task(
    task_id: str,
    task_title: str,
    description: str,
    priority: str,
    attempt: int = 1,
    retry_context_file: str = "",
) -> bool:
    """
    Autonomous task handler:
    1. Classifies intent from task title + description using NLP/LLM.
    2. Reads target files, applies targeted LLM code patches.
    3. Verifies at least one file was actually modified.
    4. Runs test suite to confirm build health.
    Returns True ONLY if code changes were made AND tests pass.
    Returns False if no files were modified (task left In Progress for manual review).
    """
    update_agent_status("builder", "running", f"Building #{task_id}: {task_title}")
    retry_note = f"\nRetry attempt: {attempt}" if attempt > 1 else ""
    console.print(Panel.fit(
        f"[bold cyan]Builder Agent — Real Implementation[/bold cyan]\n"
        f"Task: {task_title}\n"
        f"ID: {task_id}\n"
        f"Priority: {priority.upper()}{retry_note}",
        border_style="cyan"
    ))

    import time
    build_start = time.time()
    update_build_progress("starting", "Build gate — loading task context", task_id, task_title)

    if attempt > 1 and retry_context_file:
        ctx_path = Path(retry_context_file)
        if ctx_path.exists():
            failure_ctx = ctx_path.read_text(encoding="utf-8", errors="replace")[:4000]
            description = (
                f"{description}\n\n"
                f"=== PREVIOUS TEST RUN FAILED (attempt {attempt - 1}) — FIX THESE ISSUES ===\n"
                f"{failure_ctx}\n"
                f"=== END FAILURE OUTPUT — implement fixes and ensure all tests pass ==="
            )
            console.print(f"[yellow]↻ Retry build with prior test failure context ({len(failure_ctx)} chars)[/yellow]")

    # Step 1: Classify intent (strip retry failure blobs so NLP stays on-task)
    update_build_progress("classifying", "Classifying task intent (NLP + rules)", task_id, task_title)
    clean_desc = (description or "").split("=== PREVIOUS TEST")[0].strip()
    intent_result = classify_task_intent_and_intent_map(task_title, clean_desc)
    intents = intent_result["intents"]
    update_build_progress(
        "classifying",
        f"Detected intents: {', '.join(intents[:4])}",
        task_id, task_title, intents=intents,
    )
    console.print(f"[cyan]Detected intents: {intents}[/cyan]")
    if intent_result.get("target_files"):
        console.print(f"[cyan]LLM target files: {intent_result['target_files']}[/cyan]")

    # Step 2: Component-specific helper builds
    update_build_progress("spec_load", "Loading task spec + target file map", task_id, task_title, intents=intents)
    spec_context = _load_task_spec_context(ROOT_DIR, task_title, description)
    if spec_context:
        description = f"{description}\n\nTask spec reference:\n{spec_context[:3000]}"

    if "BROWSER_HEADER_TITLE" in intents:
        index_html = ROOT_DIR / "frontend" / "index.html"
        if index_html.exists():
            content = index_html.read_text(encoding="utf-8")
            import re
            new_content = re.sub(r'<title>.*?</title>', '<title>AgenticOps AI</title>', content)
            if new_content != content:
                index_html.write_text(new_content, encoding="utf-8")
                console.print("[green]✅ Updated browser tab title in frontend/index.html to 'AgenticOps AI'[/green]")

    if "NAVBAR_AND_SIDEBAR_NAVIGATION" in intents:
        build_navbar(ROOT_DIR, task_title, description)
    if "MULTI_TARGET_DATABASE_ARCHITECTURE" in intents:
        build_warehouse_analytics(ROOT_DIR, task_title, description)

    # Step 3: Snapshot all target files before any LLM changes (for rollback on test failure)
    file_backups: dict = {}
    dynamic_paths: list = []

    def _snapshot(path: Path):
        key = str(path)
        if path.exists():
            file_backups[key] = path.read_text(encoding="utf-8")
        else:
            file_backups[key] = None

    for fkey, fpath in CODEBASE_MAP.items():
        _snapshot(fpath)

    for rel in intent_result.get("target_files") or []:
        p = ROOT_DIR / rel.replace("/", os.sep)
        if p.is_file():
            _snapshot(p)
        elif p.suffix == ".jsx" or rel.endswith(".jsx"):
            dynamic_paths.append(p)
            _snapshot(p)

    # Apply LLM code changes to target files
    update_build_progress("patching", "Applying code patches (LLM + rule-based handlers)", task_id, task_title, intents=intents)
    modified_files = apply_intent_fixes(ROOT_DIR, CODEBASE_MAP, task_title, description, intents)

    # Rule-based fallback when LLM makes no changes (no API key or UNCHANGED responses)
    if not modified_files:
        console.print("[cyan]LLM made no changes — applying rule-based fixes...[/cyan]")
        modified_files = apply_rule_based_fixes(ROOT_DIR, task_title, description, intents)

    if not modified_files:
        console.print(Panel(
            "[yellow]Builder: No code changes generated.[/yellow]\n"
            "No target files matched or all patches returned UNCHANGED.\n"
            "Build gate FAILED — Test will not run until Builder produces changes or fixes.",
            border_style="yellow"
        ))
        update_agent_status("builder", "idle", "Autonomous Builder Agent Active (Listening for tasks)")
        record_build_result(task_id, task_title, [], False, time.time() - build_start, intents=intents)
        return False

    already_done = modified_files == ["already_applied"]
    real_files = [f for f in modified_files if f != "already_applied"]
    update_build_progress(
        "patching",
        f"{'Verify-only — requirements already in codebase' if already_done else f'Modified {len(real_files)} file(s)'}",
        task_id,
        task_title,
        files_modified=real_files,
        build_outcome="verify_only" if already_done else "code_changed",
        intents=intents,
        already_applied=already_done,
    )

    if already_done:
        console.print("[green]Requirements already in codebase — running unit verification before Test gate[/green]")
    else:
        console.print(f"[green]Files modified: {real_files}[/green]")

    # Step 4: Verification — run tests AFTER changes
    update_build_progress("unit_verify", "Running builder unit verification (pytest)", task_id, task_title, intents=intents, already_applied=already_done)
    test_passed = run_builder_test_verification()

    if not test_passed and not already_done:
        # ROLLBACK: LLM changes broke the codebase — restore every modified file
        console.print("[bold red]Tests failed after LLM changes \u2014 rolling back all modified files...[/bold red]")
        rolled_back = []
        for modified_name in modified_files:
            if modified_name == "already_applied":
                continue
            candidates = list(ROOT_DIR.rglob(modified_name))
            if not candidates:
                candidates = [ROOT_DIR / modified_name]
            for fpath in candidates:
                if not fpath.is_file():
                    continue
                key = str(fpath)
                backup = file_backups.get(key)
                if backup is None and fpath.exists():
                    try:
                        fpath.unlink()
                        rolled_back.append(f"deleted:{modified_name}")
                    except OSError:
                        pass
                elif backup is not None:
                    fpath.write_text(backup, encoding="utf-8")
                    rolled_back.append(modified_name)
                break
        console.print(f"[yellow]Rolled back files: {rolled_back}[/yellow]")

    duration = time.time() - build_start
    record_build_result(task_id, task_title, modified_files, already_done, duration, intents=intents)
    update_build_progress(
        "done",
        f"Build gate {'passed' if test_passed else 'failed'} — "
        f"{'verify-only' if already_done else f'{len(real_files)} file(s) changed'} ({duration:.0f}s)",
        task_id,
        task_title,
        files_modified=real_files,
        build_outcome="verify_only" if already_done else "code_changed",
    )
    update_agent_status("builder", "idle", "Autonomous Builder Agent Active (Listening for tasks)")
    return test_passed



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Builder Agent")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--task-title", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--priority", default="medium")
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--retry-context-file", default="")
    args = parser.parse_args()

    success = handle_task(
        args.task_id, args.task_title, args.description, args.priority,
        attempt=args.attempt, retry_context_file=args.retry_context_file,
    )
    sys.exit(0 if success else 1)
