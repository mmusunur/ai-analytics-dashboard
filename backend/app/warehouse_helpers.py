"""
Warehouse Helpers — Mock data fallbacks and statistics aggregator helpers for warehouse_service.
Keeps backend/app/warehouse_service.py lightweight (< 250 lines).
"""

from typing import Optional


def fetch_mock_warehouse_data(target_db: str = "pg_prod", oerdte: Optional[str] = None, oewhse: Optional[str] = None) -> list:
    """Generate resilient mock warehouse sales data when remote DB connection is offline."""
    mock_facilities = ["01", "58", "61", "72", "84", "95"]
    if oewhse and str(oewhse).zfill(2) in mock_facilities:
        mock_facilities = [str(oewhse).zfill(2)]
    elif oewhse and str(oewhse).strip():
        mock_facilities = [str(oewhse).strip()]

    items = []
    base_date = str(oerdte) if oerdte and len(str(oerdte)) == 8 else "20260730"
    
    if oerdte and len(str(oerdte)) == 8 and str(oerdte) not in ("20260730", "20260729", ""):
        return []

    for idx, whs in enumerate(mock_facilities):
        inv_no = f"INV-2026-{1000 + idx}"
        items.append({
            "whs_num": whs,
            "batch_id": f"BATCH-{whs}-001",
            "oeinvo": inv_no,
            "invc_num_stg": inv_no,
            "oerdte": base_date,
            "cust_item_code": f"ITEM-{100 + idx}",
            "cs_item_code": f"CS-{100 + idx}",
            "procurement_transfer_status": "COMPLETED",
            "cases_bld_stg": 8500 + (idx * 1200),
            "orgnl_ordr_qty_stg": 9000 + (idx * 1250),
            "whs_scrtch_qty_stg": 15 + (idx * 5)
        })
    return items


def compute_warehouse_summary(items: list) -> dict:
    """Compute KPI summary totals from list of warehouse item dicts."""
    total_cases = sum(it.get("cases_bld_stg", 0) for it in items)
    total_order = sum(it.get("orgnl_ordr_qty_stg", 0) for it in items)
    total_scratch = sum(it.get("whs_scrtch_qty_stg", 0) for it in items)
    distinct_whse = len(set(it.get("whs_num") for it in items if it.get("whs_num")))
    distinct_invo = len(set(it.get("oeinvo") for it in items if it.get("oeinvo")))

    fulfillment_rate = f"{(total_cases / total_order * 100):.1f}%" if total_order > 0 else "0%"

    return {
        "total_cases_built": total_cases,
        "total_original_order_qty": total_order,
        "total_scratch_qty": total_scratch,
        "total_warehouses": distinct_whse,
        "distinct_warehouses": distinct_whse,
        "distinct_invoices": distinct_invo,
        "total_invoices_processed": distinct_invo,
        "procurement_fulfillment_rate": fulfillment_rate,
        "warehouse_totals": [
            {
                "whs_num": whs,
                "warehouse": f"WHS {whs}",
                "cases_built": sum(it.get("cases_bld_stg", 0) for it in items if it.get("whs_num") == whs),
                "scratch_qty": sum(it.get("whs_scrtch_qty_stg", 0) for it in items if it.get("whs_num") == whs),
                "original_order_qty": sum(it.get("orgnl_ordr_qty_stg", 0) for it in items if it.get("whs_num") == whs)
            }
            for whs in sorted(set(it.get("whs_num") for it in items if it.get("whs_num")))
        ]
    }
