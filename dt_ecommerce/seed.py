"""
Dalali Webshop — sample data seed.
Run via:
    bench --site erpnext.localhost execute dt_ecommerce.seed.run
"""

import os
import urllib.request

import frappe
from frappe.utils import today, add_days


# ─── Constants ────────────────────────────────────────────────────────────────

FILES_DIR = os.path.join(
    frappe.get_site_path(), "public", "files"
)
UNSPLASH = "https://images.unsplash.com/photo-{id}?w={w}&q=80&auto=format&fit=crop"

# filename → (unsplash_photo_id, width_px)   — all verified 200
IMGS: dict[str, tuple[str, int]] = {
    # category cards (landscape 800 px)
    "dalali-cat-whisky.jpg":     ("1569529465841-dfecdab7503b", 800),
    "dalali-cat-redwine.jpg":    ("1474722883778-792e7990302f", 800),
    "dalali-cat-whitewine.jpg":  ("1556742049-0cfed4f6a45d",   800),
    "dalali-cat-champagne.jpg":  ("1558618666-fcd25c85cd64",   800),
    "dalali-cat-beer.jpg":       ("1533488765986-dfa2a9939acd", 800),
    "dalali-cat-gin-vodka.jpg":  ("1514362545857-3bc16c4c7d1b", 800),
    "dalali-cat-cognac.jpg":     ("1470337458703-46ad1756a187", 800),
    "dalali-cat-rum.jpg":        ("1551522435-a13afa10f103",   800),
    # product shots (portrait 600 px)
    "dalali-prod-jwblack.jpg":   ("1527281400683-1aae777175f8", 600),
    "dalali-prod-jwgold.jpg":    ("1516535794938-6063878f08cc", 600),
    "dalali-prod-jameson.jpg":   ("1546519638-68e109498ffc",   600),
    "dalali-prod-jd.jpg":        ("1569529465841-dfecdab7503b", 600),
    "dalali-prod-cab.jpg":       ("1510812431401-41d2bd2722f3", 600),
    "dalali-prod-malbec.jpg":    ("1474722883778-792e7990302f", 600),
    "dalali-prod-chard.jpg":     ("1556742049-0cfed4f6a45d",   600),
    "dalali-prod-moet.jpg":      ("1558618666-fcd25c85cd64",   600),
    "dalali-prod-tusker.jpg":    ("1535958636474-b021ee887b13", 600),
    "dalali-prod-absolut.jpg":   ("1514362545857-3bc16c4c7d1b", 600),
    "dalali-prod-hennessy.jpg":  ("1470337458703-46ad1756a187", 600),
    "dalali-prod-bacardi.jpg":   ("1551522435-a13afa10f103",   600),
    # bundle hero (landscape 800 px)
    "dalali-bnd-whisky.jpg":     ("1527281400683-1aae777175f8", 800),
    "dalali-bnd-wine.jpg":       ("1506377585622-bedcbb027afc", 800),
    "dalali-bnd-party.jpg":      ("1514362545857-3bc16c4c7d1b", 800),
}


# ─── Image helpers ────────────────────────────────────────────────────────────

def _download_image(fname: str) -> str:
    """Download image to public/files/; return '/files/fname' or '' on failure."""
    photo_id, w = IMGS[fname]
    dest = os.path.join(FILES_DIR, fname)
    if os.path.exists(dest):
        print(f"  [IMG-SKIP] {fname}")
        return f"/files/{fname}"
    url = UNSPLASH.format(id=photo_id, w=w)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 Dalali/1.0"})
        with urllib.request.urlopen(req, timeout=25) as resp, open(dest, "wb") as fh:
            fh.write(resp.read())
        kb = os.path.getsize(dest) // 1024
        print(f"  [IMG-OK]   {fname}  ({kb} KB)")
        return f"/files/{fname}"
    except Exception as exc:
        print(f"  [IMG-WARN] {fname}: {exc}")
        return ""


def _download_all() -> dict[str, str]:
    print("\n── Downloading images ──")
    return {k: _download_image(k) for k in IMGS}


# ─── Frappe record helpers ────────────────────────────────────────────────────

