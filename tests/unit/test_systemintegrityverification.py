"""Unit tests for Systemintegrityverification component."""
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent

def test_systemintegrityverification_exists():
    file_path = ROOT_DIR / "frontend" / "src" / "components" / "Systemintegrityverification.jsx"
    assert file_path.exists(), "Systemintegrityverification.jsx component file must exist"
