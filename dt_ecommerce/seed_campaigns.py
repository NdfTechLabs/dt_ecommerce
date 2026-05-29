"""
dt_ecommerce.seed_campaigns
Seeds Campaign records and linked Pricing Rules for the Dalali webshop
promotional banner strip.

Run via:
    bench --site erpnext.localhost execute dt_ecommerce.seed_campaigns.run
"""

import frappe
from frappe.utils import today, add_days

COMPANY = "NdfTechLabs"
CURRENCY = "KES"

# ─── Campaign + Pricing Rule definitions ─────────────────────────────────────
#
# Each entry:
#   campaign_name    : str  — Campaign record name
#   description      : str  — Campaign description (shown in ERPNext)
#   rules            : list of dicts, each dict = one Pricing Rule:
#       title        : str
#       item_groups  : list[str]   — Item Group names for the child table
#       disc_pct     : float | 0   — discount_percentage
#       disc_amt     : float | 0   — discount_amount (KES)
#       valid_days   : int         — days from today until valid_upto
#                                    use 0 for no expiry (None)
#       min_qty      : float | 0   — minimum_qty to unlock the rule
#       priority     : int         — higher = applied first when multiple rules match

CAMPAIGN_DEFS = [
    {
        "campaign_name": "May Case Bonanza",
        "description": "End-of-month whisky clearance — 15 % off all scotch and Irish whiskey cases.",
        "rules": [
            {
                "title":       "May Case Bonanza — 15% Off All Whisky",
                "item_groups": ["Whisky & Scotch"],
                "disc_pct":    15,
                "disc_amt":    0,
                "valid_days":  30,
                "min_qty":     0,
                "priority":    5,
            },
        ],
    },
    {
        "campaign_name": "Wine Week",
        "description": "Annual wine promotion covering all red and white wine categories.",
        "rules": [
            {
                "title":       "Wine Week — 10% Off Red Wine",
                "item_groups": ["Red Wine"],
                "disc_pct":    10,
                "disc_amt":    0,
                "valid_days":  14,
                "min_qty":     0,
                "priority":    5,
            },
            {
                "title":       "Wine Week — 10% Off White Wine",
                "item_groups": ["White Wine"],
                "disc_pct":    10,
                "disc_amt":    0,
                "valid_days":  14,
                "min_qty":     0,
                "priority":    5,
            },
        ],
    },
    {
        "campaign_name": "Champagne Flash Sale",
        "description": "48-hour flash promotion on all sparkling wines and champagne.",
        "rules": [
            {
                "title":       "Champagne Flash Sale — KES 2,000 Off Per Case",
                "item_groups": ["Champagne & Sparkling"],
                "disc_pct":    0,
                "disc_amt":    2_000,
                "valid_days":  7,
                "min_qty":     0,
                "priority":    8,
            },
        ],
    },
    {
        "campaign_name": "Festive Season Sale",
        "description": "Year-end festive promotion across all spirits categories — biggest discount of the year.",
        "rules": [
            {
                "title":       "Festive Season — 20% Off Whisky & Scotch",
                "item_groups": ["Whisky & Scotch"],
                "disc_pct":    20,
                "disc_amt":    0,
                "valid_days":  60,
                "min_qty":     12,   # minimum 1 case
                "priority":    10,
            },
            {
                "title":       "Festive Season — 15% Off Brandy & Cognac",
                "item_groups": ["Brandy & Cognac"],
                "disc_pct":    15,
                "disc_amt":    0,
                "valid_days":  60,
                "min_qty":     12,
                "priority":    10,
            },
            {
                "title":       "Festive Season — 15% Off Champagne & Sparkling",
                "item_groups": ["Champagne & Sparkling"],
                "disc_pct":    15,
                "disc_amt":    0,
                "valid_days":  60,
                "min_qty":     6,    # minimum 1 case (6-pack)
                "priority":    9,
            },
        ],
    },
    {
        "campaign_name": "Trade Account Welcome",
        "description": "Ongoing discount for newly verified trade accounts placing their first three orders.",
        "rules": [
            {
                "title":       "Trade Welcome — 5% Off Gin & Vodka",
                "item_groups": ["Gin & Vodka"],
                "disc_pct":    5,
                "disc_amt":    0,
                "valid_days":  0,    # 0 = no expiry
                "min_qty":     0,
                "priority":    2,
            },
            {
                "title":       "Trade Welcome — 5% Off Rum & Tequila",
                "item_groups": ["Rum & Tequila"],
                "disc_pct":    5,
                "disc_amt":    0,
                "valid_days":  0,
                "min_qty":     0,
                "priority":    2,
            },
        ],
    },
    {
        "campaign_name": "Beer & Cider Summer",
        "description": "Summer promotional push on local and imported beers — ideal for restaurant and bar accounts.",
        "rules": [
            {
                "title":       "Summer Beer Deal — 12% Off Beer & Cider (5+ Cases)",
                "item_groups": ["Beer & Cider"],
                "disc_pct":    12,
                "disc_amt":    0,
                "valid_days":  21,
                "min_qty":     120,  # 5 cases × 24 btl
                "priority":    6,
            },
        ],
    },
]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _upsert_campaign(campaign_name: str, description: str) -> str:
    """Return existing Campaign name, or create and return new one."""
    existing = frappe.db.get_value("Campaign", {"campaign_name": campaign_name}, "name")
    if existing:
        print(f"  [SKIP] Campaign: {campaign_name}")
        return existing
    doc = frappe.get_doc({
        "doctype":       "Campaign",
        "campaign_name": campaign_name,
        "description":   description,
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"  [OK]   Campaign: {doc.name}")
    return doc.name


def _upsert_pricing_rule(campaign_doc_name: str, rule: dict) -> None:
    """Create a Pricing Rule if one with the same title doesn't exist.

    NOTE: ERPNext's Pricing Rule controller (cleanup_fields_value) clears the
    `campaign` Link field when `applicable_for` is not set to "Campaign".
    When `applicable_for` is left empty the rule applies to ALL customers
    automatically — which is what we want for webshop promotions.
    The campaign link is intentionally omitted; Campaign records serve as CRM
    reference / reporting objects only.
    """
    exists = frappe.db.exists("Pricing Rule", {
        "title":   rule["title"],
        "selling": 1,
    })
    if exists:
        print(f"    [SKIP] Pricing Rule: {rule['title'][:60]}")
        return

    valid_upto = add_days(today(), rule["valid_days"]) if rule["valid_days"] else None

    doc = frappe.get_doc({
        "doctype":                    "Pricing Rule",
        "title":                      rule["title"],
        # campaign link omitted — cleared by controller when applicable_for is blank
        "selling":                    1,
        "buying":                     0,
        # item_groups is a child table — list of {item_group} dicts
        "item_groups": [{"item_group": g} for g in rule["item_groups"]],
        "apply_on":                   "Item Group",
        "price_or_product_discount":  "Price",
        "rate_or_discount":           "Discount Percentage" if rule["disc_pct"] else "Discount Amount",
        "discount_percentage":        rule["disc_pct"],
        "discount_amount":            rule["disc_amt"],
        "min_qty":                    rule["min_qty"] or 0,
        "priority":                   rule["priority"],
        "valid_from":                 today(),
        "valid_upto":                 valid_upto,
        "company":                    COMPANY,
        "currency":                   CURRENCY,
        "disable":                    0,
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    disc = f"{rule['disc_pct']}%" if rule["disc_pct"] else f"KES {rule['disc_amt']:,.0f}"
    min_note = f"  min_qty:{rule['min_qty']}" if rule["min_qty"] else ""
    print(f"    [OK]   Pricing Rule: {disc:10}  {', '.join(rule['item_groups'])}{min_note}")


# ─── Entry point ─────────────────────────────────────────────────────────────

def run() -> None:
    """
    Idempotent campaign seed.
    Creates Campaign records and linked Pricing Rules for all entries
    in CAMPAIGN_DEFS. Skips records that already exist.
    """
    frappe.set_user("Administrator")

    total_camps  = 0
    total_rules  = 0

    for defn in CAMPAIGN_DEFS:
        print(f"\n── {defn['campaign_name']} ──")
        camp_name = _upsert_campaign(defn["campaign_name"], defn["description"])
        if camp_name:
            total_camps += 1
        for rule in defn["rules"]:
            _upsert_pricing_rule(camp_name, rule)
            total_rules += 1

    print(f"\n{'═' * 60}")
    print(f"  Campaigns seeded : {len(CAMPAIGN_DEFS)}")
    print(f"  Pricing Rules    : {total_rules} definitions processed")
    print(f"  Next step        : bench --site erpnext.localhost clear-cache")
    print(f"{'═' * 60}\n")
