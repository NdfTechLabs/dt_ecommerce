"""
dt_ecommerce.catalog_guard
Layer-3 defence: prevents internal-operation items from being
published to the Dalali webshop.

Registered in hooks.py under doc_events → Website Item → validate.
"""

import frappe
from frappe import _

# Parent group that marks everything BELOW it as internal / non-web
INTERNAL_PARENT = "Internal Operations"


def get_internal_groups() -> set[str]:
    """Return the set of all Item Group names whose ancestor is INTERNAL_PARENT."""
    if not frappe.db.exists("Item Group", INTERNAL_PARENT):
        return set()
    # Walk the nested-set tree: all descendants of Internal Operations
    lft, rgt = frappe.db.get_value("Item Group", INTERNAL_PARENT, ["lft", "rgt"])
    rows = frappe.db.get_all(
        "Item Group",
        filters={"lft": [">=", lft], "rgt": ["<=", rgt]},
        pluck="name",
    )
    return set(rows)


def block_internal_publish(doc, method=None):
    """
    Validate hook on Website Item.
    Raises ValidationError if the item's group lives under Internal Operations,
    or if the group explicitly has show_in_website = 0.
    """
    if not doc.published:
        return  # unpublishing is always allowed

    item_group = frappe.db.get_value("Item", doc.item_code, "item_group")
    if not item_group:
        return

    # Check 1: group is under the Internal Operations subtree
    internal_groups = get_internal_groups()
    if item_group in internal_groups:
        frappe.throw(
            _("Item {0} belongs to the internal group '{1}' and cannot be "
              "published to the webshop. Move it to a Wholesale Catalog "
              "group first.").format(doc.item_code, item_group),
            title=_("Webshop Publication Blocked"),
        )

    # Check 2: group has show_in_website explicitly disabled
    show_in_website = frappe.db.get_value("Item Group", item_group, "show_in_website")
    if not show_in_website:
        frappe.throw(
            _("Item {0} is in group '{1}' which is not enabled for the website "
              "(show_in_website = No). Enable the group for the website, or "
              "move the item to a Wholesale Catalog group.").format(
                doc.item_code, item_group),
            title=_("Webshop Publication Blocked"),
        )
