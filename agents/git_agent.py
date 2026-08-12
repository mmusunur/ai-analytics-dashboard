"""
Git Agent — Handles end-of-day git operations.
Stages all changes, creates meaningful commit messages, and pushes to remote.
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional
from rich.console import Console
from dotenv import load_dotenv

load_dotenv()
console = Console()

ROOT_DIR = Path(__file__).parent.parent
GITHUB_REPO = os.getenv("GITHUB_REPO", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


def _run_git(command: list[str], cwd: Path = ROOT_DIR) -> tuple[str, str, int]:
    """Run a git command and return (stdout, stderr, returncode)."""
    result = subprocess.run(
        ["git"] + command,
        cwd=str(cwd),
        capture_output=True,
        text=True
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def init_repo() -> bool:
    """Initialize git repository if not already initialized."""
    git_dir = ROOT_DIR / ".git"
    if git_dir.exists():
        console.print("[green]✅ Git repo already initialized[/green]")
        return True

    stdout, stderr, code = _run_git(["init"])
    if code == 0:
        console.print("[green]✅ Git repo initialized[/green]")
        # Set default branch to main
        _run_git(["checkout", "-b", "main"])
        return True
    else:
        console.print(f"[red]❌ Git init failed: {stderr}[/red]")
        return False


def set_remote(repo_url: str) -> bool:
    """Set the remote origin URL."""
    # Check if remote already exists
    stdout, _, _ = _run_git(["remote", "get-url", "origin"])
    if stdout:
        console.print(f"[yellow]⚠️  Remote already set: {stdout}[/yellow]")
        return True

    _, stderr, code = _run_git(["remote", "add", "origin", repo_url])
    if code == 0:
        console.print(f"[green]✅ Remote set: {repo_url}[/green]")
        return True
    else:
        console.print(f"[red]❌ Failed to set remote: {stderr}[/red]")
        return False


def get_changed_files() -> list[str]:
    """Get list of all changed/untracked files."""
    stdout, _, _ = _run_git(["status", "--porcelain"])
    if not stdout:
        return []

    files = []
    for line in stdout.split("\n"):
        if line.strip():
            # Format: "XY filename"
            parts = line.strip().split(" ", 1)
            if len(parts) > 1:
                files.append(parts[-1].strip())
    return files


def get_meaningful_changed_files() -> list[str]:
    """
    Get list of meaningful changed source code/documentation files.
    Filters out log files, system cache, temporary files, and noisy state logs
    to prevent unnecessary spam commits.
    """
    raw_files = get_changed_files()
    meaningful = []
    
    # Exclude temporary, cache, log, and noisy state files
    ignored_patterns = (
        ".log", ".system_generated", "__pycache__", ".pytest_cache",
        "brain/", ".tmp", "task-", "logs/"
    )
    
    for f in raw_files:
        normalized = f.replace("\\", "/").lower()
        if any(pat in normalized for pat in ignored_patterns):
            continue
        meaningful.append(f)
        
    return meaningful


def stage_all() -> bool:
    """Stage all changes."""
    _, stderr, code = _run_git(["add", "."])
    if code == 0:
        console.print("[cyan]📦 All changes staged[/cyan]")
        return True
    else:
        console.print(f"[red]❌ Git add failed: {stderr}[/red]")
        return False


def generate_commit_message(
    tasks_completed: list[str] = None,
    files_changed: list[str] = None,
    custom_summary: Optional[str] = None
) -> str:
    """Generate a meaningful commit message from today's activity."""
    today = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M")

    if custom_summary:
        subject = f"EOD {today}: {custom_summary}"
    else:
        subject = f"EOD {today} @ {time_str} — Daily agent commit"

    body_lines = []

    if tasks_completed:
        body_lines.append("## Tasks Completed")
        for task in tasks_completed[:10]:  # Max 10 tasks in commit
            body_lines.append(f"- ✅ {task}")

    if files_changed:
        body_lines.append("\n## Files Changed")
        for f in files_changed[:20]:  # Max 20 files
            body_lines.append(f"- {f}")

    body_lines.append(f"\n🤖 Auto-committed by Git Agent at {time_str}")

    return subject + "\n\n" + "\n".join(body_lines)


