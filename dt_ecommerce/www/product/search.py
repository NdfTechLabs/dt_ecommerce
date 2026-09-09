import frappe

from webshop.templates.pages.product_search import product_search # adjust import

from dt_ecommerce.utils import enrich_website_items


def map_to_website_items(item_codes):

    if not item_codes:
        return []

    # Fetch Website Item data
    results = frappe.get_all(
        "Website Item",
        filters={
            "item_code": ["in", item_codes],
            "published": 1
        },
        fields=[
            "name",
            "item_code",
            "item_name",
            "web_item_name",
            "route",
            "website_image",
            "item_group",
            "has_variants",
            "short_description",
            "web_long_description",
            "on_backorder",
        ]
    )

    if not results:
        return []

    # Preserve the ranking/order returned by resolve_section()
    mapping = {
        item["item_code"]: item
        for item in results
    }

    ordered = [
        mapping[c]
        for c in item_codes
        if c in mapping
    ]

    # Enrich items with information required by ProductGrid
    return enrich_website_items(ordered)

def get_context(context):
    q = (frappe.form_dict.get("q") or "").strip()
    context.q = q

    if not q:
        context.items = []
        return context

    # 🔥 call your search engine
    search_data = product_search(query=q, limit=20)

    results = search_data.get("results", [])

    if not results:
        context.items = []
        return context

    # 🔥 extract item_codes (important step)
    item_codes = []

    for r in results:
        # depends on your redis result structure
        code = r.get("item_code") or r.get("name")
        if code:
            item_codes.append(code)

    # 🔥 reuse your existing pipeline
    items = map_to_website_items(item_codes)

    context.items = items

    webshop_settings = frappe.get_single("Webshop Settings")

    context.webshop_settings = {
        "enabled": webshop_settings.enabled,
        "enable_wishlist": webshop_settings.enable_wishlist,
        "show_stock_availability": webshop_settings.show_stock_availability,
        "allow_items_not_in_stock": webshop_settings.allow_items_not_in_stock,
        "enable_checkout": webshop_settings.enable_checkout,
    }

    return context