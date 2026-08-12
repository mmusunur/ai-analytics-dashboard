"""Task 44 — user delivery guide generation."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "agents"))

from memory_manager import _build_usage_guide, format_delivery_comment


def test_data_analytics_usage_guide():
    guide = _build_usage_guide(
        ["DATA_ANALYTICS_ML"],
        ["frontend/src/components/DataAnalytics.jsx"],
        "Data Analytics",
        False,
    )
    assert guide["route"] == "/"
    assert "Dashboard" in guide["where"]
    assert len(guide["steps"]) >= 2
    assert any("Upload" in s or "Train" in s or "Analytics" in s for s in guide["steps"])


def test_copilot_usage_guide():
    guide = _build_usage_guide(
        ["AI_COPILOT_DATE_AGNOSTIC_QUERY"],
        ["frontend/src/components/AiDataCopilot.jsx"],
        "AI Copilot",
        False,
    )
    assert guide["route"] == "/"
    assert "Copilot" in guide["headline"] or "copilot" in guide["headline"].lower()


def test_delivery_comment_includes_steps():
    guide = _build_usage_guide(["DATA_ANALYTICS_ML"], [], "Test Task", False)
    text = format_delivery_comment(guide)
    assert "Where:" in text or "**Where:**" in text
    assert "How to use" in text
