"""Unit tests for DataAnalytics component."""
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent

def test_dataanalytics_exists():
    file_path = ROOT_DIR / "frontend" / "src" / "components" / "DataAnalytics.jsx"
    assert file_path.exists(), "DataAnalytics.jsx component file must exist"

def test_dataanalytics_structure():
    content = (ROOT_DIR / "frontend/src/components/DataAnalytics.jsx").read_text(encoding="utf-8")
    assert "data-analytics-panel" in content
    assert "/api/data/upload" in content
    assert "/api/analytics/train" in content

def test_dataanalytics_on_dashboard():
    dash = (ROOT_DIR / "frontend/src/pages/Dashboard.jsx").read_text(encoding="utf-8")
    assert "DataAnalytics" in dash
    assert "<DataAnalytics" in dash
