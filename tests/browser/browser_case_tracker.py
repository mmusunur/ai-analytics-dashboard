"""
Track individual browser test case PASS/FAIL and sync to TEST_CASES.xlsx.
"""

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "memory" / "browser_test_registry.json"


def _load() -> dict:
    if REGISTRY_PATH.exists():
        try:
            return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"cases": {}, "last_run": None}


def _save(data: dict) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def record_case(case_id: str, passed: bool, message: str = "") -> None:
    data = _load()
    data["cases"][case_id] = {
        "status": "PASS" if passed else "FAIL",
        "message": (message or "")[:500],
        "updated_at": datetime.now().isoformat(),
    }
    data["last_run"] = datetime.now().isoformat()
    _save(data)


def get_case_status(case_id: str) -> str:
    return _load().get("cases", {}).get(case_id, {}).get("status", "PENDING")


def sync_excel_from_registry() -> None:
    """Regenerate TEST_CASES.xlsx using per-case browser registry statuses."""
    import subprocess
    import sys
    subprocess.run(
        [sys.executable, str(ROOT / "tests" / "generate_test_excel.py"), "--browser-passed", "true"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