def _upsert(doctype: str, key, fields: dict) -> str:
    """Insert-or-update a record. key = name-str or filter-dict."""
    exists = frappe.db.exists(doctype, key)
    if exists:
        name = exists if isinstance(exists, str) else key
        try:
            doc = frappe.get_doc(doctype, name)
            changed = any(
                v is not None and getattr(doc, k, None) != v
                for k, v in fields.items()
                if k not in ("doctype", "name")
            )
            if changed:
                for k, v in fields.items():
                    if k not in ("doctype", "name") and v is not None:
                        setattr(doc, k, v)
                doc.save(ignore_permissions=True)
                frappe.db.commit()
                print(f"  [UPD]  {doctype}: {name}")
            else:
                print(f"  [SKIP] {doctype}: {name}")
        except Exception as exc:
            print(f"  [ERR]  {doctype}: {name} — {exc}")
        return name
    doc = frappe.get_doc({"doctype": doctype, **fields})
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"  [OK]   {doctype}: {doc.name}")
    return doc.name


def _upsert_wi(item_code: str, fields: dict) -> str:
    """Insert-or-update Website Item (auto-named; keyed by item_code)."""
    exists = frappe.db.exists("Website Item", {"item_code": item_code})
    if exists:
        doc = frappe.get_doc("Website Item", exists)
        changed = any(
            v is not None and getattr(doc, k, None) != v
            for k, v in fields.items()
            if k not in ("doctype", "name", "item_code")
        )
        if changed:
            for k, v in fields.items():
                if k not in ("doctype", "name", "item_code") and v is not None:
                    setattr(doc, k, v)
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            print(f"  [UPD]  Website Item: {item_code}")
        else:
            print(f"  [SKIP] Website Item: {item_code}")
        return exists
    doc = frappe.get_doc({"doctype": "Website Item", "item_code": item_code, **fields})
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"  [OK]   Website Item: {doc.name}")
    return doc.name


