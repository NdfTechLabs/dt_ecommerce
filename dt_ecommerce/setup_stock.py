"""
dt_ecommerce.setup_stock
Creates opening stock for DAL-* items in Stores - NDF and
configures Webshop Settings to display prices and stock availability.

Run via:
    bench --site erpnext.localhost execute dt_ecommerce.setup_stock.run
"""

import frappe
from frappe.utils import today, flt


WAREHOUSE    = "Stores - NDF"
COMPANY      = "NdfTechLabs"
COST_CENTRE  = "Main - NDF"
DIFF_ACCOUNT = "Temporary Opening - NDF"   # credit side for opening stock entry

# item_code → (opening_qty, valuation_rate_kes)
# qty in individual bottles; valuation = landed cost (≈ 60 % of selling price)
OPENING_STOCK = {
    "DAL-JWB-750":    (48,  1_920),   # 4 cases  ×12   @ KES 1,920/btl
    "DAL-JWG-750":    (24,  3_900),   # 2 cases  ×12   @ KES 3,900/btl
    "DAL-JAM-700":    (36,  1_680),   # 3 cases  ×12   @ KES 1,680/btl
    "DAL-JD-700":     (36,  1_500),   # 3 cases  ×12   @ KES 1,500/btl
    "DAL-CAB-750":    (24,  1_140),   # 2 cases  ×12   @ KES 1,140/btl
    "DAL-MALBEC-750": (24,    960),   # 2 cases  ×12   @ KES   960/btl
    "DAL-CHARD-750":  (24,    870),   # 2 cases  ×12   @ KES   870/btl
    "DAL-MOET-750":   (12,  5_880),   # 2 cases  × 6   @ KES 5,880/btl
    "DAL-TUSK-500":   (96,    168),   # 4 cases  ×24   @ KES   168/btl
    "DAL-ABSV-1L":    (24,  2_160),   # 2 cases  ×12   @ KES 2,160/btl
    "DAL-HENN-700":   (24,  5_100),   # 2 cases  ×12   @ KES 5,100/btl
    "DAL-BAC-700":    (24,  1_170),   # 2 cases  ×12   @ KES 1,170/btl
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _already_has_stock(item_code: str) -> bool:
    """Return True if the item already has a positive actual_qty in Stores."""
    qty = frappe.db.get_value("Bin",
        {"item_code": item_code, "warehouse": WAREHOUSE},
        "actual_qty") or 0
    return flt(qty) > 0


def _set_item_default_warehouse(item_code: str) -> None:
    """
    Ensure the Item has a default warehouse for the company set to Stores - NDF.
    This is what the webshop stock-availability check reads.
    """
    doc = frappe.get_doc("Item", item_code)
    # look for an existing row for this company
    existing = next(
        (r for r in doc.item_defaults if r.company == COMPANY), None
    )
    if existing:
        if existing.default_warehouse == WAREHOUSE:
            print(f"  [SKIP] Item default warehouse already set: {item_code}")
            return
        existing.default_warehouse = WAREHOUSE
    else:
        doc.append("item_defaults", {
            "company":           COMPANY,
            "default_warehouse": WAREHOUSE,
        })
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    print(f"  [OK]   Default warehouse set: {item_code} → {WAREHOUSE}")


# ─── Main sections ───────────────────────────────────────────────────────────

def _create_opening_stock_entry() -> str | None:
    """
    Create and submit a Material Receipt Stock Entry for all DAL-* items
    that have no stock yet.  Returns the Stock Entry name, or None if all
    items already have stock.
    """
    items_to_add = [
        (code, qty, rate)
        for code, (qty, rate) in OPENING_STOCK.items()
        if not _already_has_stock(code)
    ]

    if not items_to_add:
        print("  [SKIP] All DAL-* items already have opening stock.")
        return None

    se = frappe.get_doc({
        "doctype":          "Stock Entry",
        "stock_entry_type": "Material Receipt",
        "company":          COMPANY,
        "posting_date":     today(),
        "posting_time":     "08:00:00",
        "remarks":          "Dalali opening stock — webshop launch",
        "items": [
            {
                "item_code":        code,
                "qty":              qty,
                "basic_rate":       rate,
                "t_warehouse":      WAREHOUSE,
                "cost_center":      COST_CENTRE,
                "expense_account":  DIFF_ACCOUNT,
            }
            for code, qty, rate in items_to_add
        ],
    })
    se.insert(ignore_permissions=True)
    se.submit()
    frappe.db.commit()
    print(f"  [OK]   Stock Entry submitted: {se.name}  ({len(items_to_add)} items)")
    return se.name


def _set_item_default_warehouses() -> None:
    print("\n── Item default warehouses ──")
    for code in OPENING_STOCK:
        _set_item_default_warehouse(code)


def _configure_webshop() -> None:
    print("\n── Webshop Settings ──")
    ws = frappe.get_doc("Webshop Settings")
    changes = {
        "show_price":              1,   # show KES prices to visitors
        "show_stock_availability": 1,   # show In Stock / Out of Stock badge
        "show_quantity_in_website": 0,  # hide exact qty (wholesale — no need to expose)
        "allow_items_not_in_stock": 0,  # block checkout when out of stock
    }
    updated = []
    for field, value in changes.items():
        if getattr(ws, field) != value:
            setattr(ws, field, value)
            updated.append(field)
    if updated:
        ws.save(ignore_permissions=True)
        frappe.db.commit()
        print(f"  [OK]   Updated: {', '.join(updated)}")
    else:
        print("  [SKIP] Webshop Settings already correct.")


def _verify() -> None:
    print("\n── Verification ──")
    print(f"  {'Item':20}  {'Warehouse':25}  {'Qty':>8}  {'Val.Rate':>12}  {'Stock Value':>14}")
    print("  " + "─" * 85)
    total_value = 0.0
    for code in OPENING_STOCK:
        row = frappe.db.get_value("Bin",
            {"item_code": code, "warehouse": WAREHOUSE},
            ["actual_qty", "valuation_rate", "stock_value"],
            as_dict=True) or {}
        qty   = flt(row.get("actual_qty", 0))
        rate  = flt(row.get("valuation_rate", 0))
        value = flt(row.get("stock_value", 0))
        total_value += value
        flag = "✅" if qty > 0 else "❌"
        print(f"  {flag} {code:20}  {WAREHOUSE:25}  {qty:8.0f}  {rate:12,.0f}  {value:14,.0f}")
    print("  " + "─" * 85)
    print(f"  {'TOTAL OPENING STOCK VALUE (KES)':62}  {total_value:14,.0f}")


# ─── Entry point ─────────────────────────────────────────────────────────────

def run() -> None:
    """
    Idempotent setup:
      1. Create & submit opening Material Receipt for DAL-* items (skips items
         that already have positive stock)
      2. Set default warehouse on each Item for the webshop stock check
      3. Enable price + stock-availability display in Webshop Settings
      4. Print a verification table
    """
    frappe.set_user("Administrator")

    print("\n── 1. Opening Stock Entry ──")
    se_name = _create_opening_stock_entry()

    _set_item_default_warehouses()
    _configure_webshop()
    _verify()

    print(f"\n{'═' * 60}")
    if se_name:
        print(f"  Stock Entry : {se_name}")
    print(f"  Warehouse   : {WAREHOUSE}")
    print(f"  Next step   : bench --site erpnext.localhost clear-cache")
    print(f"{'═' * 60}\n")
