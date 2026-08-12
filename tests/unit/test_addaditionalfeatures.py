"""Unit tests for AddAditionalFeatures component."""
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent

def test_addaditionalfeatures_exists():
    file_path = ROOT_DIR / "frontend" / "src" / "components" / "AddAditionalFeatures.jsx"
    assert file_path.exists(), "AddAditionalFeatures.jsx component file must exist"
