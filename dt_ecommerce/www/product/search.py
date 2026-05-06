import frappe

from webshop.templates.pages.product_search import product_search # adjust import


def map_to_website_items(item_codes):
    if not item_codes:
        return []

    # 🔥 fetch only fields required by item_card macro
    results = frappe.get_all(
        "Website Item",
        filters={
            "item_code": ["in", item_codes],
            "published": 1
        },
        fields=[
            "item_code",
            "web_item_name",
            "route",
            "website_image",
            "item_group"
        ]
    )

    if not results:
        return []

    # 🔥 preserve ranking
    mapping = {r["item_code"]: r for r in results}

    ordered = [mapping[c] for c in item_codes if c in mapping]

    return ordered

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

    return context