"""
Canonical output paths and in-place save helpers for documentation artifacts.
There is exactly ONE PPTX and ONE DOCX — generators always replace these files.
"""

from pathlib import Path

DOCS_DIR = Path(__file__).parent

PPTX_PATH = DOCS_DIR / "AgenticOps_AI_Overview.pptx"
DOCX_PATH = DOCS_DIR / "AgenticOps_AI_Documentation.docx"

# Legacy/alternate names to remove if they exist (avoid duplicate decks)
LEGACY_PPTX_NAMES = (
    "AgenticOps_AI.pptx",
    "AgenticOps_AI_Overview (1).pptx",
    "AgenticOps_Overview.pptx",
)


def remove_legacy_pptx_copies():
    """Delete stale duplicate PPTX files; keep only the canonical path."""
    for name in LEGACY_PPTX_NAMES:
        legacy = DOCS_DIR / name
        if legacy.exists() and legacy.resolve() != PPTX_PATH.resolve():
            legacy.unlink()
            print(f"[OK] Removed legacy duplicate: {legacy.name}")


def save_in_place(target: Path, write_fn) -> Path:
    """
    Replace target file in place via a temp sibling file.
    write_fn(temp_path) must create the new content at temp_path.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(target.suffix + ".tmp")
    try:
        write_fn(temp)
        if target.exists():
            target.unlink()
        temp.replace(target)
    except Exception:
        if temp.exists():
            temp.unlink()
        raise
    return target
