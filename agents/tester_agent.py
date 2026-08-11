import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

from memory_manager import update_agent_status, log_task_result, save_state, load_state

console = Console(force_terminal=True)
ROOT_DIR = Path(__file__).parent.parent
TESTS_DIR = ROOT_DIR / "tests"
REPORTS_DIR = ROOT_DIR / "reports"


def _run_command(cmd: list[str], cwd: Path = ROOT_DIR) -> tuple[str, str, int]:
    """Run a shell command and return (stdout, stderr, returncode)."""
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode


def update_excel_matrix(
    unit_passed: bool = True,
    browser_passed: bool = True,
    task_id: str | None = None,
):
    """Run tests/generate_test_excel.py to sync TEST_CASES.xlsx (static + sprint dynamic cases)."""
    try:
        cmd = [
            sys.executable,
            str(ROOT_DIR / "tests" / "generate_test_excel.py"),
            "--unit-passed", str(unit_passed).lower(),
            "--browser-passed", str(browser_passed).lower(),
        ]
        if task_id:
            cmd.extend(["--task-id", task_id])
        subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, timeout=120)
        console.print("[bold green][EXCEL] TEST_CASES.xlsx updated (static + sprint task cases).[/bold green]")
    except Exception as e:
        console.print(f"[yellow][EXCEL WARNING] Could not update Excel matrix: {e}[/yellow]")


def register_sprint_task_tests(
    task_id: str,
    task_title: str,
    description: str = "",
    project_name: str = "",
) -> int:
    """Dynamically generate browser test cases from sprint task and persist to registry."""
    sys.path.insert(0, str(ROOT_DIR / "tests"))
    try:
        from sprint_task_test_generator import register_sprint_task
        cases = register_sprint_task(task_id, task_title, description, project_name)
        console.print(
            f"[bold cyan][SPRINT-TESTS] Registered {len(cases)} dynamic browser test case(s) "
            f"for task: {task_title}[/bold cyan]"
        )
        for c in cases:
            console.print(f"  • {c['case_id']}: {c['name']}")
        return len(cases)
    except Exception as e:
        console.print(f"[yellow][SPRINT-TESTS WARNING] Could not register sprint test cases: {e}[/yellow]")
        return 0


def run_unit_tests() -> dict:
    """Run pytest unit tests and return structured results."""
    console.print("\n[bold cyan][UNIT-TESTS] Running Unit Tests...[/bold cyan]")
    REPORTS_DIR.mkdir(exist_ok=True)
    report_path = REPORTS_DIR / "unit_test_report.html"

    stdout, stderr, code = _run_command([
        "python", "-m", "pytest",
        "tests/unit/",
        "-v",
        "--tb=short",
        f"--html={report_path}",
        "--self-contained-html",
        "-q"
    ])

    passed = stdout.count(" PASSED")
    failed = stdout.count(" FAILED")
    errors = stdout.count(" ERROR")

    result = {
        "type": "unit",
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "total": passed + failed + errors,
        "success": code == 0,
        "output": stdout[-3000:],
        "report": str(report_path),
        "timestamp": datetime.now().isoformat()
    }

    if code == 0:
        console.print(f"[bold green][PASS] Unit tests PASSED: {passed}/{result['total']}[/bold green]")
    else:
        console.print(f"[bold red][FAIL] Unit tests FAILED: {failed} failures, {errors} errors[/bold red]")

    return result


