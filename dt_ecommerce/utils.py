import frappe
from frappe.utils import flt

def extend_dalali_context(context: dict) -> None:
	"""Inject Dalali wholesale data into the website rendering context.

	Hooked via ``update_website_context`` in hooks.py.
	Adds ``dalali_item_code`` and ``dalali_case_size`` so templates can render
	a JSON bootstrap blob without raw DB calls in Jinja.
	"""
	doc = context.get("doc")
	if not doc:
		return

	doctype = getattr(doc, "doctype", None) or (doc.get("doctype") if isinstance(doc, dict) else None)
	if doctype != "Website Item":
		return

	item_code = getattr(doc, "item_code", None) or (doc.get("item_code") if isinstance(doc, dict) else None)
	if not item_code:
		return

	case_size = frappe.db.get_value("Item", item_code, "custom_case_size") or 12

	# Expose minimal bootstrap data; full meta is fetched client-side via frappe.call
	context["dalali_item_code"] = item_code
	context["dalali_case_size"] = int(case_size)


def dalali_bootstrap_script(context: dict) -> str:
	"""Render an inline <script> block that seeds window.dalali_* variables.

	Called as a Jinja global via the ``jinja.methods`` hook, so any template
	can call {{ dalali_bootstrap_script(context) | safe }}.
	"""
	item_code = context.get("dalali_item_code", "")
	case_size = context.get("dalali_case_size", 12)

	if not item_code:
		return ""

	return (
		f'<script>'
		f'window.dalali_item_code = {frappe.as_json(item_code)};'
		f'window.dalali_case_size = {int(case_size)};'
		f'</script>'
	)

def enrich_website_items(items):
    from webshop.webshop.shopping_cart.product_info import (
        get_product_info_for_website,
        set_product_info_for_website,
    )

    for item in items:
        item_code = item["item_code"]

        # ---------------------------------------------------------
        # Let native Webshop populate its standard product info
        # ---------------------------------------------------------

        set_product_info_for_website(item)

        # ---------------------------------------------------------
        # Get native product/cart information
        # ---------------------------------------------------------

        try:
            response = get_product_info_for_website(
                item_code,
                skip_quotation_creation=True
            ) or {}

            product_info = response.get("product_info") or {}
            cart_settings = response.get("cart_settings") or {}

        except Exception:
            product_info = {}
            cart_settings = {}

        # ---------------------------------------------------------
        # Native ProductGrid properties
        # ---------------------------------------------------------

        item["has_variants"] = bool(
            item.get("has_variants")
        )

        item["on_backorder"] = bool(
            product_info.get("on_backorder")
        )

        item["in_stock"] = bool(
            product_info.get("in_stock")
        )

        # These are not provided by get_product_info_for_website()
        # so default them unless you populate them elsewhere.
        item["wished"] = bool(
            item.get("wished", False)
        )

        item["in_cart"] = bool(
            item.get("in_cart", False)
        )

        # ---------------------------------------------------------
        # Price information
        # ---------------------------------------------------------

        price = product_info.get("price") or {}

        item["formatted_price"] = (
            price.get("formatted_price")
            or ""
        )

        item["formatted_mrp"] = (
            price.get("formatted_mrp")
            or ""
        )

        item["discount"] = (
            price.get("formatted_discount_percent")
            or price.get("formatted_discount_rate")
            or ""
        )

        # ---------------------------------------------------------
        # Raw price
        # ---------------------------------------------------------

        item["price"] = flt(
            price.get("price_list_rate")
            or item.get("price")
            or 0
        )

        item["currency"] = (
            price.get("currency")
            or item.get("currency")
            or "KES"
        )

        # ---------------------------------------------------------
        # Case size - custom Dalali field
        # ---------------------------------------------------------

        item["case_size"] = int(
            frappe.db.get_value(
                "Item",
                item_code,
                "custom_case_size"
            ) or 12
        )

        # ---------------------------------------------------------
        # URL
        # ---------------------------------------------------------

        item["url"] = (
            f"/{item['route']}"
            if item.get("route")
            else "#"
        )

    return items
