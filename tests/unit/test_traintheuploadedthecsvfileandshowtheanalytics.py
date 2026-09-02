"""Unit tests for TrainTheUploadedTheCsvFileAndShowTheAnalytics component."""
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent

def test_traintheuploadedthecsvfileandshowtheanalytics_exists():
    file_path = ROOT_DIR / "frontend" / "src" / "components" / "TrainTheUploadedTheCsvFileAndShowTheAnalytics.jsx"
    assert file_path.exists(), "TrainTheUploadedTheCsvFileAndShowTheAnalytics.jsx component file must exist"
