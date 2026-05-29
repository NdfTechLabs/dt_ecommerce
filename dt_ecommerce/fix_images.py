"""
dt_ecommerce.fix_images
Patches website_image directly on Website Item (and Item Group) records.

The normal doc.save() path skips Attach Image fields that have no matching
File record in tabFile.  frappe.db.set_value bypasses that check and writes
the path directly to the column — which is all the webshop template needs
(it just renders <img src="{{ item.website_image }}"  />).

Run via:
    bench --site erpnext.localhost execute dt_ecommerce.fix_images.run
"""

import frappe

# ── Product (Website Item) images ────────────────────────────────────────────
PRODUCT_IMAGES = {
    "DAL-JWB-750":    "/files/dalali-prod-jwblack.jpg",
    "DAL-JWG-750":    "/files/dalali-prod-jwgold.jpg",
    "DAL-JAM-700":    "/files/dalali-prod-jameson.jpg",
    "DAL-JD-700":     "/files/dalali-prod-jd.jpg",
    "DAL-CAB-750":    "/files/dalali-prod-cab.jpg",
    "DAL-MALBEC-750": "/files/dalali-prod-malbec.jpg",
    "DAL-CHARD-750":  "/files/dalali-prod-chard.jpg",
    "DAL-MOET-750":   "/files/dalali-prod-moet.jpg",
    "DAL-TUSK-500":   "/files/dalali-prod-tusker.jpg",
    "DAL-ABSV-1L":    "/files/dalali-prod-absolut.jpg",
    "DAL-HENN-700":   "/files/dalali-prod-hennessy.jpg",
    "DAL-BAC-700":    "/files/dalali-prod-bacardi.jpg",
    # bundles
    "DAL-BND-WHISKY": "/files/dalali-bnd-whisky.jpg",
    "DAL-BND-WINE":   "/files/dalali-bnd-wine.jpg",
    "DAL-BND-PARTY":  "/files/dalali-bnd-party.jpg",
}

# ── Item Group category images ────────────────────────────────────────────────
GROUP_IMAGES = {
    "Whisky & Scotch":       "/files/dalali-cat-whisky.jpg",
    "Red Wine":              "/files/dalali-cat-redwine.jpg",
    "White Wine":            "/files/dalali-cat-whitewine.jpg",
    "Champagne & Sparkling": "/files/dalali-cat-champagne.jpg",
    "Beer & Cider":          "/files/dalali-cat-beer.jpg",
    "Gin & Vodka":           "/files/dalali-cat-gin-vodka.jpg",
    "Brandy & Cognac":       "/files/dalali-cat-cognac.jpg",
    "Rum & Tequila":         "/files/dalali-cat-rum.jpg",
}


def _set_wi_image(item_code: str, img_path: str) -> None:
    """Set website_image on a Website Item using a direct DB write."""
    wi_name = frappe.db.get_value("Website Item", {"item_code": item_code}, "name")
    if not wi_name:
        print(f"  [MISS] Website Item not found: {item_code}")
        return
    current = frappe.db.get_value("Website Item", wi_name, "website_image")
    if current == img_path:
        print(f"  [SKIP] {item_code}  (already set)")
        return
    frappe.db.set_value("Website Item", wi_name, "website_image", img_path)
    print(f"  [OK]   {item_code}  →  {img_path}")


def _set_group_image(group_name: str, img_path: str) -> None:
    """Set website_image on an Item Group using a direct DB write."""
    if not frappe.db.exists("Item Group", group_name):
        print(f"  [MISS] Item Group not found: {group_name}")
        return
    current = frappe.db.get_value("Item Group", group_name, "website_image")
    if current == img_path:
        print(f"  [SKIP] {group_name}  (already set)")
        return
    frappe.db.set_value("Item Group", group_name, "website_image", img_path)
    print(f"  [OK]   {group_name}  →  {img_path}")


def run() -> None:
    """
    Idempotent image patch.
    Uses frappe.db.set_value (direct SQL UPDATE) to bypass the Attach Image
    validation that requires a corresponding tabFile record.
    """
    frappe.set_user("Administrator")

    print("\n── Website Item images ──")
    for item_code, img_path in PRODUCT_IMAGES.items():
        _set_wi_image(item_code, img_path)

    print("\n── Item Group images ──")
    for group_name, img_path in GROUP_IMAGES.items():
        _set_group_image(group_name, img_path)

    frappe.db.commit()

    print(f"\n{'═' * 60}")
    print(f"  Website Items patched : {len(PRODUCT_IMAGES)}")
    print(f"  Item Groups  patched  : {len(GROUP_IMAGES)}")
    print(f"  Next step: bench --site erpnext.localhost clear-cache")
    print(f"{'═' * 60}\n")
