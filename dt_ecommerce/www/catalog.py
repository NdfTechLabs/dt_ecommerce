"""
dt_ecommerce.www.catalog
Category Listing & Filter Page — B2B left-sidebar + 5-column dense grid.

URL: /catalog
Query params (all optional, all combinable):
    item_group      — active Item Group name
    custom_region   — origin region / distillery
    custom_varietal — wine varietal / style
    custom_vintage  — vintage year (integer)
    min_price       — KES minimum bottle price
    max_price       — KES maximum bottle price
    search          — free-text keyword
    packaging       — 'case' | 'bottle' (informational; no DB field yet)
    show_vol_only   — '1' = restrict to items that have ≥1 active Pricing Rule
    brands          — repeatable: ?brands=Jameson&brands=Absolut
    page            — pagination page number (default 1)
"""

import frappe
from frappe.utils import flt, cint
from urllib.parse import quote

CATALOG_PARENT = "Dalali Wholesale Catalog"
PAGE_SIZE = 40   # 5 cols × 8 rows


# ── param helpers ────────────────────────────────────────────────────────────

def _p(key, default=""):
    """Read a single scalar query param."""
    v = frappe.form_dict.get(key, default)
    if isinstance(v, list):
        return v[0].strip() if v else default
    return str(v).strip() if v is not None else default


def _plist(key):
    """Read a multi-value query param."""
    v = frappe.form_dict.get(key)
    if v is None:
        return []
    if isinstance(v, list):
        return [x for x in v if x]
    return [v] if v else []


# ── URL builder (preserves all active filters) ───────────────────────────────

def _build_url(overrides: dict, base_params: dict) -> str:
    """Build a /catalog? URL merging base_params with overrides."""
    merged = dict(base_params)
    merged.update(overrides)
    parts = []
    for k, v in merged.items():
        if k == "brands":
            for b in (v if isinstance(v, list) else [v]):
                if b:
                    parts.append(f"brands={quote(str(b))}")
        elif v not in (None, "", 0, "0"):
            parts.append(f"{k}={quote(str(v))}")
    return "/catalog?" + "&".join(parts) if parts else "/catalog"


# ── item count helper ─────────────────────────────────────────────────────────

def _count(group_name):
    return frappe.db.count("Website Item", {"item_group": group_name, "published": 1})


# ── main context ─────────────────────────────────────────────────────────────