def run_browser_tests() -> dict:
    """Run Playwright browser tests (requires frontend :5173 and backend :8000)."""
    console.print("\n[bold cyan][BROWSER-TESTS] Running Playwright Browser Tests...[/bold cyan]")
    REPORTS_DIR.mkdir(exist_ok=True)
    report_path = REPORTS_DIR / "browser_test_report.html"

    # Mandatory: application must be running before browser tests
    sys.path.insert(0, str(ROOT_DIR / "scripts"))
    try:
        from server_health import ensure_servers_running, servers_healthy
        if not servers_healthy()["healthy"]:
            console.print("[yellow][BROWSER-TESTS] Servers not up — auto-starting backend & frontend...[/yellow]")
        if not ensure_servers_running(wait_seconds=25):
            return {
                "type": "browser",
                "passed": 0,
                "failed": 1,
                "total": 1,
                "success": False,
                "output": "Browser tests skipped: frontend (:5173) or backend (:8000) not reachable.",
                "report": str(report_path),
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        console.print(f"[yellow][BROWSER-TESTS] Server health check warning: {e}[/yellow]")

    _run_command(["python", "-m", "playwright", "install", "chromium", "--with-deps"])

    stdout, stderr, code = _run_command([
        "python", "-m", "pytest",
        "tests/browser/",
        "-v",
        "--tb=short",
        f"--html={report_path}",
        "--self-contained-html",
        "-q"
    ])

    passed = stdout.count(" PASSED")
    failed = stdout.count(" FAILED")

    result = {
        "type": "browser",
        "passed": passed,
        "failed": failed,
        "total": passed + failed,
        "success": code == 0,
        "output": stdout[-3000:],
        "report": str(report_path),
        "timestamp": datetime.now().isoformat()
    }

    if code == 0:
        console.print(f"[bold green][PASS] Browser tests PASSED: {passed}/{result['total']}[/bold green]")
    else:
        console.print(f"[bold red][FAIL] Browser tests FAILED: {failed} failures[/bold red]")

    return result


def run_all_tests(
    task_id: str | None = None,
    task_title: str | None = None,
    description: str | None = None,
    project_name: str | None = None,
) -> dict:
    """Run unit + browser tests (including dynamic sprint task cases), update TEST_CASES.xlsx."""
    update_agent_status("tester", "running", "Full test suite")

    if task_id and task_title:
        register_sprint_task_tests(
            task_id, task_title, description or task_title, project_name or ""
        )

    console.print(Panel.fit(
        "[bold]Tester Agent — Full Test Suite & Auto Excel Sync[/bold]\n"
        f"[dim]{datetime.now().strftime('%Y-%m-%d %H:%M')}[/dim]"
        + (f"\n[cyan]Sprint Task: {task_title}[/cyan]" if task_title else ""),
        border_style="cyan"
    ))

    unit_results = run_unit_tests()
    browser_results = run_browser_tests()

    combined = {
        "unit": unit_results,
        "browser": browser_results,
        "total_passed": unit_results["passed"] + browser_results["passed"],
        "total_failed": unit_results["failed"] + browser_results["failed"],
        "all_passed": unit_results["success"] and browser_results["success"],
        "timestamp": datetime.now().isoformat(),
        "task_id": task_id,
        "task_title": task_title,
    }

    # Always update Excel with static + dynamic sprint cases and last run results
    update_excel_matrix(
        unit_passed=unit_results["success"],
        browser_passed=browser_results["success"],
        task_id=task_id,
    )
    if combined["all_passed"]:
        console.print("[bold green][EXCEL] TEST_CASES.xlsx updated after full suite PASS.[/bold green]")
    else:
        console.print("[bold yellow][EXCEL] TEST_CASES.xlsx updated with FAIL results for review.[/bold yellow]")

    # Update state with test results
    state = load_state()
    if "agents" not in state:
        state["agents"] = {}
    if "tester" not in state["agents"]:
        state["agents"]["tester"] = {}
    state["agents"]["tester"]["last_test_results"] = {
        "unit": unit_results["success"],
        "browser": browser_results["success"],
        "passed": combined["total_passed"],
        "failed": combined["total_failed"]
    }
    save_state(state)

    status = "completed" if combined["all_passed"] else "failed"
    log_task_result(
        "TEST-RUN",
        "Full Test Suite",
        "tester",
        status,
        f"Unit: {unit_results['passed']}/{unit_results['total']} | Browser: {browser_results['passed']}/{browser_results['total']}"
    )

    update_agent_status("tester", "idle")

    if combined["all_passed"]:
        console.print(Panel(
            f"[bold green]✅ ALL TESTS PASSED! TEST_CASES.xlsx UPDATED![/bold green]\n"
            f"Unit: {unit_results['passed']}/{unit_results['total']} | "
            f"Browser: {browser_results['passed']}/{browser_results['total']}",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[bold red]❌ TESTS FAILED[/bold red]\n"
            f"Unit failed: {unit_results['failed']} | "
            f"Browser failed: {browser_results['failed']}",
            border_style="red"
        ))

    return combined


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Tester Agent — full quality gate")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--task-title", default=None)
    parser.add_argument("--description", default=None)
    parser.add_argument("--project-name", default=None)
    args = parser.parse_args()

    results = run_all_tests(
        task_id=args.task_id,
        task_title=args.task_title,
        description=args.description,
        project_name=args.project_name,
    )
    print(json.dumps(results, indent=2))
    sys.exit(0 if results.get("all_passed") else 1)
