"""Unit tests for TrainingTheCsvData component."""
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent

def test_trainingthecsvdata_exists():
    file_path = ROOT_DIR / "frontend" / "src" / "components" / "TrainingTheCsvData.jsx"
    assert file_path.exists(), "TrainingTheCsvData.jsx component file must exist"
