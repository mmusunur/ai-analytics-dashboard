"""Unit tests for Navbar component integration."""
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent

def test_navbar_file_exists():
    navbar_path = ROOT_DIR / "frontend" / "src" / "components" / "Navbar.jsx"
    assert navbar_path.exists(), "Navbar.jsx component file must exist"

def test_navbar_structure():
    navbar_path = ROOT_DIR / "frontend" / "src" / "components" / "Navbar.jsx"
    content = navbar_path.read_text(encoding="utf-8")
    assert "export default function Navbar" in content
    assert "AI Analytics Dashboard" in content