def _upsert_price(item_code: str, price: float) -> str:
    """Insert-or-update Item Price (Standard Selling, KES)."""
    exists = frappe.db.exists("Item Price", {
        "item_code": item_code, "selling": 1, "price_list": "Standard Selling",
    })
    if exists:
        cur = frappe.db.get_value("Item Price", exists, "price_list_rate")
        if cur != price:
            frappe.db.set_value("Item Price", exists, "price_list_rate", price)
            frappe.db.commit()
            print(f"  [UPD]  Item Price: {item_code} → KES {price:,.0f}")
        else:
            print(f"  [SKIP] Item Price: {item_code}")
        return exists
    doc = frappe.get_doc({
        "doctype": "Item Price", "item_code": item_code,
        "price_list": "Standard Selling", "selling": 1,
        "currency": "KES", "price_list_rate": price,
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"  [OK]   Item Price: {item_code} @ KES {price:,.0f}")
    return doc.name


# ─── Seed sections ────────────────────────────────────────────────────────────

def _seed_item_groups(I: dict) -> None:
    print("\n── 1. Item Groups ──")
    rows = [
        ("Whisky & Scotch",       "whisky-scotch",       "dalali-cat-whisky.jpg"),
        ("Red Wine",               "red-wine",            "dalali-cat-redwine.jpg"),
        ("White Wine",             "white-wine",          "dalali-cat-whitewine.jpg"),
        ("Champagne & Sparkling",  "champagne-sparkling", "dalali-cat-champagne.jpg"),
        ("Beer & Cider",           "beer-cider",          "dalali-cat-beer.jpg"),
        ("Gin & Vodka",            "gin-vodka",           "dalali-cat-gin-vodka.jpg"),
        ("Brandy & Cognac",        "brandy-cognac",       "dalali-cat-cognac.jpg"),
        ("Rum & Tequila",          "rum-tequila",         "dalali-cat-rum.jpg"),
    ]
    for name, route, img in rows:
        _upsert("Item Group", name, {
            "item_group_name": name,
            "parent_item_group": "All Item Groups",
            "is_group": 0,
            "show_in_website": 1,
            "route": route,
            "website_image": I[img],
        })


def _seed_brands() -> None:
    print("\n── 2. Brands ──")
    for b in [
        "Johnnie Walker", "Jameson", "Jack Daniel's",
        "Moët & Chandon", "Hennessy", "Absolut", "Bacardi", "Tusker",
    ]:
        _upsert("Brand", b, {"brand": b})


def _seed_items() -> None:
    print("\n── 3. Items ──")
    # (code, name, group, brand, region, country, varietal, abv, vintage, case)
    rows = [
        ("DAL-JWB-750",   "Johnnie Walker Black Label 750ml",  "Whisky & Scotch",      "Johnnie Walker", "Speyside",     "Scotland",     "Blended Scotch Whisky",  40.0, 0,    12),
        ("DAL-JWG-750",   "Johnnie Walker Gold Label 750ml",   "Whisky & Scotch",      "Johnnie Walker", "Highlands",    "Scotland",     "Blended Scotch Whisky",  40.0, 0,    12),
        ("DAL-JAM-700",   "Jameson Irish Whiskey 700ml",       "Whisky & Scotch",      "Jameson",        "Cork",         "Ireland",      "Blended Irish Whiskey",  40.0, 0,    12),
        ("DAL-JD-700",    "Jack Daniel's Old No.7 700ml",      "Whisky & Scotch",      "Jack Daniel's",  "Tennessee",    "USA",          "Tennessee Whiskey",      40.0, 0,    12),
        ("DAL-CAB-750",   "Château Reserve Cabernet 750ml",    "Red Wine",             "Johnnie Walker", "Bordeaux",     "France",       "Cabernet Sauvignon",     13.5, 2019, 12),
        ("DAL-MALBEC-750","Mendoza Malbec 750ml",              "Red Wine",             "Jameson",        "Mendoza",      "Argentina",    "Malbec",                 14.0, 2020, 12),
        ("DAL-CHARD-750", "Stellenbosch Chardonnay 750ml",     "White Wine",           "Absolut",        "Stellenbosch", "South Africa", "Chardonnay",             13.0, 2021, 12),
        ("DAL-MOET-750",  "Moët Impérial Brut 750ml",          "Champagne & Sparkling","Moët & Chandon", "Épernay",      "France",       "Brut Champagne",         12.0, 0,     6),
        ("DAL-TUSK-500",  "Tusker Lager 500ml",                "Beer & Cider",         "Tusker",         "Nairobi",      "Kenya",        "Lager",                   4.2, 0,    24),
        ("DAL-ABSV-1L",   "Absolut Vodka 1 Litre",             "Gin & Vodka",          "Absolut",        "Åhus",         "Sweden",       "Premium Vodka",          40.0, 0,    12),
        ("DAL-HENN-700",  "Hennessy VS Cognac 700ml",          "Brandy & Cognac",      "Hennessy",       "Cognac",       "France",       "VS Cognac",              40.0, 0,    12),
        ("DAL-BAC-700",   "Bacardi Carta Blanca 700ml",        "Rum & Tequila",        "Bacardi",        "Puerto Rico",  "Puerto Rico",  "White Rum",              37.5, 0,    12),
    ]
    for code, name, grp, brand, region, country, varietal, abv, vintage, case_sz in rows:
        _upsert("Item", code, {
            "item_code": code, "item_name": name, "item_group": grp,
            "brand": brand, "stock_uom": "Nos", "is_stock_item": 1,
            "custom_case_size": case_sz,
            "custom_alcohol_content": abv,
            "custom_vintage_year": vintage or None,
            "custom_region": region,
            "custom_origin_country": country,
            "custom_wine_varietal": varietal,
        })


def _seed_website_items(I: dict) -> None:
    print("\n── 4. Website Items (products) ──")
    # (code, web_name, ranking, img_key)
    rows = [
        ("DAL-JWB-750",   "Johnnie Walker Black Label 750ml",    100, "dalali-prod-jwblack.jpg"),
        ("DAL-JWG-750",   "Johnnie Walker Gold Label 750ml",      90, "dalali-prod-jwgold.jpg"),
        ("DAL-JAM-700",   "Jameson Irish Whiskey 700ml",          85, "dalali-prod-jameson.jpg"),
        ("DAL-JD-700",    "Jack Daniel's Old No.7 700ml",         80, "dalali-prod-jd.jpg"),
        ("DAL-CAB-750",   "Château Reserve Cabernet Sauvignon",   75, "dalali-prod-cab.jpg"),
        ("DAL-MALBEC-750","Mendoza Malbec",                       70, "dalali-prod-malbec.jpg"),
        ("DAL-CHARD-750", "Stellenbosch Chardonnay",              65, "dalali-prod-chard.jpg"),
        ("DAL-MOET-750",  "Moët Impérial Brut",                   95, "dalali-prod-moet.jpg"),
        ("DAL-TUSK-500",  "Tusker Lager 500ml",                   60, "dalali-prod-tusker.jpg"),
        ("DAL-ABSV-1L",   "Absolut Vodka 1 Litre",                72, "dalali-prod-absolut.jpg"),
        ("DAL-HENN-700",  "Hennessy VS Cognac 700ml",             88, "dalali-prod-hennessy.jpg"),
        ("DAL-BAC-700",   "Bacardi Carta Blanca Rum 700ml",       55, "dalali-prod-bacardi.jpg"),
    ]
    for code, web_name, ranking, img in rows:
        _upsert_wi(code, {
            "web_item_name": web_name,
            "published": 1,
            "ranking": ranking,
            "website_image": I[img],
        })


def _seed_prices() -> None:
    print("\n── 5. Item Prices ──")
    for code, price in [
        ("DAL-JWB-750",    3200), ("DAL-JWG-750",    6500),
        ("DAL-JAM-700",    2800), ("DAL-JD-700",     2500),
        ("DAL-CAB-750",    1900), ("DAL-MALBEC-750", 1600),
        ("DAL-CHARD-750",  1450), ("DAL-MOET-750",   9800),
        ("DAL-TUSK-500",    280), ("DAL-ABSV-1L",    3600),
        ("DAL-HENN-700",   8500), ("DAL-BAC-700",    1950),
    ]:
        _upsert_price(code, price)


def _seed_pricing_rules() -> None:
    # Superseded by dt_ecommerce.seed_campaigns — that module uses the correct
    # apply_on="Item Group" + item_groups child table structure.
    # This stub is kept so seed.run() remains a single entry point; it delegates.
    print("\n── 6. Pricing Rules / Campaigns ──")
    print("  [DELEGATE] Calling seed_campaigns.run() …")
    from dt_ecommerce import seed_campaigns
    seed_campaigns.run()


def _seed_bundles(I: dict) -> None:
    print("\n── 7–10. Bundle Items, Product Bundles, Website Items, Prices ──")
    bundle_defs = [
        (
            "DAL-BND-WHISKY",
            "Dalali Whisky Tasting Bundle",
            "Whisky & Scotch",
            "Johnnie Walker",
            "JW Black, JW Gold, Jameson & Jack Daniel's. Curated whisky selection for tastings.",
            [("DAL-JWB-750", 2), ("DAL-JWG-750", 1), ("DAL-JAM-700", 1), ("DAL-JD-700", 2)],
            29500,
            50,
            "dalali-bnd-whisky.jpg",
        ),
        (
            "DAL-BND-WINE",
            "Dalali Red Wine Case Mix",
            "Red Wine",
            "Jameson",
            "Mixed 6-bottle case: Cabernet, Malbec & Chardonnay. Ideal for restaurants and bars.",
            [("DAL-CAB-750", 2), ("DAL-MALBEC-750", 2), ("DAL-CHARD-750", 2)],
            9500,
            45,
            "dalali-bnd-wine.jpg",
        ),
        (
            "DAL-BND-PARTY",
            "Dalali Party Starter Pack",
            "Rum & Tequila",
            "Bacardi",
            "Bacardi, Absolut, Jack Daniel's & Tusker lager. Serves up to 30 guests.",
            [("DAL-BAC-700", 2), ("DAL-ABSV-1L", 1), ("DAL-JD-700", 1), ("DAL-TUSK-500", 6)],
            14200,
            40,
            "dalali-bnd-party.jpg",
        ),
    ]
    for code, name, grp, brand, desc, components, price, ranking, img in bundle_defs:
        # Parent Item (non-stock)
        _upsert("Item", code, {
            "item_code": code, "item_name": name, "item_group": grp,
            "brand": brand, "stock_uom": "Nos", "is_stock_item": 0, "custom_case_size": 1,
        })
        # Product Bundle
        if frappe.db.exists("Product Bundle", {"new_item_code": code}):
            print(f"  [SKIP] Product Bundle: {code}")
        else:
            doc = frappe.get_doc({
                "doctype": "Product Bundle",
                "new_item_code": code,
                "description": desc,
                "items": [{"item_code": ic, "qty": qty, "uom": "Nos"} for ic, qty in components],
            })
            doc.insert(ignore_permissions=True)
            frappe.db.commit()
            print(f"  [OK]   Product Bundle: {code} ({len(components)} components)")
        # Website Item
        _upsert_wi(code, {
            "web_item_name": name,
            "published": 1,
            "ranking": ranking,
            "website_image": I[img],
        })
        # Price
        _upsert_price(code, price)


# ─── Public entry point ───────────────────────────────────────────────────────

def run() -> None:
    """
    Idempotent seed: inserts missing records, updates images on existing ones.
    bench --site erpnext.localhost execute dt_ecommerce.seed.run
    """
    frappe.set_user("Administrator")

    I = _download_all()

    _seed_item_groups(I)
    _seed_brands()
    _seed_items()
    _seed_website_items(I)
    _seed_prices()
    _seed_pricing_rules()
    _seed_bundles(I)

    ok  = sum(1 for p in I.values() if p)
    tot = len(IMGS)
    print(f"\n{'═' * 60}")
    print(f"✅  Dalali seed complete  —  {ok}/{tot} images downloaded")
    print(f"    bench --site erpnext.localhost clear-cache")
    print(f"    http://erpnext.localhost:8000")
    print(f"{'═' * 60}\n")
