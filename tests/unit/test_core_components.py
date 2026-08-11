"""
Unit tests for core UI components and services (Navbar, Warehouse, Inventory Risk Forecast, Sales Analytics).
"""

from pathlib import Path
from backend.app.warehouse_service import get_warehouse_statistics, DB_CONFIGURATIONS

ROOT_DIR = Path(__file__).parent.parent.parent


def test_navbar_component():
    comp_path = ROOT_DIR / "frontend" / "src" / "components" / "Navbar.jsx"
    assert comp_path.exists(), "Navbar.jsx should exist"
    content = comp_path.read_text(encoding="utf-8")
    assert "AgenticOps AI" in content or "AI Analytics Dashboard" in content


def test_warehouse_analytics_component():
    comp_path = ROOT_DIR / "frontend" / "src" / "components" / "WarehouseAnalytics.jsx"
    assert comp_path.exists(), "WarehouseAnalytics.jsx should exist"
    content = comp_path.read_text(encoding="utf-8")
    assert "Warehouse Level Statistics" in content


def test_inventory_risk_forecast_component():
    comp_path = ROOT_DIR / "frontend" / "src" / "components" / "InventoryRiskForecast.jsx"
    assert comp_path.exists(), "InventoryRiskForecast.jsx should exist"
    content = comp_path.read_text(encoding="utf-8")
    assert "Inventory Risk Forecast" in content


def test_warehouse_sales_analytics_backend_service():
    assert "pg_dev" in DB_CONFIGURATIONS
    assert "oracle_dev" in DB_CONFIGURATIONS
    stats = get_warehouse_statistics("pg_dev")
    assert stats["status"] == "success"


def test_warehouse_sales_analytics_component():
    comp_path = ROOT_DIR / "frontend" / "src" / "components" / "WarehouseSalesAnalytics.jsx"
    assert comp_path.exists(), "WarehouseSalesAnalytics.jsx should exist"
    content = comp_path.read_text(encoding="utf-8")
    assert "Warehouse & Invoice Sales Analytics" in content