def get_context(context):
    context.full_width = 1
    context.no_breadcrumbs = 1

    # ── read params ──────────────────────────────────────────────────────────
    active_group    = _p("item_group")
    active_region   = _p("custom_region")
    active_varietal = _p("custom_varietal")
    active_vintage  = _p("custom_vintage")
    active_brand    = _p("brand")          # single brand from category tree link
    search_q        = _p("search")
    packaging       = _p("packaging")
    show_vol_only   = _p("show_vol_only") == "1"
    min_price_raw   = _p("min_price", "0")
    max_price_raw   = _p("max_price", "0")
    page            = max(1, cint(_p("page", "1")))
    active_brands   = _plist("brands")     # multi-value checkboxes

    min_price = flt(min_price_raw)
    max_price = flt(max_price_raw)

    # Base param dict (for pagination / clear-filter URLs)
    base_params = {}
    if active_group:    base_params["item_group"]       = active_group
    if active_brand:    base_params["brand"]            = active_brand
    if active_brands:   base_params["brands"]           = active_brands
    if active_region:   base_params["custom_region"]    = active_region
    if active_varietal: base_params["custom_varietal"]  = active_varietal
    if active_vintage:  base_params["custom_vintage"]   = active_vintage
    if search_q:        base_params["search"]           = search_q
    if packaging:       base_params["packaging"]        = packaging
    if show_vol_only:   base_params["show_vol_only"]    = "1"

    # ── breadcrumb ───────────────────────────────────────────────────────────
    crumbs = [
        {"label": "Home",      "url": "/"},
        {"label": "Portfolio", "url": "/catalog"},
    ]
    if active_group:
        parent = frappe.db.get_value("Item Group", active_group, "parent_item_group")
        if parent and parent not in ("All Item Groups", CATALOG_PARENT):
            crumbs.append({
                "label": parent,
                "url":   f"/catalog?item_group={quote(parent)}",
            })
        crumbs.append({"label": active_group, "url": ""})
    context.breadcrumb   = crumbs
    context.active_group = active_group
    context.page_title   = active_group or "All Products"

    # ── top-level catalog categories ─────────────────────────────────────────
    top_groups = frappe.get_all(
        "Item Group",
        filters={"parent_item_group": CATALOG_PARENT, "show_in_website": 1},
        fields=["name", "item_group_name"],
        order_by="item_group_name asc",
    )
    for g in top_groups:
        g["url"] = f"/catalog?item_group={quote(g['name'])}"
    context.top_groups = top_groups

    # ── sidebar sub-group / sibling facets ───────────────────────────────────
    if active_group:
        children = frappe.get_all(
            "Item Group",
            filters={"parent_item_group": active_group, "show_in_website": 1},
            fields=["name", "item_group_name"],
            order_by="item_group_name asc",
        )
        for c in children:
            c["count"] = _count(c["name"])
            c["url"]   = f"/catalog?item_group={quote(c['name'])}"
        sub_groups = [c for c in children if c["count"] > 0]

        if not sub_groups:
            # Leaf node: show siblings so user can pivot
            parent = frappe.db.get_value("Item Group", active_group, "parent_item_group")
            if parent:
                siblings = frappe.get_all(
                    "Item Group",
                    filters={"parent_item_group": parent, "show_in_website": 1},
                    fields=["name", "item_group_name"],
                    order_by="item_group_name asc",
                )
                for s in siblings:
                    s["count"]  = _count(s["name"])
                    s["url"]    = f"/catalog?item_group={quote(s['name'])}"
                    s["active"] = s["name"] == active_group
                sub_groups = siblings
    else:
        sub_groups = []
        for g in top_groups:
            sub_groups.append({
                "name":            g["name"],
                "item_group_name": g["item_group_name"],
                "url":             g["url"],
                "count":           _count(g["name"]),
                "active":          False,
            })
    context.sub_groups = sub_groups

    # ── sidebar filter options ────────────────────────────────────────────────
    context.all_brands      = frappe.get_all("Brand", fields=["name"], order_by="name asc")
    context.active_brands   = active_brands
    context.active_brand    = active_brand
    context.active_region   = active_region
    context.active_varietal = active_varietal
    context.active_vintage  = active_vintage
    context.packaging       = packaging
    context.show_vol_only   = show_vol_only
    context.search_q        = search_q

    context.regions = [
        r[0] for r in frappe.db.sql(
            "SELECT DISTINCT custom_region FROM `tabItem` "
            "WHERE custom_region IS NOT NULL AND custom_region != '' "
            "ORDER BY custom_region"
        )
    ]
    context.varietals = [
        r[0] for r in frappe.db.sql(
            "SELECT DISTINCT custom_wine_varietal FROM `tabItem` "
            "WHERE custom_wine_varietal IS NOT NULL AND custom_wine_varietal != '' "
            "ORDER BY custom_wine_varietal"
        )
    ]
    context.vintages = [
        int(r[0]) for r in frappe.db.sql(
            "SELECT DISTINCT custom_vintage_year FROM `tabItem` "
            "WHERE custom_vintage_year IS NOT NULL AND custom_vintage_year > 0 "
            "ORDER BY custom_vintage_year DESC"
        )
    ]

    # ── price slider bounds ───────────────────────────────────────────────────
    price_row = frappe.db.sql(
        "SELECT MIN(ip.price_list_rate), MAX(ip.price_list_rate) "
        "FROM `tabItem Price` ip "
        "JOIN `tabWebsite Item` wi ON wi.item_code = ip.item_code "
        "WHERE ip.selling = 1 AND ip.price_list = 'Standard Selling' AND wi.published = 1"
    )
    p_bound_min = int(flt(price_row[0][0])) if price_row and price_row[0][0] else 0
    p_bound_max = int(flt(price_row[0][1])) if price_row and price_row[0][1] else 50000

    context.price_bound_min = p_bound_min
    context.price_bound_max = p_bound_max
    context.min_price       = int(min_price) if min_price > 0 else p_bound_min
    context.max_price       = int(max_price) if max_price > 0 else p_bound_max

    # ── product query ─────────────────────────────────────────────────────────
    conds = ["wi.published = 1", "ig.show_in_website = 1"]
    vals  = []

    # Category: use nested set lft/rgt for descendent matching
    if active_group:
        lr = frappe.db.get_value("Item Group", active_group, ["lft", "rgt"], as_dict=True)
        if lr:
            conds.append("ig.lft >= %s AND ig.rgt <= %s")
            vals += [lr.lft, lr.rgt]
        else:
            conds.append("wi.item_group = %s")
            vals.append(active_group)
    else:
        cat_lr = frappe.db.get_value("Item Group", CATALOG_PARENT, ["lft", "rgt"], as_dict=True)
        if cat_lr:
            conds.append("ig.lft > %s AND ig.rgt < %s")
            vals += [cat_lr.lft, cat_lr.rgt]

    # Brands (merge single + checklist)
    combined_brands = list({b for b in ([active_brand] if active_brand else []) + active_brands if b})
    if combined_brands:
        ph = ", ".join(["%s"] * len(combined_brands))
        conds.append(f"i.brand IN ({ph})")
        vals += combined_brands

    if active_region:
        conds.append("i.custom_region = %s");       vals.append(active_region)
    if active_varietal:
        conds.append("i.custom_wine_varietal = %s"); vals.append(active_varietal)
    if active_vintage:
        conds.append("i.custom_vintage_year = %s"); vals.append(active_vintage)

    # Price range (only apply if within bounds)
    if min_price > 0:
        conds.append("COALESCE(ip.price_list_rate, 0) >= %s"); vals.append(min_price)
    if max_price > 0 and max_price < p_bound_max:
        conds.append("COALESCE(ip.price_list_rate, 0) <= %s"); vals.append(max_price)

    # Free-text
    if search_q:
        conds.append(
            "(wi.web_item_name LIKE %s OR i.item_code LIKE %s "
            " OR i.brand LIKE %s OR i.custom_region LIKE %s "
            " OR i.custom_wine_varietal LIKE %s)"
        )
        vals += [f"%{search_q}%"] * 5

    # Volume-discount-only filter
    if show_vol_only:
        conds.append(
            "EXISTS (SELECT 1 FROM `tabPricing Rule Item Group` prig "
            "        JOIN `tabPricing Rule` pr ON pr.name = prig.parent "
            "        WHERE prig.item_group = i.item_group "
            "          AND pr.selling = 1 AND pr.disable = 0 "
            "          AND pr.min_qty > 0 "
            "          AND (pr.valid_upto IS NULL OR pr.valid_upto >= CURDATE()))"
        )

    where = " AND ".join(conds)
    base_join = """
        FROM `tabWebsite Item` wi
        INNER JOIN `tabItem` i ON i.name = wi.item_code
        INNER JOIN `tabItem Group` ig ON ig.name = i.item_group
        LEFT JOIN `tabItem Price` ip
            ON ip.item_code = wi.item_code
           AND ip.selling = 1
           AND ip.price_list = 'Standard Selling'
    """

    total_count = frappe.db.sql(
        f"SELECT COUNT(DISTINCT wi.name) {base_join} WHERE {where}",
        vals
    )[0][0]

    offset = (page - 1) * PAGE_SIZE
    rows = frappe.db.sql(
        f"""
        SELECT
            wi.item_code, wi.web_item_name, wi.website_image,
            wi.item_group, wi.route,
            i.brand, i.custom_case_size, i.custom_region,
            i.custom_origin_country, i.custom_wine_varietal,
            i.custom_alcohol_content, i.custom_vintage_year,
            COALESCE(ip.price_list_rate, 0) AS price,
            COALESCE(ip.currency, 'KES')    AS currency
        {base_join}
        WHERE {where}
        ORDER BY wi.ranking DESC, wi.modified DESC
        LIMIT %s OFFSET %s
        """,
        vals + [PAGE_SIZE, offset],
        as_dict=True,
    )

    for r in rows:
        case_sz         = int(r.get("custom_case_size") or 12)
        bottle          = flt(r.get("price") or 0)
        r["case_size"]  = case_sz
        r["case_price"] = bottle * case_sz
        r["url"]        = f"/{r['route']}" if r.get("route") else "#"
        vintage         = r.get("custom_vintage_year")
        r["vintage_display"] = str(int(vintage)) if vintage and int(vintage) > 0 else ""

    context.items        = rows
    context.total_count  = total_count
    context.page         = page
    context.page_size    = PAGE_SIZE
    context.total_pages  = max(1, (total_count + PAGE_SIZE - 1) // PAGE_SIZE)

    # ── pagination URLs ───────────────────────────────────────────────────────
    context.prev_url = (
        _build_url({"page": page - 1}, base_params) if page > 1 else ""
    )
    context.next_url = (
        _build_url({"page": page + 1}, base_params) if page < context.total_pages else ""
    )

    # Sidebar form action (preserves search_q + pagination reset)
    context.filter_action = "/catalog"

    # ── clear-single-filter URLs for active filter pills ─────────────────────
    def _clear(key):
        """base_params minus one key, page reset."""
        trimmed = {k: v for k, v in base_params.items() if k != key}
        return _build_url({"page": ""}, trimmed)

    context.clear_search_url   = _clear("search")           if search_q       else ""
    context.clear_region_url   = _clear("custom_region")    if active_region  else ""
    context.clear_varietal_url = _clear("custom_varietal")  if active_varietal else ""
    context.clear_vintage_url  = _clear("custom_vintage")   if active_vintage  else ""
    context.clear_brands_url   = _clear("brands")           if active_brands   else ""

    # ── expose base_params to template (for JS data attribute) ───────────────
    context.base_params = base_params

    return context
