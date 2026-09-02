"""
Sync all documentation artifacts (PPTX + DOCX) from shared content.
Run: python docs/sync_all_documentation.py

Replaces the single canonical PPTX and DOCX in docs/ — never creates duplicates.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DOCS = Path(__file__).parent


def main():
    print("=== AgenticOps AI Documentation Sync ===")
    print("Source: docs/doc_content.py")
    print("Output: replaces docs/AgenticOps_AI_Overview.pptx + AgenticOps_AI_Documentation.docx in place\n")

    from generate_presentation import main as gen_pptx
    from generate_docx import main as gen_docx

    try:
        gen_pptx()
        gen_docx()
    except SystemExit as exc:
        print(f"\n[ERROR] Generator failed: {exc}")
        sys.exit(1)

    print("\n--- Running sync check ---")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "sync_documentation.py")], cwd=str(ROOT))

    print("\n[OK] Documentation artifacts replaced in place.")
    print(f"  • {DOCS / 'AgenticOps_AI_Overview.pptx'}")
    print(f"  • {DOCS / 'AgenticOps_AI_Documentation.docx'}")


if __name__ == "__main__":
    main()
