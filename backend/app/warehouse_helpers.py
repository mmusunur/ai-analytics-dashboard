"""
Warehouse Helpers — Summary builders and optional local seed filtering.
All warehouse/date/batch filters come from API request params (UI-driven).
PostgreSQL is primary; local seed JSON is optional offline fallback only.
"""

import json
import re
from pathlib import Path
from typing import Optional

_SEED_PATH = Path(__file__).resolve().parents[1] / "data" / "warehouse_seed.json"
_seed_cache: Optional[list] = None
_seed_mtime: Optional[float] = None


def _normalize_whs(whs: Optional[str]) -> str:
    s = str(whs or "").strip()
    if not s:
        return ""
    return s.zfill(2) if s.isdigit() else s


def _normalize_oerdte_value(oerdte: Optional[str]) -> Optional[str]:
    raw = str(oerdte or "").strip()
    if not raw:
        return None
    clean = re.sub(r"\D", "", raw)
    return clean if len(clean) == 8 else None


def _load_seed_records() -> list:
    """Load optional dev seed file (replace with DB export in production)."""
    global _seed_cache, _seed_mtime
    if not _SEED_PATH.exists():
        _seed_cache = []
        return _seed_cache
    mtime = _SEED_PATH.stat().st_mtime
    if _seed_cache is not None and _seed_mtime == mtime:
        return _seed_cache
    try:
        _seed_cache = json.loads(_SEED_PATH.read_text(encoding="utf-8"))
        _seed_mtime = mtime
    except Exception:
        _seed_cache = []
    return _seed_cache


def filter_warehouse_records(
    records: list,
    oerdte: Optional[str] = None,
    oewhse: Optional[str] = None,
    batch_id: Optional[str] = None,
    invoice_filter: str = "",
    only_scratches: bool = False,
) -> list:
    """Apply UI-driven filters to record rows (same semantics as SQL WHERE clauses)."""
    date_filter = _normalize_oerdte_value(oerdte)
    whse_filter = _normalize_whs(oewhse)
    batch_filter = str(batch_id or "").strip().lower()
    inv_filter = str(invoice_filter or "").strip().lower()

    filtered = []
    for row in records:
        row_date = _normalize_oerdte_value(row.get("oerdte"))
        if date_filter and row_date != date_filter:
            continue
        row_whs = _normalize_whs(row.get("whs_num") or row.get("oewhse"))
        if whse_filter and row_whs != whse_filter:
            continue
        if batch_filter and batch_filter not in str(row.get("batch_id", "")).lower():
            continue
        if inv_filter and inv_filter not in str(row.get("oeinvo", "")).lower():
            continue
        scratch_qty = int(row.get("whs_scrtch_qty_stg") or row.get("oeqscr") or 0)
        if only_scratches and scratch_qty <= 0:
            continue
        filtered.append(row)
    return filtered


def fetch_local_warehouse_data(
    oerdte: Optional[str] = None,
    oewhse: Optional[str] = None,
    batch_id: Optional[str] = None,
    invoice_filter: str = "",
    only_scratches: bool = False,
) -> list:
    """Filter local seed records using UI request parameters (no hardcoded filters in code)."""
    seed = _load_seed_records()
    if not seed:
        return []
    rows = filter_warehouse_records(
        seed, oerdte=oerdte, oewhse=oewhse,
        batch_id=batch_id, invoice_filter=invoice_filter, only_scratches=only_scratches,
    )
    items = []
    for row in rows:
        whs = _normalize_whs(row.get("whs_num") or row.get("oewhse"))
        inv = row.get("oeinvo") or row.get("invc_num_stg") or ""
        items.append({
            "whs_num": whs,
            "batch_id": row.get("batch_id", ""),
            "oeinvo": inv,
            "invc_num_stg": inv,
            "oerdte": row.get("oerdte", ""),
            "cust_item_code": row.get("cust_item_code", "ITEM-001"),
            "cs_item_code": row.get("cs_item_code", "CS-001"),
            "sl_itm_ind_stg": row.get("sl_itm_ind_stg", "—"),
            "procurement_transfer_status": row.get("procurement_transfer_status", "COMPLETED"),
            "cases_bld_stg": int(row.get("cases_bld_stg") or 0),
            "orgnl_ordr_qty_stg": int(row.get("orgnl_ordr_qty_stg") or 0),
            "whs_scrtch_qty_stg": int(row.get("whs_scrtch_qty_stg") or 0),
        })
    return items


