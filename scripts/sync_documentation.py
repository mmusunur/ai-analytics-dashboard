"""
Documentation sync helper — reports doc files that may need updating after code changes.
Run: python scripts/sync_documentation.py
"""

from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent

DOC_FILES = [
    ROOT / "README.md",
    ROOT / "tasks.md",
    ROOT / "docs" / "AGENT_PIPELINE_USER_GUIDE.md",
    ROOT / "docs" / "doc_content.py",
    ROOT / "docs" / "AgenticOps_AI_Overview.pptx",
    ROOT / "docs" / "AgenticOps_AI_Documentation.docx",
    ROOT / "tests" / "TEST_CASES.xlsx",
]

CODE_SIGNAL_DIRS = [
    ROOT / "frontend" / "src",
    ROOT / "agents",
    ROOT / "backend",
    ROOT / "tests",
]

def latest_mtime(paths):
    latest = None
    for base in paths:
        if not base.exists():
            continue
        for f in base.rglob("*"):
            if f.is_file() and f.suffix in {".py", ".jsx", ".js", ".ts", ".tsx", ".md"}:
                if "__pycache__" in str(f) or "node_modules" in str(f):
                    continue
                m = f.stat().st_mtime
                if latest is None or m > latest:
                    latest = m
    return latest


def main():
    code_latest = latest_mtime(CODE_SIGNAL_DIRS)
    print("=== Documentation Sync Check ===")
    print(f"Latest code change: {datetime.fromtimestamp(code_latest) if code_latest else 'unknown'}\n")

    stale = []
    for doc in DOC_FILES:
        if not doc.exists():
            print(f"[MISSING] {doc.relative_to(ROOT)}")
            stale.append(doc)
            continue
        doc_mtime = doc.stat().st_mtime
        status = "OK" if doc_mtime >= (code_latest or 0) else "STALE"
        print(f"[{status}] {doc.relative_to(ROOT)} — modified {datetime.fromtimestamp(doc_mtime)}")
        if status == "STALE":
            stale.append(doc)

    if stale:
        print("\nAction: Update stale docs per tasks/task_33_automatic_documentation_updates.md")
        print("  python docs/sync_all_documentation.py")
        print("  python tests/generate_test_excel.py")
    else:
        print("\nAll tracked documentation appears up to date.")


if __name__ == "__main__":
    main()
