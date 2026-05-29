"""
dt_ecommerce.restructure_groups
Layer-1 defence: creates a clean two-branch Item Group tree.

Run via:
    bench --site erpnext.localhost execute dt_ecommerce.restructure_groups.run
"""

import frappe
from frappe import _


CATALOG_PARENT   = "Dalali Wholesale Catalog"
INTERNAL_PARENT  = "Internal Operations"

CATALOG_GROUPS = [
    "Whisky & Scotch",
    "Red Wine",
    "White Wine",
    "Champagne & Sparkling",
    "Beer & Cider",
    "Gin & Vodka",
    "Brandy & Cognac",
    "Rum & Tequila",
]

INTERNAL_GROUPS = [
    "Products",
    "Raw Material",
    "Services",
    "Sub Assemblies",
    "Consumable",
]


def _ensure_parent_group(name: str, show_in_website: int) -> None:
    """Create the parent group if it doesn't already exist."""
    if frappe.db.exists("Item Group", name):
        doc = frappe.get_doc("Item Group", name)
        changed = False
        if doc.parent_item_group != "All Item Groups":
            doc.parent_item_group = "All Item Groups"
            changed = True
        if doc.is_group != 1:
            doc.is_group = 1
            changed = True
        if doc.show_in_website != show_in_website:
            doc.show_in_website = show_in_website
            changed = True
        if changed:
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            print(f"  [UPD]  Item Group (parent): {name}")
        else:
            print(f"  [SKIP] Item Group (parent): {name}")
    else:
        doc = frappe.get_doc({
            "doctype": "Item Group",
            "item_group_name": name,
            "parent_item_group": "All Item Groups",
            "is_group": 1,
            "show_in_website": show_in_website,
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"  [OK]   Item Group (parent): {name}")


def _reparent(group_name: str, new_parent: str, show_in_website: int) -> None:
    """Move an Item Group to a new parent and set show_in_website."""
    if not frappe.db.exists("Item Group", group_name):
        print(f"  [SKIP] Item Group not found: {group_name}")
        return
    doc = frappe.get_doc("Item Group", group_name)
    changed = False
    if doc.parent_item_group != new_parent:
        doc.parent_item_group = new_parent
        changed = True
    if doc.show_in_website != show_in_website:
        doc.show_in_website = show_in_website
        changed = True
    if doc.is_group != 0:
        doc.is_group = 0
        changed = True
    if changed:
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        print(f"  [UPD]  {group_name}  →  parent: {new_parent}, web: {show_in_website}")
    else:
        print(f"  [SKIP] {group_name}  (already correct)")


def _unpublish_internal_items() -> None:
    """
    Find any Website Items whose Item Group is in the internal branch
    and unpublish them. Logs each one so staff can review.
    """
    internal_names = set(INTERNAL_GROUPS + [INTERNAL_PARENT])
    wi_list = frappe.get_all(
        "Website Item",
        filters={"published": 1},
        fields=["name", "item_code", "item_group"],
    )
    for wi in wi_list:
        if wi.item_group in internal_names:
            frappe.db.set_value("Website Item", wi.name, "published", 0)
            frappe.db.commit()
            print(f"  [UNPUBLISH] {wi.item_code}  (group: {wi.item_group})")


def run() -> None:
    """
    Idempotent restructure:
      1. Create 'Dalali Wholesale Catalog' parent group  (show_in_website=1)
      2. Create 'Internal Operations' parent group       (show_in_website=0)
      3. Move 8 liquor categories under Wholesale Catalog
      4. Move 5 internal groups under Internal Operations, set show_in_website=0
      5. Unpublish any Website Items that ended up in internal groups
    """
    frappe.set_user("Administrator")

    print("\n── Layer 1 · Item Group restructure ──")

    # Step 1 & 2: create the two parent branches
    _ensure_parent_group(CATALOG_PARENT,  show_in_website=1)
    _ensure_parent_group(INTERNAL_PARENT, show_in_website=0)

    # Step 3: move liquor categories under the catalog branch
    print(f"\n  Moving catalog groups under '{CATALOG_PARENT}' …")
    for g in CATALOG_GROUPS:
        _reparent(g, CATALOG_PARENT, show_in_website=1)

    # Step 4: move operational groups under the internal branch
    print(f"\n  Moving internal groups under '{INTERNAL_PARENT}' …")
    for g in INTERNAL_GROUPS:
        _reparent(g, INTERNAL_PARENT, show_in_website=0)

    # Step 5: unpublish any accidental webshop listings for internal items
    print("\n  Unpublishing internal items from webshop …")
    _unpublish_internal_items()

    print("\n── Layer 2 reminder ──")
    print("  Website Item.published=1 remains the primary publication gate.")
    print("  Internal items have no Website Item records by convention.")

    print("\n── Layer 3 reminder ──")
    print("  hooks.py doc_event 'Website Item → validate' is registered.")
    print("  Run: bench --site erpnext.localhost clear-cache")
    print("  to activate the catalog_guard validation hook.\n")