def compute_warehouse_summary(items: list) -> dict:
    """Compute KPI summary totals from list of warehouse item dicts."""
    total_cases = sum(it.get("cases_bld_stg", 0) for it in items)
    total_order = sum(it.get("orgnl_ordr_qty_stg", 0) for it in items)
    total_scratch = sum(it.get("whs_scrtch_qty_stg", 0) for it in items)
    distinct_whse = len(set(it.get("whs_num") for it in items if it.get("whs_num")))
    distinct_invo = len(set(it.get("oeinvo") or it.get("invc_num_stg") for it in items if it.get("oeinvo") or it.get("invc_num_stg")))
    distinct_batches = sorted(set(str(it.get("batch_id", "")).strip() for it in items if it.get("batch_id")))

    fulfillment_rate = f"{(total_cases / total_order * 100):.1f}%" if total_order > 0 else "0%"
    scratch_rate = f"{(total_scratch / total_order * 100):.1f}%" if total_order > 0 else "0%"

    return {
        "total_cases_built": int(total_cases),
        "total_original_order_qty": int(total_order),
        "total_scratch_qty": int(total_scratch),
        "scratch_rate": scratch_rate,
        "total_warehouses": distinct_whse,
        "distinct_warehouses": distinct_whse,
        "distinct_invoices": distinct_invo,
        "total_invoices_processed": distinct_invo,
        "total_line_items": len(items),
        "batch_ids": distinct_batches,
        "procurement_fulfillment_rate": fulfillment_rate,
        "warehouse_totals": [
            {
                "whs_num": whs,
                "warehouse": f"WHS {whs}",
                "cases_built": sum(it.get("cases_bld_stg", 0) for it in items if it.get("whs_num") == whs),
                "scratch_qty": sum(it.get("whs_scrtch_qty_stg", 0) for it in items if it.get("whs_num") == whs),
                "original_order_qty": sum(it.get("orgnl_ordr_qty_stg", 0) for it in items if it.get("whs_num") == whs),
            }
            for whs in sorted(set(it.get("whs_num") for it in items if it.get("whs_num")))
        ],
    }


def build_summary_from_sql(agg: dict, whs_rows: list) -> dict:
    """Build summary dict from SQL aggregate rows (full filtered dataset, not paginated)."""
    total_cases = int(agg.get("total_cases") or 0)
    total_order = int(agg.get("total_order") or 0)
    total_scratch = int(agg.get("total_scratch") or 0)
    distinct_whse = int(agg.get("distinct_whse") or 0)
    distinct_invo = int(agg.get("distinct_invo") or 0)
    fulfillment_rate = f"{(total_cases / total_order * 100):.1f}%" if total_order > 0 else "0%"
    scratch_rate = f"{(total_scratch / total_order * 100):.1f}%" if total_order > 0 else "0%"

    warehouse_totals = []
    for row in whs_rows or []:
        whs = str(row.get("whs_num", "")).strip()
        if not whs:
            continue
        warehouse_totals.append({
            "whs_num": whs,
            "warehouse": f"WHS {whs}",
            "cases_built": int(row.get("cases_built") or 0),
            "scratch_qty": int(row.get("scratch_qty") or 0),
            "original_order_qty": int(row.get("original_order_qty") or 0),
        })

    return {
        "total_cases_built": total_cases,
        "total_original_order_qty": total_order,
        "total_scratch_qty": total_scratch,
        "scratch_rate": scratch_rate,
        "total_warehouses": distinct_whse,
        "distinct_warehouses": distinct_whse,
        "distinct_invoices": distinct_invo,
        "total_invoices_processed": distinct_invo,
        "procurement_fulfillment_rate": fulfillment_rate,
        "warehouse_totals": warehouse_totals,
    }