def commit(message: str) -> bool:
    """Commit staged changes with the given message."""
    result = subprocess.run(
        ["git", "commit", "-F", "-"],
        cwd=str(ROOT_DIR),
        input=message,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    stderr = result.stderr.strip()
    if result.returncode == 0:
        console.print(f"[green]✅ Committed: {message.splitlines()[0][:60]}...[/green]")
        return True
    elif "nothing to commit" in stderr.lower() or "no changes added" in stderr.lower():
        console.print("[yellow]⚠️  Nothing to commit[/yellow]")
        return True  # Not an error
    else:
        console.print(f"[red]❌ Commit failed: {stderr}[/red]")
        return False


def push(branch: str = "main", force: bool = False) -> bool:
    """Push commits to remote origin."""
    cmd = ["push", "-u", "origin", branch]
    if force:
        cmd.append("--force")

    stdout, stderr, code = _run_git(cmd)
    if code == 0:
        console.print(f"[bold green]🚀 Pushed to origin/{branch}[/bold green]")
        return True
    else:
        console.print(f"[red]❌ Push failed: {stderr}[/red]")
        console.print("[yellow]💡 Tip: Make sure GITHUB_TOKEN is set and repo exists[/yellow]")
        return False


def pull(branch: str = "main") -> bool:
    """Pull latest changes from remote origin."""
    stdout, stderr, code = _run_git(["pull", "origin", branch])
    if code == 0:
        console.print(f"[bold green]📥 Pulled latest changes from origin/{branch}[/bold green]")
        return True
    else:
        console.print(f"[red]❌ Pull failed: {stderr}[/red]")
        return False


def get_commit_log(n: int = 5) -> list[str]:
    """Get the last N commit messages."""
    stdout, _, _ = _run_git(["log", f"-{n}", "--oneline"])
    return stdout.split("\n") if stdout else []


def get_unpushed_commits(branch: str = "main") -> list[str]:
    """Check for local commits that have not been pushed to remote."""
    stdout, _, code = _run_git(["log", f"origin/{branch}..HEAD", "--oneline"])
    if code == 0 and stdout.strip():
        return [line for line in stdout.split("\n") if line.strip()]
    return []


def eod_push(
    tasks_completed: list[str] = None,
    custom_summary: Optional[str] = None
) -> bool:
    """
    Daily End-of-Day workflow:
    1. Check for uncommitted meaningful source code/doc files and unpushed commits.
    2. If NO meaningful code changes exist (e.g. only logs/cache), skip Git commit & push.
    3. If meaningful code changes exist, stage, commit, and push to remote.
    """
    console.print("\n[bold magenta]🌙 Starting Daily End-of-Day Git Check...[/bold magenta]")

    meaningful_files = get_meaningful_changed_files()
    unpushed_commits = get_unpushed_commits()

    if not meaningful_files and not unpushed_commits:
        console.print("[yellow]⚠️  No meaningful code/doc changes or unpushed commits found. Skipping unnecessary Git commit & push.[/yellow]")
        return True

    if meaningful_files:
        console.print(f"[cyan]📁 {len(meaningful_files)} meaningful file(s) changed[/cyan]")
        if not stage_all():
            return False

        message = generate_commit_message(
            tasks_completed=tasks_completed,
            files_changed=meaningful_files,
            custom_summary=custom_summary
        )

        if not commit(message):
            return False
    elif unpushed_commits:
        console.print(f"[cyan]📦 {len(unpushed_commits)} unpushed commit(s) ready to push[/cyan]")

    if GITHUB_REPO:
        return push()
    else:
        console.print("[yellow]⚠️  No GITHUB_REPO set — commit saved locally only[/yellow]")
        return True


def setup_git_config(name: str = "AI Analytics Agent", email: str = "agent@ai-dashboard.local"):
    """Set up git user config for agent commits."""
    _run_git(["config", "user.name", name])
    _run_git(["config", "user.email", email])
    console.print(f"[green]✅ Git config: {name} <{email}>[/green]")


if __name__ == "__main__":
    import argparse
    import sys
    import time

    ROOT = Path(__file__).parent.parent
    sys.path.insert(0, str(ROOT / "agents"))
    from memory_manager import update_agent_status

    parser = argparse.ArgumentParser(description="Git Agent")
    parser.add_argument("--standby", action="store_true", help="Run standby loop for fleet supervisor")
    args = parser.parse_args()

    if args.standby:
        console.print("[bold blue]Git Agent — standby mode[/bold blue]")
        update_agent_status("git_agent", "running", "Standby - ready for commits")
        while True:
            time.sleep(30)
            update_agent_status("git_agent", "running", "Standby - ready for commits")
    else:
        console.print("[bold blue]Git Agent Test[/bold blue]")
        init_repo()
        setup_git_config()
        log = get_commit_log()
        console.print(f"Recent commits: {log}")
        changed = get_changed_files()
        console.print(f"Changed files: {changed}")
