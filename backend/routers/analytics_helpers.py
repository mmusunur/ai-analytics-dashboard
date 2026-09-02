"""
Analytics Helpers — Copilot NLP intent parser & Anomaly calculators for analytics.py.
Keeps backend/routers/analytics.py lightweight (< 200 lines).
"""

import re
from typing import Optional


def parse_copilot_intent(prompt: str) -> dict:
    """Extract warehouse numbers, scratch intents, and entity filters from natural language prompt."""
    prompt_clean = prompt.lower()

    # Extract Warehouse Facility Number
    whs_match = re.search(r"\b(?:whse|whs|warehouse|facility)\s*#?\s*(\d{1,3})\b", prompt_clean)
    if not whs_match:
        whs_match = re.search(r"\b(\d{2,3})\s*(?:whse|whs|warehouse|facility)?\b", prompt_clean)

    filtered_whse = whs_match.group(1).zfill(2) if whs_match else ""

    # Detect Scratch Intent
    filter_scratch = any(k in prompt_clean for k in ["scratch", "scrtch", "missing", "shortage"])

    # Detect Batch / Invoice
    batch_match = re.search(r"\bbatch\s*#?\s*([a-zA-Z0-9_-]+)", prompt_clean)
    filtered_batch = batch_match.group(1) if batch_match else ""

    return {
        "filtered_whse": filtered_whse,
        "filter_scratch": filter_scratch,
        "filtered_batch": filtered_batch
    }


def generate_anomaly_alerts(warehouse_items: list) -> list:
    """Scan warehouse item records and generate categorized risk alerts."""
    alerts = []
    
    # 1. High Scratch Rate Alerts
    scratch_items = [it for it in warehouse_items if it.get("whs_scrtch_qty_stg", 0) > 10]
    if scratch_items:
        whs_list = sorted(set(it.get("whs_num", "01") for it in scratch_items))
        alerts.append({
            "id": "ANOM-SCRATCH-01",
            "severity": "critical",
            "title": "🔴 Critical Fulfillment Scratch Alert",
            "message": f"Detected high scratch rate (>10 cases) across {len(whs_list)} facilities: Whse {', '.join(whs_list)}.",
            "filter_whse": whs_list[0] if whs_list else ""
        })

    # 2. Volume Spike Alerts
    high_volume = [it for it in warehouse_items if it.get("cases_bld_stg", 0) > 10000]
    if high_volume:
        alerts.append({
            "id": "ANOM-VOLUME-02",
            "severity": "warning",
            "title": "⚡ High Processing Volume Spike",
            "message": f"Surge in cases built detected for {len(high_volume)} line items (>10,000 cases).",
            "filter_whse": high_volume[0].get("whs_num", "")
        })

    # Default fallback alert
    if not alerts:
        alerts.append({
            "id": "ANOM-HEALTHY-00",
            "severity": "info",
            "title": "🟢 Warehouse Operations Optimal",
            "message": "All warehouse fulfillment metrics and scratch rates within normal operational bounds.",
            "filter_whse": ""
        })

    return alerts
