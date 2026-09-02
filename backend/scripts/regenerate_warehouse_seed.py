"""Regenerate warehouse_seed.json with multiple line items per invoice (not aggregated)."""
import json
from collections import defaultdict
from pathlib import Path

WAREHOUSES = [
    ("01", 8500, 9000, 1000),
    ("58", 9700, 10950, 2000),
    ("61", 10900, 11500, 3000),
    ("72", 12100, 12750, 4000),
    ("84", 13300, 14000, 5000),
    ("95", 14500, 15250, 6000),
]

LINES_PER_INVOICE = 5
INVOICES_PER_WHSE = 5

rows = []
for whs, total_cases, total_order, inv_base in WAREHOUSES:
    n = INVOICES_PER_WHSE * LINES_PER_INVOICE
    cases_each = total_cases // n
    cases_rem = total_cases - cases_each * n
    order_each = total_order // n
    order_rem = total_order - order_each * n
    idx = 0
    for inv_i in range(1, INVOICES_PER_WHSE + 1):
        invoice = f"INV-2026-{inv_base + inv_i}"
        batch = f"BATCH-{whs}-{inv_i:03d}"
        oerdte = "20260730" if inv_i % 2 else "20260729"
        for line in range(1, LINES_PER_INVOICE + 1):
            idx += 1
            cases = cases_each + (1 if idx <= cases_rem else 0)
            order = order_each + (1 if idx <= order_rem else 0)
            rows.append({
                "whs_num": whs,
                "batch_id": batch,
                "oeinvo": invoice,
                "oerdte": oerdte,
                "cust_item_code": f"ITEM-{whs}-{inv_i:02d}-{line:02d}",
                "cs_item_code": f"CS-{whs}-{inv_i:02d}-{line:02d}",
                "cases_bld_stg": cases,
                "orgnl_ordr_qty_stg": order,
                "whs_scrtch_qty_stg": (idx % 5) + 1,
                "sl_itm_ind_stg": "Y" if line % 3 == 0 else "N",
            })

out = Path(__file__).resolve().parents[1] / "data" / "warehouse_seed.json"
out.write_text(json.dumps(rows, indent=2), encoding="utf-8")

by = defaultdict(lambda: {"cases": 0, "order": 0, "rows": 0, "inv": set()})
for r in rows:
    w = r["whs_num"]
    by[w]["cases"] += r["cases_bld_stg"]
    by[w]["order"] += r["orgnl_ordr_qty_stg"]
    by[w]["rows"] += 1
    by[w]["inv"].add(r["oeinvo"])
print(f"Generated {len(rows)} line items -> {out}")
for w in sorted(by):
    s = by[w]
    print(f"  whs {w}: {s['rows']} lines, {len(s['inv'])} invoices, cases={s['cases']}, order={s['order']}")
