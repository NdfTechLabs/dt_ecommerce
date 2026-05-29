# Dalali Wine Wholesaler — dt_ecommerce Implementation Doc

> **App:** `dt_ecommerce` | **Frappe version:** v17 | **Last updated:** 2026-05-29 (rev 15)
>
> This document is the living reference for everything built in `dt_ecommerce` as the Dalali B2B Wholesale Liquor webshop. Update it every time a new feature, fix, or structural change is made.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture & Design Principles](#architecture--design-principles)
3. [Directory Tree](#directory-tree)
4. [Hooks Registration (`hooks.py`)](#hooks-registration-hookspy)
5. [Custom Fields (`fixtures/custom_field.json`)](#custom-fields-fixturescustom_fieldjson)
6. [Server-Side Context (`utils.py`)](#server-side-context-utilspy)
7. [API Endpoints (`api/wholesale.py`)](#api-endpoints-apiwholesalepy)
8. [Homepage Route (`www/index`)](#homepage-route-wwwindex)
9. [Catalog Page (`www/catalog`)](#catalog-page-wwwcatalog)
10. [Product Detail Page Override (`templates/`)](#product-detail-page-override-templates)
11. [Frontend JavaScript (`public/js/`)](#frontend-javascript-publicjs)
12. [CSS / Brand Theme (`public/css/`)](#css--brand-theme-publiccss)
13. [Seed Data & Utilities](#seed-data--utilities)
14. [Webshop — What Was Touched](#webshop--what-was-touched)
15. [Deployment Steps](#deployment-steps)
16. [Changelog](#changelog)

---

## Overview

Dalali is a high-converting B2B/Wholesale Liquor Distribution portal layered on top of the Frappe `webshop` app. It is built entirely inside `dt_ecommerce` using Frappe's hook and template-override system — **no core `frappe/`, `webshop/`, or `erpnext/` files are modified**.

### Key user-facing features

| Feature | Status | Entry point |
|---|---|---|
| Global sticky promo bar | ✅ Done | `dalali.js → injectPromoBar()` |
| Dalali brand theme (claret + gold) | ✅ Done | `theme_dalali.css` |
| Homepage hero + labelled filter strip | ✅ Done | `www/index.html` + `www/index.py` |
| Category grid (spaced image-dominant cards) | ✅ Done | `www/index.html` server-side + `dalali.js → injectCategoryGrid()` |
| Featured wholesale product cards | ✅ Done | `www/index.html` + `www/index.py` + `api/wholesale.get_bulk_pricing_tiers` |
| Curated wholesale bundles section | ✅ Done | `www/index.html` + `www/index.py` (queries `Product Bundle`) |
| Promotional banner / announcement strip | ✅ Done | `www/index.html` + `www/index.py` (active `Pricing Rule` records by date/priority) |
| **Catalog listing & filter page** | ✅ Done | `www/catalog.py` + `www/catalog.html` |
| Horizontal sticky filter bar on listing pages | ✅ Done | `dalali.js → convertFiltersToHorizontal()` |
| Bottle / Case unit toggle on PDP | ✅ Done | `dalali.js → injectUnitCaseToggle()` |
| Add to Cart + Buy Now CTA buttons on PDP | ✅ Done | `dalali.js → injectUnitCaseToggle()` + `pdpCartAction()` |
| Recommended items grid on PDP | ✅ Done | `dalali.js → initPDPRecommended()` + `api/wholesale.get_recommended_items` |
| Volume pricing tier table on PDP | ✅ Done | `dalali.js → injectTierTable()` |
| Tier detail modal on PDP | ✅ Done | `dalali.js → openTierModal()` |
| Wine/spirits metadata grid on PDP | ✅ Done | `dalali.js → injectWineMeta()` |
| Wholesale custom fields on Item master | ✅ Done | `fixtures/custom_field.json` |
| Seed data (items, prices, bundles, campaigns) | ✅ Done | `seed.py`, `seed_campaigns.py` |
| Catalog guard (block internal-item publishing) | ✅ Done | `catalog_guard.py` + `hooks.py doc_events` |

---

## Architecture & Design Principles

### Overlay pattern — never modify core apps

Frappe's Jinja `ChoiceLoader` searches apps in the order listed in `sites/<site>/apps.txt`. `dt_ecommerce` sits at position 5, `webshop` at position 9. Any template placed at an identical path in `dt_ecommerce/templates/` automatically shadows the webshop version.

### Guardrails followed

1. Never modify files inside `apps/frappe/`, `apps/webshop/`, or `apps/erpnext/`.
2. All template overrides use `{% extends %}` + `{% block %}` blocks where possible.
3. No raw SQL inside Jinja templates — DB calls go through Python context controllers or `@frappe.whitelist` API functions.
4. All CSS/JS registered via `web_include_css` / `web_include_js` in `hooks.py`.
5. All DOM manipulation runs inside `frappe.ready()` to avoid racing native webshop events.
6. Cart/qty state managed by webshop is never replaced — only the existing native qty `<input>` value is set.
7. All user-facing strings wrapped in `__()` for i18n.

---

## Directory Tree

```
apps/dt_ecommerce/
├── DALALI_WEBSHOP.md                  ← this file
├── DALALI_DATA_GUIDE.md               NEW — seed data & operational data guide
│
└── dt_ecommerce/
    ├── hooks.py                       MODIFIED — all Frappe hook registrations
    ├── utils.py                       NEW — server-side context helpers
    ├── catalog_guard.py               NEW — ValidationError for internal item publishing
    ├── fix_images.py                  NEW — direct DB patch for website_image fields
    ├── seed.py                        NEW — full data seed (items, prices, bundles)
    ├── seed_campaigns.py              NEW — seed 6 campaigns + 10 Pricing Rules
    ├── restructure_groups.py          NEW — build two-branch Item Group tree
    ├── __init__.py
    ├── modules.txt
    ├── patches.txt
    │
    ├── api/
    │   ├── __init__.py                NEW — package marker
    │   └── wholesale.py               NEW — 4 whitelisted guest API endpoints
    │
    ├── fixtures/
    │   └── custom_field.json          NEW — 10 custom fields on Item doctype
    │
    ├── public/
    │   ├── css/
    │   │   ├── base.css               PRE-EXISTING — generic layout variables
    │   │   ├── theme_glass.css        PRE-EXISTING — glass UI theme
    │   │   └── theme_dalali.css       MODIFIED — Dalali brand theme + all component CSS
    │   └── js/
    │       ├── theme.js               PRE-EXISTING — navbar scroll + search typeahead
    │       └── dalali.js              MODIFIED — all wholesale UI logic incl. catalog
    │
    ├── templates/
    │   ├── generators/item/
    │   │   └── item.html              OVERRIDE — shadows webshop PDP template
    │   └── includes/
    │       ├── footer/footer.html     PRE-EXISTING
    │       └── navbar/navbar.html     PRE-EXISTING
    │
    └── www/
        ├── index.py                   MODIFIED — homepage context controller
        ├── index.html                 MODIFIED — hero + filter strip + all sections
        ├── catalog.py                 NEW — catalog page context (B2B filter page)
        ├── catalog.html               NEW — left-sidebar + 5-col product grid
        └── product/
            ├── search.py              PRE-EXISTING
            └── search.html            PRE-EXISTING
```

---

## Hooks Registration (`hooks.py`)

```python
required_apps = ["webshop"]

# v=1.2 — bump _V whenever CSS/JS changes to force browsers to re-fetch
# (Werkzeug ignores query strings for static files; browsers treat each ?v= as a new URL)
_V = "?v=1.2"

web_include_css = [
    "/assets/dt_ecommerce/css/base.css"         + _V,
    "/assets/dt_ecommerce/css/theme_glass.css"  + _V,
    "/assets/dt_ecommerce/css/theme_dalali.css" + _V,
]

web_include_js = [
    "/assets/dt_ecommerce/js/theme.js"  + _V,
    "/assets/dt_ecommerce/js/dalali.js" + _V,
]

fixtures = [
    {
        "dt": "Custom Field",
        "filters": [["dt", "=", "Item"], ["fieldname", "in", [
            "custom_dalali_section", "custom_liquor_category", "custom_wine_varietal",
            "custom_origin_country", "custom_region", "custom_dalali_col",
            "custom_vintage_year", "custom_alcohol_content", "custom_case_size", "custom_importer",
        ]]],
    }
]

update_website_context = ["dt_ecommerce.utils.extend_dalali_context"]

jinja = {
    "methods": ["dt_ecommerce.utils.dalali_bootstrap_script"],
}

doc_events = {
    "Website Item": {
        "validate": "dt_ecommerce.catalog_guard.block_internal_publish",
    }
}
```

| Hook | Purpose |
|---|---|
| `required_apps` | Declares `webshop` as a hard dependency |
| `_V` | Version string appended to all static asset URLs for cache busting — bump when CSS/JS changes |
| `web_include_css` | Injects all three CSS files (with version query string) into every website page `<head>` |
| `web_include_js` | Injects both JS files (with version query string) into every website page `<body>` |
| `fixtures` | Specifies the Custom Field records to deploy/export with `bench import-fixtures` |
| `update_website_context` | Calls `extend_dalali_context` on every page render to inject `dalali_item_code` and `dalali_case_size` |
| `jinja.methods` | Exposes `dalali_bootstrap_script` as a callable Jinja global in all templates |
| `doc_events` | `Website Item.validate` → `catalog_guard.block_internal_publish` prevents accidental publishing of internal items |

### Cache busting

Frappe's dev server serves plain static CSS/JS files with `Cache-Control: max-age=43200` (12 h). Since the files have no content hash in their URL, browsers cache them indefinitely until that window expires. The `_V` version string converts the URL to a cache-miss whenever it is bumped.

**Workflow:** edit CSS/JS → `bench build --app dt_ecommerce` → bump `_V` in `hooks.py` → `bench --site erpnext.localhost clear-cache`.

> Note: Frappe's esbuild pipeline (`bench build`) discovers `*.bundle.{css,scss,js}` entry points and emits content-hashed files to `public/dist/`. We do **not** use this pipeline for dt_ecommerce because the postcss2 plugin resolves CSS `@import` paths relative to a temp directory, which breaks when importing sibling files. The manual `_V` version string achieves equivalent cache busting with zero build complexity.

---

## Custom Fields (`fixtures/custom_field.json`)

All fields are added to the **`Item`** doctype under a collapsible **"Wholesale & Beverage Details"** section.

| Fieldname | Type | Details |
|---|---|---|
| `custom_dalali_section` | Section Break | Collapsible group header, inserted after `item_group` |
| `custom_liquor_category` | Select | Options: Wine, Whiskey, Vodka, Beer, Gin, Champagne & Sparkling, Tequila, Rum, Brandy, Mixers & Syrups, Other — search indexed |
| `custom_wine_varietal` | Small Text | e.g. "Cabernet Sauvignon", "Single Malt", "London Dry" |
| `custom_origin_country` | Data | e.g. "France" — search indexed |
| `custom_region` | Data | e.g. "Bordeaux", "Speyside", "Cognac" |
| `custom_dalali_col` | Column Break | Creates two-column layout in the section |
| `custom_vintage_year` | Int | Year for wine; age-statement integer for spirits |
| `custom_alcohol_content` | Float | ABV % |
| `custom_case_size` | Int | Bottles per wholesale case, default 12 |
| `custom_importer` | Link → Supplier | Importer/distributor linked to Supplier doctype |

**Deploy:** `bench --site <site> import-fixtures --app dt_ecommerce`

---

## Server-Side Context (`utils.py`)

### `extend_dalali_context(context: dict) -> None`

Registered via `update_website_context`. Runs on every website page render.

- Guards: only acts when `doc.doctype == "Website Item"`.
- Reads `custom_case_size` from `tabItem` via `frappe.db.get_value`.
- Writes `context["dalali_item_code"]` and `context["dalali_case_size"]`.
- Purpose: seeds `window.dalali_*` at render time so `dalali.js` has `item_code` and `case_size` without an extra API round-trip on PDP load.

### `dalali_bootstrap_script(context: dict) -> str`

Registered via `jinja.methods`. Available as a Jinja global in any template.

- Returns a `<script>` block string: `window.dalali_item_code = …; window.dalali_case_size = …;`
- Returns `""` when not on an item page (safe no-op).
- Usage in templates: `{{ dalali_bootstrap_script(context) | safe }}`

---

## API Endpoints (`api/wholesale.py`)

All endpoints: `@frappe.whitelist(allow_guest=True)`

### `get_pricing_tiers(item_code: str) → list[dict]`

**Path:** `dt_ecommerce.api.wholesale.get_pricing_tiers`

JOINs `tabPricing Rule` with `tabPricing Rule Item Code`. Returns active, non-expired volume-discount tiers sorted ascending by `min_qty`.

Returned fields per tier:

| Field | Type | Notes |
|---|---|---|
| `min_qty` | int | Minimum quantity for this tier |
| `max_qty` | int/null | Maximum quantity (null = unlimited) |
| `discount_percentage` | float | % off unit price |
| `discount_amount` | float | Fixed amount off unit price |
| `rate` | float | Override rate per unit |
| `price_or_product_discount` | str | "Price" or "Product" |

Filters applied: `pr.disable = 0`, `pr.selling = 1`, valid date range checked.

---

### `get_item_wholesale_meta(item_code: str) → dict`

**Path:** `dt_ecommerce.api.wholesale.get_item_wholesale_meta`

Reads all 8 custom wholesale fields from `tabItem`. Also resolves `custom_importer` (Supplier link) → `supplier_name` and adds it as `custom_importer_name`.

---

### `get_recommended_items(item_code: str, limit: int = 8) → list[dict]`

**Path:** `dt_ecommerce.api.wholesale.get_recommended_items`

Returns published `Website Item` records similar to `item_code`, ordered by relevance score then `ranking DESC`.

**Scoring** (additive):

| Condition | Score |
|---|---|
| Same `item_group` | +4 |
| Same `brand` | +2 |
| Same `custom_region` | +1 |

Candidate items must match at least one condition (OR filter). Current item is always excluded.

Returned fields per item: `item_code`, `web_item_name`, `website_image`, `item_group`, `route`, `brand`, `custom_case_size`, `price`, `currency` — plus computed: `url` (= `/{route}`), `case_size`, `case_price` (= price × case_size).

---

### `get_category_grid(limit: int = 8) → list[dict]`

**Path:** `dt_ecommerce.api.wholesale.get_category_grid`

Returns `Item Group` records where `show_in_website=1` and `is_group=0`, ordered by name.

Each result includes:
- `name`, `route`, `website_image`, `image`
- `image_url` — resolved from `website_image` or `image`
- `url` — `/all-products?item_group=<encoded name>`

---

## Homepage Route (`www/`)

### `www/index.py` — Context Controller

Routes `/` to this controller. `get_context()` builds five template variables:

| Variable | Source | Purpose |
|---|---|---|
| `context.categories` | `frappe.get_all("Item Group", is_group=0, show_in_website=1)` | Filter matrix Type dropdown |
| `context.brands` | `frappe.get_all("Brand")` | Filter matrix Brand dropdown |
| `context.regions` | `frappe.get_all("Liquor Region")` → fallback to `DISTINCT custom_region` | Filter matrix Region dropdown |
| `context.varietals` | `SELECT DISTINCT custom_wine_varietal FROM tabItem` | Filter matrix Varietal dropdown |
| `context.category_grid` | `frappe.get_all("Item Group", show_in_website=1, is_group=0, limit=8)` + image/url enrichment | Category card grid section |
| `context.featured_products` | `frappe.get_all("Website Item", published=1, order_by ranking, limit=8)` + price/case_size enrichment | Featured product cards section |
| `context.wholesale_bundles` | `frappe.get_all("Product Bundle", limit=6)` → filtered to those with a published Website Item; enriched with component count, price, image, url | Curated bundles section; silently yields `[]` on any exception |
| `context.promo_banners` | Raw SQL on `tabPricing Rule`: `selling=1, disable=0, apply_on='Item Group'`, valid date range, `ORDER BY priority DESC, creation DESC LIMIT 4` | Dynamic promo cards; `badge` derived from `discount_percentage` or `discount_amount`; silently yields `[]` on any exception |

`category_grid` enrichment: each group gets `image_url` (from `website_image` or `image`) and `url` (`/catalog?item_group=<quoted name>`).

### `www/index.html` — Homepage Template

Extends `templates/web.html`. A single `<form>` wraps both the hero section and the filter strip so all inputs submit together via GET to `/catalog`.

**Structure:**

```
form.dalali-matrix-form                      (action="/catalog" method="GET")
├── section.dalali-hero-section              (dark background image)
│   └── div.dalali-hero-container            (max-width: 960px, centred)
│       ├── h1.dalali-hero-title
│       ├── p.dalali-hero-sub
│       └── div.dalali-search-row
│           ├── input[name="search"]         aria-label="Search products"
│           └── button.dalali-btn-search
│
└── div.dalali-filter-strip                  (white bar with 3px claret top-border)
    └── div.dalali-filter-strip-inner        (max-width: 1040px, flex row, align: flex-end)
        ├── span.dalali-filter-label         "Filter by:" muted uppercase prefix
        ├── div.dalali-filter-field          (flex-col: label + select)
        │   ├── label.dalali-filter-field-label  "TYPE" (claret, uppercase)
        │   └── select.dalali-select[name="item_group"]    ← context.categories
        ├── div.dalali-filter-field
        │   ├── label.dalali-filter-field-label  "BRAND"
        │   └── select.dalali-select[name="brand"]         ← context.brands
        ├── div.dalali-filter-field
        │   ├── label.dalali-filter-field-label  "REGION"
        │   └── select.dalali-select[name="custom_region"] ← context.regions
        ├── div.dalali-filter-field
        │   ├── label.dalali-filter-field-label  "VARIETAL / STYLE"
        │   └── select.dalali-select[name="custom_varietal"] ← context.varietals
        └── button.dalali-btn-browse         (align-self: flex-end)

section#dalali-category-grid.dalali-category-section    (only if category_grid is non-empty)
└── div.container
    ├── div.dalali-section-header
    │   ├── h2.dalali-section-title          "Shop by Category"
    │   └── a.dalali-section-link            "View all →" → /catalog
    └── div.dalali-category-grid             (4-col grid, 2-col ≤768px, 1-col ≤400px)
        └── (up to 8×) a.dalali-category-card
            ├── img.dalali-category-img      or div.dalali-category-img-placeholder
            └── span.dalali-category-name
```

All form controls carry `aria-label` attributes for accessibility.
The `section#dalali-category-grid` ID doubles as the JS idempotency guard — `injectCategoryGrid()` in `dalali.js` skips injection if this element already exists.

**Why the form wraps both sections:** HTML5 allows `<form>` to be a transparent wrapper around block/sectioning elements. This keeps a single form action so search text + all four filter dropdowns always submit as one GET request regardless of which submit button the user clicks.

```
section#dalali-announcement.dalali-announcement-section  (always rendered)
└── div.container
    ├── div.dalali-promo-banners                         (only if promo_banners is non-empty)
    │   └── (up to 4×) div.dalali-promo-card            (claret gradient; left: badge+title+expiry; right: CTA)
    │       ├── div.dalali-promo-card-left
    │       │   ├── span.dalali-promo-badge              "X% OFF" gold pill
    │       │   ├── h3.dalali-promo-card-title
    │       │   └── p.dalali-promo-expiry
    │       └── div.dalali-promo-card-right
    │           └── a.dalali-promo-card-cta              "Shop Now →" → /catalog
    └── div.dalali-value-strip                           (always shown — 4 value tiles)
        ├── div.dalali-value-item                        📦 Wholesale Pricing
        ├── div.dalali-value-divider
        ├── div.dalali-value-item                        🚚 Fast Delivery
        ├── div.dalali-value-divider
        ├── div.dalali-value-item                        🏷️ Volume Discounts
        ├── div.dalali-value-divider
        └── div.dalali-value-item                        💳 Trade Accounts

section#dalali-products.dalali-products-section          (only if featured_products is non-empty)
└── div.container
    ├── div.dalali-section-header
    │   └── a.dalali-section-link                        "View all →" → /catalog
    └── div.dalali-product-grid
        └── (up to 8×) div.dalali-product-card          (data-item-code, data-case-size, data-price, data-currency)

section#dalali-bundles.dalali-bundles-section            (only if wholesale_bundles is non-empty)
└── div.container
    ├── div.dalali-section-header.dalali-bundles-header
    │   └── a.dalali-section-link.dalali-bundles-link   "View all →" → /catalog
    └── div.dalali-bundle-grid                           (3-col grid)
        └── (up to 6×) article.dalali-bundle-card
            ├── a.dalali-bundle-img-wrap                 (16:9 image + bottom gradient overlay)
            │   ├── img.dalali-bundle-img                or div.dalali-bundle-img-placeholder
            │   └── div.dalali-bundle-img-overlay
            ├── div.dalali-bundle-body
            │   ├── span.dalali-bundle-meta              "N SKUs"
            │   ├── a.dalali-bundle-title
            │   ├── p.dalali-bundle-desc                 2-line clamp
            │   └── div.dalali-bundle-price              "From KES X,XXX"
            └── div.dalali-bundle-footer
                └── a.dalali-bundle-cta                  "View Bundle →"
```

---

## Catalog Page (`www/catalog`)

### Route & URL Parameters

**URL:** `/catalog` — registered automatically by Frappe's `www/` route scanner.

All query parameters are optional and fully combinable:

| Parameter | Type | Description |
|---|---|---|
| `item_group` | string | Filter by Item Group name (uses nested-set lft/rgt for descendants) |
| `custom_region` | string | Origin region / distillery |
| `custom_varietal` | string | Wine varietal or spirit style |
| `custom_vintage` | int | Vintage year |
| `min_price` | float | Minimum bottle price (KES) |
| `max_price` | float | Maximum bottle price (KES) |
| `search` | string | Free-text — matches `web_item_name`, `item_code`, `brand`, `custom_region`, `custom_wine_varietal` |
| `packaging` | `bottle` \| `case` | Informational — stored in context, no DB field yet |
| `show_vol_only` | `1` | Restrict to items with ≥ 1 active Pricing Rule (by item group, `min_qty > 0`) |
| `brands` | string (repeatable) | Multi-value, e.g. `?brands=Jameson&brands=Absolut` |
| `page` | int | Pagination page number (default 1) |

**Page size:** `PAGE_SIZE = 40` (5 columns × 8 rows).

### `catalog.py` — Context Variables

| Variable | Type | Source / Notes |
|---|---|---|
| `context.full_width` | `1` | Removes Bootstrap container from `<main>` |
| `context.no_breadcrumbs` | `1` | Suppresses Frappe's default breadcrumb bar |
| `context.breadcrumb` | `list[dict]` | Custom crumb trail: Home → Portfolio → (parent group) → active group |
| `context.active_group` | `str` | Currently selected Item Group name |
| `context.page_title` | `str` | `active_group` or `"All Products"` |
| `context.top_groups` | `list[dict]` | Direct children of `"Dalali Wholesale Catalog"` with `show_in_website=1`; each has `name`, `item_group_name`, `url` |
| `context.sub_groups` | `list[dict]` | Children of `active_group` with `count` + `url`; if leaf (no children with count > 0) falls back to siblings; if no active_group shows all top_groups |
| `context.all_brands` | `list[dict]` | All `Brand` records ordered by name |
| `context.active_brands` | `list[str]` | Multi-value brands from `?brands=` params |
| `context.active_brand` | `str` | Single brand (from `?brand=`) |
| `context.active_region` | `str` | Active region filter |
| `context.active_varietal` | `str` | Active varietal filter |
| `context.active_vintage` | `str` | Active vintage filter |
| `context.packaging` | `str` | Active packaging radio value |
| `context.show_vol_only` | `bool` | Whether "Volume discount only" checkbox is active |
| `context.search_q` | `str` | Active search query |
| `context.regions` | `list[str]` | DISTINCT `custom_region` values from `tabItem` |
| `context.varietals` | `list[str]` | DISTINCT `custom_wine_varietal` values from `tabItem` |
| `context.vintages` | `list[int]` | DISTINCT `custom_vintage_year` values, DESC |
| `context.price_bound_min` | `int` | MIN price from `tabItem Price` (published items only) |
| `context.price_bound_max` | `int` | MAX price from `tabItem Price` (published items only) |
| `context.min_price` | `int` | Active min price (defaults to `price_bound_min`) |
| `context.max_price` | `int` | Active max price (defaults to `price_bound_max`) |
| `context.items` | `list[dict]` | Product rows (see below) |
| `context.total_count` | `int` | Total matching items (for pagination) |
| `context.page` | `int` | Current page number |
| `context.page_size` | `int` | Always 40 |
| `context.total_pages` | `int` | Ceil of total_count / PAGE_SIZE |
| `context.prev_url` | `str` | Previous page URL (empty if on page 1) |
| `context.next_url` | `str` | Next page URL (empty if on last page) |
| `context.filter_action` | `str` | `"/catalog"` — sidebar form `action` attribute |
| `context.base_params` | `dict` | All active filter params (for JS / clear-filter URLs) |
| `context.clear_search_url` | `str` | URL removing `search` param (empty if no search active) |
| `context.clear_region_url` | `str` | URL removing `custom_region` param |
| `context.clear_varietal_url` | `str` | URL removing `custom_varietal` param |
| `context.clear_vintage_url` | `str` | URL removing `custom_vintage` param |
| `context.clear_brands_url` | `str` | URL removing all `brands` params |

**Item row fields** (each dict in `context.items`):
`item_code`, `web_item_name`, `website_image`, `item_group`, `route`,
`brand`, `custom_case_size`, `custom_region`, `custom_origin_country`,
`custom_wine_varietal`, `custom_alcohol_content`, `custom_vintage_year`,
`price`, `currency` — plus computed: `case_size`, `case_price` (= price × case_size),
`url` (= `/{route}`), `vintage_display` (string or `""`).

**Product SQL** joins `tabWebsite Item` → `tabItem` → `tabItem Group` → `tabItem Price (LEFT)`. Category filter uses nested-set `lft`/`rgt` columns on `tabItem Group` to match all descendants. Free-text matches 5 fields via `LIKE`. Volume-only filter uses `EXISTS` subquery on `tabPricing Rule Item Group`.

**Clear-filter pattern:** `_clear(key)` removes one key from `base_params` and calls `_build_url({"page": ""}, trimmed)` → clean URL with remaining filters but no page offset.

### `catalog.html` — Template Structure

Extends `templates/web.html`. Uses `context.no_breadcrumbs = 1` and renders its own `<nav class="dalali-catalog-breadcrumb">`.

```
nav.dalali-catalog-breadcrumb                          (custom breadcrumb — Frappe default suppressed)
│   ├── a.dalali-crumb                                 "Home" / "Portfolio" / parent group
│   ├── span.dalali-crumb-sep                          "›"
│   └── span.dalali-crumb-current[aria-current=page]  active group or "All Products"

div.dalali-catalog-layout                              (CSS grid: 240px sidebar + 1fr main)
├── aside.dalali-catalog-sidebar                       (position: sticky, max-height: 100vh)
│   │
│   ├── section.dalali-sidebar-section (categories)   — OUTSIDE filter form
│   │   ├── h2.dalali-sidebar-title                    "Portfolio"
│   │   ├── div.dalali-cat-tabs                        top-group pill tabs (incl. "All")
│   │   └── ul.dalali-cat-tree                         sub-group list with count badges
│   │       └── li.dalali-cat-tree-item[.active]
│   │           └── a.dalali-cat-tree-link
│   │               ├── span.dalali-cat-tree-name
│   │               └── span.dalali-cat-tree-count
│   │
│   └── form#dalali-sidebar-form[method=GET]           — wraps sections 2–5
│       ├── input[type=hidden name=item_group]         preserved active group
│       ├── input[type=hidden name=search]             preserved search_q
│       │
│       ├── section.dalali-sidebar-locator             "Find Compatible Stock"
│       │   ├── select#sb-varietal[name=custom_varietal]
│       │   ├── select#sb-region[name=custom_region]
│       │   ├── select#sb-vintage[name=custom_vintage]
│       │   └── button.dalali-locator-btn              "Find Compatible Stock →"
│       │
│       ├── section.dalali-sidebar-packaging           "Packaging"
│       │   ├── radiogroup: All / 🍷 Bottle / 📦 Case  [name=packaging]
│       │   └── checkbox[name=show_vol_only value=1]   "Volume discount only"
│       │
│       ├── section.dalali-sidebar-price               "Price (KES / bottle)"
│       │   ├── div.dalali-price-range-inputs          KES number inputs (min_price / max_price)
│       │   └── div.dalali-range-track                 dual-thumb range slider
│       │       ├── div.dalali-range-fill              absolutely positioned fill bar
│       │       ├── input#dalali-range-min.dalali-range  [tabindex=-1 aria-hidden=true]
│       │       └── input#dalali-range-max.dalali-range  [tabindex=-1 aria-hidden=true]
│       │
│       ├── section.dalali-sidebar-brands              "Brand"
│       │   ├── div.dalali-brand-search-wrap           search icon + input#dalali-brand-search
│       │   └── ul#dalali-brand-list.dalali-brand-list
│       │       └── (N×) li.dalali-brand-item[data-brand=lc-name]
│       │           └── label.dalali-brand-label
│       │               ├── input[type=checkbox name=brands]
│       │               └── span.dalali-brand-name
│       │
│       └── div.dalali-sidebar-actions
│           ├── button[type=submit].dalali-sidebar-apply   "Apply Filters"
│           └── a.dalali-sidebar-clear                     "Clear all filters" (conditional)
│
└── main.dalali-catalog-main
    ├── form.dalali-catalog-search-form[method=GET role=search]
    │   └── div.dalali-catalog-search-row
    │       ├── svg search icon (decorative)
    │       ├── input[type=text name=search].dalali-catalog-search-input
    │       └── button[type=submit].dalali-catalog-search-btn
    │
    ├── div.dalali-result-bar
    │   ├── span.dalali-result-count           "N,NNN products" (or "No products found")
    │   │   └── span.dalali-result-scope       "in Whisky & Scotch" (if active_group)
    │   ├── div.dalali-active-filters          active filter pills (conditional)
    │   │   └── (N×) span.dalali-filter-pill
    │   │       └── a.dalali-pill-remove       links to pre-computed clear_*_url
    │   └── span.dalali-result-page-info       "Page N of M" (if total_pages > 1)
    │
    ├── div.dalali-catalog-grid#dalali-catalog-grid   (5-col grid; 4→3→2 responsive)
    │   └── (up to 40×) article.dalali-cat-card
    │       ├── div.dalali-cat-card-img-wrap           (aspect-ratio: 1/1, relative)
    │       │   ├── a.dalali-cat-card-img-link         → item.url
    │       │   │   └── img.dalali-cat-card-img        or div.dalali-cat-card-img-placeholder
    │       │   ├── button.dalali-wishlist-btn         (position: absolute top-right, circular)
    │       │   │   └── svg.dalali-wishlist-icon       heart outline → filled on .active
    │       │   └── span.dalali-cat-group-pill         (position: absolute bottom-left)
    │       ├── div.dalali-cat-card-body
    │       │   ├── a.dalali-cat-card-name             2-line clamp → item.url
    │       │   ├── div.dalali-cat-card-meta           Brand · Vintage · ABV%
    │       │   └── div.dalali-cat-pricing
    │       │       ├── div.dalali-cat-bottle-price    "KES N,NNN / btl"
    │       │       ├── div.dalali-cat-case-price      "KES N,NNN / case of N"
    │       │       └── button.dalali-cat-price-why    "Why is the price variable?" → openTierModal
    │       └── div.dalali-cat-footer                  (CSS grid: 38px + 1fr)
    │           ├── button.dalali-cat-btn-add          cart icon → add_to_cart
    │           └── a.dalali-cat-btn-buy               "Buy Now" → item.url
    │
    ├── nav.dalali-catalog-pagination                  (only if total_pages > 1)
    │   ├── a.dalali-page-btn[rel=prev]                ← Prev (or span.disabled)
    │   ├── span.dalali-page-current                   "N of M"
    │   └── a.dalali-page-btn[rel=next]                Next → (or span.disabled)
    │
    └── div.dalali-catalog-empty                       (only if items is empty)
        ├── div.dalali-catalog-empty-icon              🔍
        ├── h3.dalali-catalog-empty-title              "No products found"
        ├── p.dalali-catalog-empty-sub
        └── a.dalali-catalog-empty-cta                "Clear all filters"
```

**Dual-thumb price range slider:** Two `<input type="range">` share the same track. The track itself has `pointer-events: none`; only the `::-webkit-slider-thumb` has `pointer-events: all`. A `<div class="dalali-range-fill">` is absolutely positioned and updated by JS as thumbs move. Number inputs (`#dalali-price-min` / `#dalali-price-max`) are the actual form fields; the range inputs are `tabindex="-1" aria-hidden="true"` — keyboard users interact only with the number inputs.

**Filter preservation:** The sidebar form uses `<input type="hidden">` to carry `item_group` and `search_q` across form submits. Active filter pills each link to a pre-computed clear URL (computed in `catalog.py → _clear()`).

---

## Product Detail Page Override (`templates/`)

### `templates/generators/item/item.html`

Shadows `webshop/webshop/templates/generators/item/item.html` via ChoiceLoader priority.

**Changes from the original webshop template:**

1. Added macro import for `product_image` from webshop.
2. Added `dalali-mode` CSS class to the outermost product container `<div>` — used in CSS selectors to hide the webshop's default price block (`.dalali-mode .product-price { display: none }`) and native cart row (`.dalali-mode .item-cart { display: none }`), preventing double UI while Dalali's own blocks are rendered by JS.
3. Added server-side bootstrap script at top of `{% block page_content %}`:

```jinja
{% if dalali_item_code %}
<script>
window.dalali_item_code = {{ dalali_item_code | tojson }};
window.dalali_case_size = {{ dalali_case_size | default(12) | int }};
</script>
{% endif %}
```

This means `dalali.js` can read `window.dalali_item_code` synchronously on DOMContentLoaded without waiting for an API call.

4. Replaced the webshop's 3-column sidebar recommended items section with a full-width `<section id="dalali-pdp-recommended" class="dalali-pdp-recommended-section">` placeholder at the bottom of the page. `initPDPRecommended()` in `dalali.js` populates it asynchronously.

**Page structure:**

```
div.product-container.item-main.dalali-mode
└── div.row
    ├── {% include item_image.html %}         (left column — image gallery)
    └── {% include item_details.html %}       (right column — title, add-to-cart)
        → dalali.js injects above .item-cart:
            #dalali-wholesale-block           (toggle + price + tier link + CTA buttons)
            #dalali-tier-inline               (tier table, if tiers exist)
        → .item-cart hidden via CSS

div.product-container.mt-4                   (specs / tabs / reviews)

section#dalali-pdp-recommended               (JS-populated recommended grid)
```

---

## Frontend JavaScript (`public/js/`)

### `dalali.js` — Wholesale UI (870 lines)

All logic runs inside `frappe.ready()`. Never modifies webshop cart/session state directly.

#### Page detection

| Function | Selector used | Purpose |
|---|---|---|
| `isDalaliItemPage()` | `.item-main`, `[data-variant-item-code]` | True on PDP |
| `isDalaliListingPage()` | `.item-group-content`, `#product-listing` | True on category/listing pages |
| `isDalaliCatalogPage()` | `#dalali-catalog-grid`, `.dalali-catalog-layout` | True on `/catalog` page |

#### Execution flow

```
frappe.ready()
├── injectPromoBar()                  ← every page
├── if isDalaliItemPage()
│   └── initWholesalePDP()
│       ├── getItemCode()             ← reads window.dalali_item_code or DOM attr
│       ├── Promise.all([
│       │   fetchWholesaleMeta(),     ← frappe.call get_item_wholesale_meta
│       │   fetchPricingTiers()       ← frappe.call get_pricing_tiers
│       │ ])
│       ├── injectUnitCaseToggle(itemCode, …)  ← toggle + price + CTA buttons
│       ├── injectWineMeta()
│       └── injectTierTable()         ← only if tiers.length > 0
│       initPDPRecommended()          ← parallel (independent of price data)
│           └── frappe.call get_recommended_items → renders .dalali-rec-grid
├── if isDalaliListingPage()
│   ├── injectHeroSection()
│   ├── injectCategoryGrid()          ← frappe.call get_category_grid
│   └── convertFiltersToHorizontal()
├── if isDalaliCatalogPage()
│   └── initCatalogPage()
│       ├── initPriceRangeSlider()    ← dual-thumb range sync
│       ├── initBrandSearch()         ← live search within brand list
│       ├── initTierInfoButtons()     ← .dalali-cat-price-why click → openTierModal
│       ├── initWishlistButtons()     ← heart toggle + fill attribute
│       └── initCatalogCart()         ← .dalali-cat-btn-add → update_cart
└── if #dalali-products exists
    └── initProductCards()            ← bulk tier fetch for homepage product cards
```

#### Component detail

**`injectPromoBar()`**
- Inserts a `div.dalali-promo-bar` immediately before `header / nav.navbar`.
- Falls back to `document.body.prepend()` if no navbar found.
- Idempotent — checks for existing `.dalali-promo-bar` first.

**`injectUnitCaseToggle(itemCode, bottlePrice, caseSize, tiers)`**
- Hides the webshop's native `.item-cart` row (`style.display = "none"`); Dalali's own block replaces it entirely.
- Inserts `#dalali-wholesale-block` before `.item-cart` containing:
  - Bottle / Case pill toggle
  - Price display (`#dalali-price-display` + `#dalali-price-sub`)
  - Optional "View volume price breaks" tier link
  - **`div.dalali-pdp-cta`** — "Add to Cart" (outlined claret) + "Buy Now" (solid claret) buttons
- Maintains a `currentQty` closure variable (1 for bottle, `caseSize` for case) updated on each toggle click.
- On toggle: updates price display + calls `updateCartQty(currentQty)` (sets native qty input for compatibility).
- CTA buttons call `pdpCartAction(itemCode, currentQty, buyNow, btn)`.

**`pdpCartAction(itemCode, qty, buyNow, btn)`**
- Calls `webshop.webshop.shopping_cart.cart.update_cart` with `{item_code: itemCode, qty}`.
- **Add to Cart path:** shows ✓ "Added!" success state for 1.8 s, then restores original button HTML.
- **Buy Now path:** on success, redirects to `/cart`.
- **Error path:** redirects to `/login?redirect-to=<current path>` (handles unauthenticated users).

**`initPDPRecommended(itemCode)`**
- Calls `dt_ecommerce.api.wholesale.get_recommended_items`.
- If response is empty, sets `section.style.display = "none"`.
- Otherwise renders into `#dalali-pdp-recommended`:
  - `.dalali-section-header` with "You May Also Like" + "View all →" link to `/catalog`
  - `.dalali-rec-grid` — 4-col (→3→2→1) grid of `.dalali-rec-card` articles
- Each card: square image link → card body (group pill + name + bottle price) → "View & Order" CTA footer.

**`calcCasePrice(bottlePrice, caseSize, tiers)`**
- Finds the best (last) applicable tier where `min_qty <= caseSize`.
- Applies `rate`, `discount_percentage`, or `discount_amount` in that priority order.
- Falls back to `bottlePrice × caseSize` (no discount) if no tier applies.

**`injectTierTable(tiers, bottlePrice, caseSize)`**
- Renders `#dalali-tier-inline` after `#dalali-wholesale-block`.
- Columns: Quantity range | Unit price | Saving.
- Best-value tier (last row) gets `.best-value` class + ⭐ badge.

**`openTierModal(tiers, bottlePrice, caseSize)`**
- Appends `.dalali-modal-overlay` to `document.body`.
- Closes on overlay click or ✕ button.

**`injectWineMeta(meta)`**
- Inserts `#dalali-wine-meta` before `.product-description`.
- Renders a 2-column grid for: Category, Varietal/Style, Origin, Region/Distillery, Vintage/Age, ABV%.
- Adds importer badge row if `custom_importer_name` is set.
- Skips render entirely if no fields have values.

**`injectHeroSection()`**
- Inserts `#dalali-hero` before `.item-group-content` on listing pages.
- Search input wired: Enter / button click → `/product/search?q=…`
- Two tabs: "Buy Stock Cases" (stays on page) / "Bulk/Event Inquiry" (→ `/cart`).

**`injectCategoryGrid()`**
- Skips if `#dalali-category-grid` already exists (homepage renders it server-side).
- Skips if `#product-listing` is not present (not a listing page).
- On listing pages: calls `get_category_grid` API, renders a full `section.dalali-category-section` with header row + card grid.
- Inserts after `#dalali-hero` (or before `.item-group-content` if no hero).
- JS-injected version uses `section` element + `.dalali-section-header` to match server-side structure.

**`convertFiltersToHorizontal()`**
- Clones `select` inputs from the webshop sidebar `.filters-section` into a new `#dalali-filter-bar` sticky bar above the product listing.
- Each cloned select mirrors changes back to the original hidden sidebar select and dispatches a `change` event so webshop's filter logic still fires.
- Hides the original sidebar column, expands product column from `col-md-9` to `col-md-12`.

**`initPriceRangeSlider()`**
- Reads `#dalali-range-min` / `#dalali-range-max` slider values and syncs them to `#dalali-price-min` / `#dalali-price-max` number inputs.
- On `input` event: prevents min > max collision; computes fill bar left/right percentages; updates `#dalali-range-fill` inline style.
- Also wires number inputs → range sliders (reverse direction).

**`initBrandSearch()`**
- On `input` event on `#dalali-brand-search`: lower-cases the query and sets `hidden` attribute on `.dalali-brand-item` elements whose `data-brand` attribute doesn't include the query. No API call — all filtering is DOM-only.

**`initTierInfoButtons()`**
- Listens for `click` on `.dalali-cat-price-why` buttons.
- Reads `data-item-code` from the button; calls `frappe.call dt_ecommerce.api.wholesale.get_pricing_tiers`.
- On success: calls `openTierModal(tiers, bottlePrice, caseSize)` using parent card's `data-price` and `data-case-size` attributes.

**`initWishlistButtons()`**
- Listens for `click` on `.dalali-wishlist-btn`.
- Toggles `.active` class on the button; on `.active` sets `fill="currentColor"` on the nested `.dalali-wishlist-icon` SVG and changes `stroke` to `none`; on deactivate restores `fill="none"` and `stroke="currentColor"`.
- No server call — client-side toggle only (wishlist persistence is handled by webshop's own wishlist API separately).

**`initCatalogCart()`**
- Listens for `click` on `.dalali-cat-btn-add` buttons.
- Reads `data-item-code`; calls `webshop.webshop.shopping_cart.cart.update_cart` with `{item_code, qty: 1}`.
- Shows brief `.dalali-cart-feedback` tooltip on success.

---

### `theme.js` — Navbar + Search Typeahead (pre-existing)

| Feature | Notes |
|---|---|
| Navbar scroll effect | Adds `.dt-navbar-scrolled` class after 10px scroll |
| Mobile menu toggle | `.dt-menu-trigger` click toggles `.open` on `.dt-main-menu` |
| Search typeahead | Calls `webshop.templates.pages.product_search.search` with 300ms debounce |
| Recent searches | Stored in `localStorage["recent_searches"]` (max 4 entries) |
| Search click tracking | POSTs to `dt_recomendations.api.log_search_click` (fire-and-forget) |
| Wishlist count | `webshop.webshop.wishlist.set_wishlist_count()` via `frappe.ready()` |

---

## CSS / Brand Theme (`public/css/`)

### Brand Palette (`theme_dalali.css` `:root`)

| Variable | Value | Usage |
|---|---|---|
| `--dalali-claret` | `#7B1D2B` | Primary buttons, active states |
| `--dalali-claret-d` | `#5C1520` | Hover state for claret buttons |
| `--dalali-gold` | `#B8902A` | Accent, CTAs, best-value highlights |
| `--dalali-gold-l` | `#D4AA45` | Hover state for gold buttons |
| `--dalali-ink` | `#1A0C0F` | Dark navbar, hero overlay, footer |
| `--dalali-ivory` | `#FBF7F2` | Background, body text on dark |
| `--dalali-warm` | `#2E1E22` | Body text colour |
| `--dalali-muted` | `#8A7A7E` | Labels, secondary text |
| `--dalali-border` | `#E8DDD5` | Borders, dividers |
| `--dalali-surface` | `#FFFFFF` | Card backgrounds |

These override the generic theme variables: `--color-primary`, `--color-background`, `--color-text`, `--color-accent`, `--surface-base`.

### CSS Component Map

| Section | Key classes | Notes |
|---|---|---|
| Promo bar | `.dalali-promo-bar`, `.dalali-promo-inner`, `.dalali-promo-center`, `.dalali-promo-right` | Sticky above navbar; right column hidden on mobile |
| Dark navbar | `.dt-navbar` | `background: rgba(26,12,15,0.96)` |
| Hero | `.dalali-hero-section`, `.dalali-hero-container`, `.dalali-hero-title`, `.dalali-hero-sub` | Full-bleed dark background image (`background-color` + `background-image` sub-properties); min-height 480px; contains title, sub-heading, and search bar only |
| Search bar | `.dalali-search-row`, `.dalali-search-input`, `.dalali-btn-search` | Glass-style search row inside hero (white/8% bg, ivory text) |
| Filter strip | `.dalali-filter-strip`, `.dalali-filter-strip-inner` | White bar below hero; 3px claret `border-top` anchors it visually; `box-shadow`; max-width 1040px; flex row `align-items: flex-end` |
| Filter labels | `.dalali-filter-label`, `.dalali-filter-field`, `.dalali-filter-field-label` | Each select wrapped in a flex-col field div; claret uppercase label above select; "Filter by:" muted prefix |
| Filter selects | `.dalali-select` (base), `.dalali-filter-strip .dalali-select` (override) | Base: ivory-on-dark glass (listing-page hero); strip override: ivory bg, claret chevron SVG (explicit sub-properties — no shorthand), claret focus ring (`box-shadow: 0 0 0 3px rgba(123,29,43,0.12)`) |
| Browse button | `.dalali-btn-browse`, `.dalali-filter-strip .dalali-btn-browse` | Gold base; strip override: `align-self: flex-end` to sit flush with select bottoms |
| Unit toggle | `.dalali-unit-toggle`, `.dalali-toggle-btn`, `.dalali-toggle-btn.active` | Pill-style bottle/case switcher |
| Price block | `.dalali-price-block`, `.dalali-price-main`, `.dalali-price-sub`, `.dalali-tier-link` | Large price display with optional tier link |
| Tier table | `.dalali-tier-table`, `.dalali-tier-row`, `.dalali-tier-row.best-value`, `.dalali-tier-discount` | Inline volume discount table; best row highlighted in gold |
| Tier modal | `.dalali-modal-overlay`, `.dalali-modal`, `.dalali-modal-header`, `.dalali-modal-title`, `.dalali-modal-close` | Centered overlay modal |
| Wine metadata | `.dalali-meta-grid`, `.dalali-meta-item`, `.dalali-meta-label`, `.dalali-meta-value`, `.dalali-importer-badge` | 2-column responsive grid |
| Category section | `.dalali-category-section`, `.dalali-section-header`, `.dalali-section-title`, `.dalali-section-link` | Section wrapper with heading row + animated "View all →" arrow link |
| Category grid | `.dalali-category-grid`, `.dalali-category-card`, `.dalali-category-img`, `.dalali-category-img-placeholder`, `.dalali-category-name` | 4-col (gap 20px); 3-col ≤900px; 2-col ≤600px; 1-col ≤360px. Card: white bg, 12px radius, border, overflow hidden. Image: `width:100%; aspect-ratio:4/3; object-fit:cover`; scales 1.05× on hover. Placeholder: ink→claret→gold gradient, same aspect ratio. Name: footer strip with `border-top`, turns claret on hover. Card lifts on hover (`translateY(-4px)` + shadow) |
| Announcement section | `.dalali-announcement-section` | Ivory background, placed between category grid and featured products |
| Promo banner cards | `.dalali-promo-banners`, `.dalali-promo-card`, `.dalali-promo-badge`, `.dalali-promo-card-title`, `.dalali-promo-expiry`, `.dalali-promo-card-cta` | Claret→dark-claret gradient card; gold badge pill; ivory CTA turns gold on hover; hidden when `promo_banners` is empty |
| Value strip | `.dalali-value-strip`, `.dalali-value-item`, `.dalali-value-divider`, `.dalali-value-icon`, `.dalali-value-body`, `.dalali-value-title`, `.dalali-value-desc` | White rounded card, 4 tiles with `1px` dividers; 4→2×2 (≤860px)→1-col (≤480px); dividers hidden on mobile, replaced by `border-bottom` on items |
| Bundles section | `.dalali-bundles-section`, `.dalali-bundle-grid`, `.dalali-bundle-card` | Dark `var(--dalali-ink)` section; 3-col (→2→1); card: `var(--dalali-warm)` bg, subtle gold border brightens on hover, `translateY(-4px)` lift |
| Bundle card image | `.dalali-bundle-img-wrap`, `.dalali-bundle-img`, `.dalali-bundle-img-placeholder`, `.dalali-bundle-img-overlay` | 16:9 aspect ratio; image scales 1.06× on hover; placeholder: deep claret gradient; overlay: bottom-fade gradient |
| Bundle card body | `.dalali-bundle-meta`, `.dalali-bundle-title`, `.dalali-bundle-desc`, `.dalali-bundle-price`, `.dalali-bundle-price-label`, `.dalali-bundle-price-amount` | Meta: gold uppercase "N SKUs"; title: ivory, turns gold-light on hover; desc: 2-line `-webkit-line-clamp`; price: gold amount |
| Bundle CTA | `.dalali-bundle-cta` | Full-width ivory ghost button; hover: gold fill + ink text + arrow slides right |
| Horizontal filters | `.dalali-filter-bar`, `.dalali-filter-inner`, `.dalali-filter-select`, `.dalali-filter-browse-btn` | Sticky top filter strip |
| PDP CTA buttons | `.dalali-pdp-cta`, `.dalali-pdp-add-btn`, `.dalali-pdp-buy-btn`, `.dalali-pdp-add-btn.added` | Flex row below price block. Add to Cart: outlined claret → fills on hover; turns green on `.added`. Buy Now: solid claret; arrow slides right on hover. Both `flex: 1` to share available width |
| Webshop suppression | `.dalali-mode .product-price`, `.dalali-mode .item-cart` | Both `display: none !important` — prevents double price display and double cart row |
| PDP recommended section | `.dalali-pdp-recommended-section` | Ivory bg, `border-top: 1px solid var(--dalali-border)`, `padding: 56px 0 64px`, `margin-top: 48px` |
| Recommended grid | `.dalali-rec-grid` | `repeat(4, 1fr)` → 3-col ≤1024px → 2-col ≤768px → 1-col ≤420px; `gap: 18px` |
| Recommended card | `.dalali-rec-card`, `.dalali-rec-card-img-wrap`, `.dalali-rec-card-img` | White card, 10px radius, border, hover `translateY(-4px)` + shadow. Image: `aspect-ratio: 1/1`, `object-fit: cover`, scales 1.04× on card hover |
| Recommended card body | `.dalali-rec-card-body`, `.dalali-rec-card-group`, `.dalali-rec-card-name`, `.dalali-rec-card-price` | Group: 0.68rem muted uppercase. Name: 2-line `-webkit-line-clamp`, turns claret on hover. Price: 0.95rem bold ink |
| Recommended card CTA | `.dalali-rec-card-footer`, `.dalali-rec-card-cta` | Full-width solid claret button, darkens on hover |
| Catalog breadcrumb | `.dalali-catalog-breadcrumb`, `.dalali-crumb`, `.dalali-crumb-current`, `.dalali-crumb-sep` | Custom breadcrumb above catalog layout; replaces Frappe default |
| Catalog layout | `.dalali-catalog-layout` | `display: grid; grid-template-columns: 240px 1fr; align-items: start; max-width: 1440px; margin: 0 auto` |
| Catalog sidebar | `.dalali-catalog-sidebar` | `position: sticky; top: 0; max-height: 100vh; overflow-y: auto`; collapses to `position: static` on mobile |
| Sidebar sections | `.dalali-sidebar-section`, `.dalali-sidebar-title` | White bg, `border-bottom: 1px solid var(--dalali-border)`, `padding: 16px` |
| Category tabs | `.dalali-cat-tabs`, `.dalali-cat-tab`, `.dalali-cat-tab.active` | Pill tabs; active: claret bg + ivory text |
| Category tree | `.dalali-cat-tree`, `.dalali-cat-tree-item`, `.dalali-cat-tree-item.active`, `.dalali-cat-tree-link`, `.dalali-cat-tree-name`, `.dalali-cat-tree-count` | List with inline count badge; active item: claret left border + claret text |
| Profile locator | `.dalali-locator-fields`, `.dalali-locator-field`, `.dalali-locator-label`, `.dalali-sidebar-select`, `.dalali-locator-btn` | 3 stacked selects + CTA button (full-width, claret) |
| Packaging radios | `.dalali-radio-group`, `.dalali-radio-item`, `.dalali-radio-label`, `.dalali-checkbox-item`, `.dalali-checkbox-label` | Inline radio group + checkbox item |
| Price range slider | `.dalali-price-range-inputs`, `.dalali-price-input-wrap`, `.dalali-price-prefix`, `.dalali-price-number`, `.dalali-range-track`, `.dalali-range-fill`, `.dalali-range` | Dual-thumb overlay slider; track `pointer-events: none`; `::-webkit-slider-thumb pointer-events: all`; fill bar absolutely positioned |
| Brand directory | `.dalali-brand-search-wrap`, `.dalali-brand-search-icon`, `.dalali-brand-search`, `.dalali-brand-list`, `.dalali-brand-item`, `.dalali-brand-label`, `.dalali-brand-name` | Brand search input above scrollable (`max-height: 180px`) checkbox list |
| Sidebar actions | `.dalali-sidebar-actions`, `.dalali-sidebar-apply`, `.dalali-sidebar-clear` | Apply button (claret, full-width) + "Clear all filters" muted link |
| Catalog search bar | `.dalali-catalog-search-form`, `.dalali-catalog-search-row`, `.dalali-catalog-search-icon`, `.dalali-catalog-search-input`, `.dalali-catalog-search-btn` | Main-area search bar with icon, border, claret Submit button |
| Result bar | `.dalali-result-bar`, `.dalali-result-count`, `.dalali-result-scope`, `.dalali-result-page-info` | Flex row: count on left, page info on right |
| Filter pills | `.dalali-active-filters`, `.dalali-filter-pill`, `.dalali-pill-remove` | Claret/gold pill tags with ✕ remove link; each links to pre-computed clear URL |
| Catalog grid | `.dalali-catalog-grid` | `display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px`; 4-col ≤1400px; 3-col ≤1024px; 2-col ≤600px |
| Catalog card | `.dalali-cat-card` | White card, `border-radius: 10px`, border, hover `translateY(-4px)` + shadow; `display: flex; flex-direction: column` |
| Card image | `.dalali-cat-card-img-wrap`, `.dalali-cat-card-img-link`, `.dalali-cat-card-img`, `.dalali-cat-card-img-placeholder` | `aspect-ratio: 1/1` square; image `object-fit: cover` scales 1.04× on hover; placeholder: ink→claret gradient |
| Wishlist button | `.dalali-wishlist-btn`, `.dalali-wishlist-btn.active`, `.dalali-wishlist-icon` | `position: absolute; top: 7px; right: 7px; width: 30px; height: 30px; border-radius: 50%`; white bg; claret on `.active` |
| Category pill | `.dalali-cat-group-pill` | `position: absolute; bottom: 6px; left: 6px`; ivory bg / claret text; `0.65rem` uppercase |
| Card body | `.dalali-cat-card-body`, `.dalali-cat-card-name`, `.dalali-cat-card-meta` | Name: 2-line clamp, turns claret on hover. Meta: 3 inline spans (brand · vintage · ABV%) separated by `·` |
| Card pricing | `.dalali-cat-pricing`, `.dalali-cat-bottle-price`, `.dalali-cat-case-price`, `.dalali-cat-price-why`, `.dalali-price-na` | Bottle price bold ink; case price muted smaller; "Why variable?" in claret micro-link style |
| Card CTA footer | `.dalali-cat-footer`, `.dalali-cat-btn-add`, `.dalali-cat-btn-buy` | `display: grid; grid-template-columns: 38px 1fr`. Add icon: outlined cart, claret border. Buy Now: solid claret fill, ivory text |
| Catalog pagination | `.dalali-catalog-pagination`, `.dalali-page-btn`, `.dalali-page-btn.disabled`, `.dalali-page-current` | Centered flex row; active buttons: claret outline; disabled: muted, `cursor: default` |
| Catalog empty state | `.dalali-catalog-empty`, `.dalali-catalog-empty-icon`, `.dalali-catalog-empty-title`, `.dalali-catalog-empty-sub`, `.dalali-catalog-empty-cta` | Centred column; large 🔍 emoji; claret CTA link |

---

## Seed Data & Utilities

All utilities live in `dt_ecommerce/` (same level as `hooks.py`) and are run via `bench execute`.

### `restructure_groups.py` — Item Group Tree

```bash
bench --site erpnext.localhost execute dt_ecommerce.restructure_groups.run
```

Creates a clean two-branch Item Group hierarchy:

- **`Dalali Wholesale Catalog`** (parent for all customer-facing groups)
  - Whisky & Scotch
  - Red Wine
  - White Wine
  - Champagne & Sparkling
  - Beer & Cider
  - Gin & Vodka
  - Brandy & Cognac
  - Rum & Tequila

- **`Internal Operations`** (parent for non-web groups)
  - Products, Raw Material, Services, Sub Assemblies, Consumable, Fixed Assets, Furniture and Fixtures

**Why:** The catalog guard (`catalog_guard.py`) uses the nested-set subtree of `"Internal Operations"` to block accidental publishing. Run this once before seeding items.

---

### `seed.py` — Items, Prices, Website Items, Product Bundles

```bash
bench --site erpnext.localhost execute dt_ecommerce.seed.run
```

Creates (or skips if already exists):
1. **12 Item records** with wholesale fields populated (brand, case_size, varietal, region, ABV, vintage).
2. **Item Price** records (Standard Selling price list, KES).
3. **Website Item** records (published, with web_item_name and route).
4. **3 Product Bundle** records (whisky sampler, premium wine selection, party pack).
5. **Images**: Downloads 26 JPEGs from Unsplash into `sites/<site>/public/files/` — skips files that already exist.

**Key constants:**
- `CATALOG_PARENT = "Dalali Wholesale Catalog"` — all seeded items go into this tree
- `PAGE_SIZE` — not used here; items are individually assigned to child groups
- `IMGS` dict — maps `filename → (unsplash_photo_id, width_px)` for 26 images

---

### `seed_campaigns.py` — Campaigns + Pricing Rules

```bash
bench --site erpnext.localhost execute dt_ecommerce.seed_campaigns.run
```

Seeds **6 Campaign records** and **~10 Pricing Rules** for the homepage promotional banner strip.

Each rule has:
- `apply_on = "Item Group"` (required for `index.py` promo_banners query)
- `selling = 1`, `disable = 0`
- Valid date window (`valid_from` / `valid_upto`)
- `min_qty` threshold for volume-discount rules
- `priority` ordering

**Sample campaigns:** Whisky Season Sale (20% off), Summer Wine Promotion (15% off), Case Deal of the Week (buy 5 cases, save KES 2,000), etc.

---

### `fix_images.py` — Direct DB Image Path Patch

```bash
bench --site erpnext.localhost execute dt_ecommerce.fix_images.run
```

Writes `website_image` directly to `tabWebsite Item` and `tabItem Group` via `frappe.db.set_value`, bypassing the normal Attach Image field validation (which requires a matching `tabFile` record). Useful after `seed.py` runs but before images are registered in the File doctype.

**`PRODUCT_IMAGES` dict:** maps `item_code → "/files/dalali-prod-*.jpg"` for 12 SKUs + 3 bundles.
**`GROUP_IMAGES` dict:** maps `item_group_name → "/files/dalali-cat-*.jpg"` for 8 categories.

---

### `catalog_guard.py` — Webshop Publication Guard

```python
# Registered automatically via hooks.py:
doc_events = {
    "Website Item": {
        "validate": "dt_ecommerce.catalog_guard.block_internal_publish",
    }
}
```

**`block_internal_publish(doc, method=None)`** fires on every `Website Item` save:

1. Skips if `doc.published == 0` (unpublishing is always allowed).
2. Reads `item_group` from the linked `Item` record.
3. Builds the set of all descendant group names under `"Internal Operations"` using the nested-set `lft`/`rgt` subtree walk.
4. **Throws `ValidationError`** if the item's group is in the internal subtree.
5. **Throws `ValidationError`** if the item's group has `show_in_website = 0`.

Error title: `"Webshop Publication Blocked"`. The error message names the item code, the offending group, and suggests the fix.

---

### `DALALI_DATA_GUIDE.md`

Companion document at the repo root covering:
- Correct bench execute commands for all utilities
- Expected Item Group tree structure after `restructure_groups`
- Expected item and bundle records after `seed`
- How to add new products (Item → custom fields → Website Item → fix_images if needed)
- How to add new campaigns / promotions
- Common issues and fixes (image not showing, catalog guard errors, pricing rule not appearing)

---

## Webshop — What Was Touched

**Nothing in `apps/webshop/` was modified.** Every change is applied as an overlay:

| Mechanism | How Dalali uses it |
|---|---|
| ChoiceLoader template override | `dt_ecommerce/templates/generators/item/item.html` shadows the webshop version |
| `update_website_context` | Adds `dalali_item_code` + `dalali_case_size` to webshop's own page context dict |
| `web_include_css/js` | CSS/JS appended to every page the webshop renders |
| `@frappe.whitelist` API | New endpoints in `dt_ecommerce.api.wholesale` — webshop API files untouched |
| Cart qty interaction | `dalali.js` sets `.value` on the existing native qty `<input>` + dispatches `change`; does not replace cart logic |

Webshop cart, checkout, wishlist, order history, and review flows are fully intact.

---

## Deployment Steps

```bash
# 1. Install the app on a site (first time only)
bench --site erpnext.localhost install-app dt_ecommerce

# 2. Deploy custom fields from fixtures
bench --site erpnext.localhost import-fixtures --app dt_ecommerce

# 3. Run migrations (if any patches added)
bench --site erpnext.localhost migrate

# 4. Build frontend assets
bench build --app dt_ecommerce

# 5. Clear cache
bench --site erpnext.localhost clear-cache

# 6. Restart services (if hooks.py changed)
bench restart
```

> After any change to `hooks.py`, always restart bench — hooks are loaded at startup.
> After any change to `.css` or `.js` files in `public/`, always run `bench build --app dt_ecommerce`.

---

## Changelog

### 2026-05-29 — PDP CTA Buttons + Recommended Items (v1.3)

**`api/wholesale.py`** (MODIFIED)
- Added `get_recommended_items(item_code, limit=8)` — returns up to 8 published items scored by relevance (+4 same group, +2 same brand, +1 same region), ordered by score DESC then `ranking DESC`. Returns `item_code`, `web_item_name`, `website_image`, `item_group`, `route`, `brand`, `custom_case_size`, `price`, `currency`, `url`, `case_size`, `case_price`.

**`templates/generators/item/item.html`** (MODIFIED)
- Replaced webshop's 3-column sidebar recommended layout with a full-width `<section id="dalali-pdp-recommended" class="dalali-pdp-recommended-section">` placeholder at the bottom.
- Reviews, specs, and website content remain in the main container above it.

**`public/js/dalali.js`** (MODIFIED)
- `injectUnitCaseToggle` signature changed: now takes `itemCode` as first argument. Hides `.item-cart` natively; tracks `currentQty` (1 or caseSize) as a closure variable. Appends `div.dalali-pdp-cta` containing "Add to Cart" (outlined claret) and "Buy Now" (solid claret) buttons inside `#dalali-wholesale-block`.
- Added `pdpCartAction(itemCode, qty, buyNow, btn)` — calls `update_cart`, shows ✓ "Added!" feedback on add, redirects to `/cart` on buy now, redirects to login on error.
- Added `initPDPRecommended(itemCode)` — called from `initWholesalePDP()` independently of the price/tier promise chain. Fetches `get_recommended_items`, renders a 4-col `.dalali-rec-grid` into `#dalali-pdp-recommended`.
- `initWholesalePDP()` updated to call `initPDPRecommended(itemCode)` in parallel (outside `Promise.all`).

**`public/css/theme_dalali.css`** (MODIFIED)
- Added `.dalali-mode .item-cart { display: none !important }` — native webshop cart row suppressed.
- Added `.dalali-pdp-cta`, `.dalali-pdp-add-btn`, `.dalali-pdp-buy-btn`, `.dalali-pdp-add-btn.added` — PDP CTA pair.
- Added `.dalali-pdp-recommended-section`, `.dalali-rec-grid`, `.dalali-rec-card`, `.dalali-rec-card-img-wrap`, `.dalali-rec-card-img`, `.dalali-rec-card-body`, `.dalali-rec-card-group`, `.dalali-rec-card-name`, `.dalali-rec-card-price`, `.dalali-rec-card-footer`, `.dalali-rec-card-cta` — full recommended grid CSS.

**`hooks.py`** (MODIFIED)
- `_V` bumped to `"?v=1.3"` for CSS/JS cache busting.

---

### 2026-05-27 — Catalog Page + Cache Busting (v1.2)

**`www/catalog.py`** (NEW)
- Full B2B listing page context controller at route `/catalog`.
- Reads 11 query params: `item_group`, `custom_region`, `custom_varietal`, `custom_vintage`, `min_price`, `max_price`, `search`, `packaging`, `show_vol_only`, `brands` (multi-value), `page`.
- Category tree: top-level groups from `"Dalali Wholesale Catalog"` parent; sub-groups with `_count()` badges; leaf-node sibling pivot.
- Product SQL: JOIN across `tabWebsite Item` + `tabItem` + `tabItem Group` + `tabItem Price`. Nested-set lft/rgt for descendant category filtering. Volume-only `EXISTS` subquery. `PAGE_SIZE = 40`.
- Price slider bounds from MIN/MAX of published `tabItem Price`.
- Clear-filter URL pattern: `_clear(key)` removes one param from `base_params`, calls `_build_url()`.
- Pre-computed `context.clear_*_url` for each filter type; `context.base_params` exposed to template.

**`www/catalog.html`** (NEW)
- Extends `templates/web.html`. Custom breadcrumb (`no_breadcrumbs=1`).
- Two-pane layout: 240px sticky sidebar + 1fr main (`dalali-catalog-layout`).
- Sidebar: category tabs + sub-group tree (outside form) + sidebar form with 5 sections (profile locator, packaging radios + vol-only checkbox, dual-thumb price range, brand directory).
- Main: inline search form; result bar with active filter pills; 5-col product grid (`dalali-catalog-grid`); pagination; empty state.
- Each `article.dalali-cat-card`: square image + wishlist heart + category pill + card body (name + meta + pricing) + split CTA footer (cart icon + "Buy Now").

**`www/index.py`** (MODIFIED)
- Changed `category_grid` URL from `/webshop?item_group=…` → `/catalog?item_group=…`.
- Changed `promo_banners` SQL: removed `campaign IS NOT NULL` filter; now uses `apply_on = 'Item Group'` + `ORDER BY priority DESC` + `LIMIT 4`.

**`www/index.html`** (MODIFIED)
- Changed form `action` from `/webshop` → `/catalog`.
- All "View all →" links updated to `/catalog`.
- Promo banner CTA links updated to `/catalog`.

**`public/css/theme_dalali.css`** (MODIFIED)
- ~500 lines appended: full catalog page CSS component set (breadcrumb, layout grid, sidebar, category tree, profile locator, packaging radios, dual-thumb price slider, brand directory, sidebar actions, search bar, result bar, filter pills, 5-col product grid, product card, wishlist button, category pill, pricing block, split CTA footer, pagination, empty state).

**`public/js/dalali.js`** (MODIFIED)
- Added `isDalaliCatalogPage()` detection function.
- Added `initCatalogPage()` and five sub-functions: `initPriceRangeSlider()`, `initBrandSearch()`, `initTierInfoButtons()`, `initWishlistButtons()`, `initCatalogCart()`.
- Updated `frappe.ready()` execution flow to call `initCatalogPage()` on catalog pages.
- Changed `/webshop` → `/catalog` in `injectCategoryGrid()` "View all" link.

**`hooks.py`** (MODIFIED)
- Added `_V = "?v=1.2"` version string appended to all `web_include_css` / `web_include_js` paths.
- Browser-side cache bust: treats `theme_dalali.css?v=1.2` as a new URL; Werkzeug ignores the query string and serves the same physical file.
- **Root cause fixed:** Frappe's Werkzeug dev server serves static CSS/JS with `Cache-Control: max-age=43200` (12 h). Without a version string in the URL, browsers would cache files for 12 hours after any change.

---

### 2026-05-27 — Seed Data & Catalog Guard (v1.0 / v1.1)

**`restructure_groups.py`** (NEW)
- Builds clean two-branch `Item Group` tree: `"Dalali Wholesale Catalog"` (8 customer-facing sub-groups) + `"Internal Operations"` (6 internal groups).
- Sets `show_in_website=1` on catalog groups, `show_in_website=0` on internal groups.

**`seed.py`** (NEW)
- Creates 12 Item records (whisky, wine, beer, spirits) with all `custom_dalali_*` fields populated.
- Creates `Item Price`, `Website Item` (published), and 3 `Product Bundle` records.
- Downloads 26 Unsplash images into `sites/<site>/public/files/` (skips existing).

**`seed_campaigns.py`** (NEW)
- Creates 6 Campaign records and ~10 `Pricing Rule` records for the homepage promo banner strip.
- All rules: `apply_on = 'Item Group'`, `selling=1`, `disable=0`, valid date window, `priority` ordering.

**`fix_images.py`** (NEW)
- Bypasses Frappe's Attach field validation using `frappe.db.set_value` to write `website_image` paths directly on `Website Item` and `Item Group` records.
- Maps 12 SKUs + 3 bundles + 8 category groups to their Unsplash image paths.

**`catalog_guard.py`** (NEW)
- `block_internal_publish(doc, method)` hook fires on `Website Item.validate`.
- Throws `ValidationError` if item's group is in the nested-set subtree of `"Internal Operations"` or has `show_in_website=0`.
- Registered via `hooks.py doc_events`.

**`DALALI_DATA_GUIDE.md`** (NEW)
- Companion operational guide: bench execute commands, expected data shapes, how to add products/campaigns, common errors.

---

### 2026-05-26 — Promotional Banner / Announcement Strip (v0.10)

**`www/index.py`**
- Added `context.promo_banners` block (wrapped in `try/except` — silently yields `[]`).
- Raw SQL on `tabPricing Rule`: `selling=1`, `disable=0`, `campaign IS NOT NULL AND != ''`, valid date window (`valid_from ≤ TODAY ≤ valid_upto`), `ORDER BY creation DESC LIMIT 3`.
- Each dict: `title` (from `pr.title` or `pr.campaign`), `campaign`, `badge` (derived: `"X% OFF"` from `discount_percentage`, `"KES X,XXX OFF"` from `discount_amount`), `valid_upto` (stringified).

**`www/index.html`**
- Added `section#dalali-announcement.dalali-announcement-section` between the category grid `{% endif %}` and the featured products section.
- Section **always renders** (not conditional) so the value strip is always visible.
- `div.dalali-promo-banners` is conditionally rendered `{% if promo_banners %}` — hidden when no active campaigns in DB.
- Each `div.dalali-promo-card`: left column (badge + title + expiry) + right column ("Shop Now →" CTA).
- `div.dalali-value-strip` always shown — 4 benefit tiles with `div.dalali-value-divider` separators:
  - 📦 Wholesale Pricing — competitive case rates from 5+ cases
  - 🚚 Fast Delivery — Nairobi same-day on orders above 10 cases
  - 🏷️ Volume Discounts — tiered pricing unlocks automatically at checkout
  - 💳 Trade Accounts — 30-day credit terms for verified businesses

**`theme_dalali.css`**
- `.dalali-announcement-section`: ivory background, `padding: 0 0 56px`.
- `.dalali-promo-banners`: flex column, `gap: 12px`, `margin-bottom: 40px`.
- `.dalali-promo-card`: `background: linear-gradient(100deg, var(--dalali-claret) 0%, #3B0A14 100%)`; flex row space-between; `border-radius: 12px`; `padding: 24px 32px`.
- `.dalali-promo-badge`: gold bg, ink text, `0.72rem` bold uppercase pill.
- `.dalali-promo-card-cta`: ivory bg / claret text; hover: gold bg / ink text + arrow slides right.
- `.dalali-value-strip`: white card, `border: 1px solid var(--dalali-border)`, `border-radius: 12px`, `overflow: hidden`; flex row, 4 items.
- `.dalali-value-divider`: `width: 1px`, `background: var(--dalali-border)`, `align-self: stretch`.
- Responsive `@media (max-width: 860px)`: wrap to 2×2, `border-bottom` replaces dividers. `@media (max-width: 480px)`: full-stack.

---

### 2026-05-26 — Curated Wholesale Bundles Section (v0.9)

**`www/index.py`**
- Added `context.wholesale_bundles` block (wrapped in `try/except Exception` — silently yields `[]` if `Product Bundle` table is empty or schema differs).
- Queries `frappe.get_all("Product Bundle", fields=["name","new_item_code","description"], limit=6)`.
- For each record: looks up a published `Website Item` for `new_item_code` — skips bundles with no published web page.
- Enriches each bundle dict: `title` (from `web_item_name`), `image` (from `website_image`), `url`, `description` (truncated to 120 chars), `item_count` (`frappe.db.count("Product Bundle Item")`), `price` + `currency` (from `Item Price`, selling=1).

**`www/index.html`**
- Added `section#dalali-bundles.dalali-bundles-section` after the featured products section, guarded by `{% if wholesale_bundles %}`.
- Each `article.dalali-bundle-card` contains:
  - `a.dalali-bundle-img-wrap` → `img.dalali-bundle-img` (16:9) or `div.dalali-bundle-img-placeholder` (🎁) + `div.dalali-bundle-img-overlay` (bottom gradient).
  - `div.dalali-bundle-body` → `span.dalali-bundle-meta` ("N SKUs"), `a.dalali-bundle-title`, `p.dalali-bundle-desc`, `div.dalali-bundle-price` ("From KES X,XXX").
  - `div.dalali-bundle-footer` → `a.dalali-bundle-cta` ("View Bundle →" with animated SVG arrow).

**`theme_dalali.css`**
- Added `.dalali-bundles-section`: `background: var(--dalali-ink)`, `padding: 64px 0 72px`.
- Added `.dalali-bundles-title` / `.dalali-bundles-link` overrides for ivory/gold text on dark background.
- Added `.dalali-bundle-grid`: 3-col, `gap: 24px`; →2-col (≤900px); →1-col (≤540px).
- `.dalali-bundle-card`: `background: var(--dalali-warm)`, gold `border: 1px solid rgba(184,144,42,0.25)` brightening to `var(--dalali-gold)` on hover; `translateY(-4px)` + shadow lift.
- `.dalali-bundle-img`: `aspect-ratio: 16/9`, scales 1.06× on hover. `.dalali-bundle-img-placeholder`: deep ink→claret gradient.
- `.dalali-bundle-img-overlay`: absolute bottom-fade (`linear-gradient(to top, rgba(13,5,8,0.55), transparent)`).
- `.dalali-bundle-meta`: gold, uppercase, `0.72rem`. `.dalali-bundle-title`: ivory, turns `--dalali-gold-l` on hover. `.dalali-bundle-desc`: muted ivory, 2-line `-webkit-line-clamp`. `.dalali-bundle-price-amount`: gold, `1.15rem` bold.
- `.dalali-bundle-cta`: full-width ghost button (ivory border/text); hover: fills gold, text becomes ink, arrow slides right.

---

### 2026-05-26 — Category Grid Redesign: Spaced Cards + Image-Dominant Layout (v0.8)

**`theme_dalali.css`**
- `.dalali-category-grid`: removed the 1px-gap border-table trick (`gap:1px; background:border-colour; overflow:hidden`). Now uses `gap: 20px` with individual card borders.
- Grid breakpoints changed: 4-col (default) → 3-col (≤900px, gap 16px) → 2-col (≤600px, gap 12px) → 1-col (≤360px).
- `.dalali-category-card`: removed `padding`, `align-items: center`, `gap`, `min-height`. Now `overflow: hidden` on the card (not the grid) to clip the image to the border-radius. Added `border: 1px solid var(--dalali-border)`. Hover: `translateY(-4px)` + shadow instead of claret background flip.
- `.dalali-category-img`: removed `72px × 72px` fixed size. Now `width: 100%; aspect-ratio: 4/3; object-fit: cover; display: block`. Scales `1.05×` on card hover via `transition: transform 0.3s ease`.
- `.dalali-category-img-placeholder`: same `width: 100%; aspect-ratio: 4/3` — replaced the grey flat background with `linear-gradient(135deg, #2E1E22 0%, #7B1D2B 60%, #B8902A 100%)`. Emoji size increased to `2.8rem`.
- `.dalali-category-name`: now the card footer — `padding: 12px 16px 13px`, `border-top: 1px solid var(--dalali-border)`, `text-align: center`. Turns `var(--dalali-claret)` on card hover.

---

### 2026-05-26 — Filter Strip Refinement: Labels + Claret Chevron + Focus Ring (v0.7)

**`www/index.html`**
- Each `<select>` in the filter strip now wrapped in `<div class="dalali-filter-field">` containing:
  - `<label class="dalali-filter-field-label" for="fs-*">` — uppercase claret label ("Type", "Brand", "Region", "Varietal / Style")
  - `<select id="fs-*">` — wired to the label via `for`/`id`
- Added `<span class="dalali-filter-label">Filter by:</span>` prefix before the fields.
- `<option>` placeholder text changed from "Type (All)" → "All Types" style to feel more natural.

**`theme_dalali.css`**
- `.dalali-filter-strip`: added `border-top: 3px solid var(--dalali-claret)` — visual anchor connecting strip to hero above; padding increased to `20px 0`.
- `.dalali-filter-strip-inner`: `align-items: flex-end` (bottom-aligns labelled fields with the browse button); `max-width` widened to `1040px`; `gap: 12px`.
- Added `.dalali-filter-label`: `0.72rem`, muted, uppercase, `padding-bottom: 11px` for optical baseline alignment with selects.
- Added `.dalali-filter-field`: `flex-direction: column; gap: 5px; flex: 1 1 0; min-width: 130px; max-width: 230px`.
- Added `.dalali-filter-field-label`: `0.7rem`, `font-weight: 700`, `color: var(--dalali-claret)`, uppercase.
- `.dalali-filter-strip .dalali-select`: rewritten using explicit sub-properties (`background-color`, `background-image`, `background-repeat`, `background-position`) instead of the `background` shorthand — prevents shorthand from resetting position/repeat to defaults. Chevron SVG changed from warm-brown stroke to `#7B1D2B` (claret). Added `width: 100%` so select fills the field wrapper.
- Added `.dalali-filter-strip .dalali-select:focus`: `box-shadow: 0 0 0 3px rgba(123, 29, 43, 0.12)` focus ring for keyboard accessibility.
- Added `.dalali-filter-strip .dalali-btn-browse`: `align-self: flex-end` so button bottom-aligns with labelled selects.
- Added `@media (max-width: 860px)` for filter strip: wraps to 2×2 field grid + full-width browse button. `@media (max-width: 420px)`: fields go full-width.

---

### 2026-05-26 — Hero Background Fix + Filter Strip Separation (v0.6)

**Root cause identified:** Hero section background was not rendering because the browser cached the old `theme_dalali.css` (served with `Cache-Control: max-age=43200`). An inline `<style>` block in `index.html` confirmed the CSS selector and element were correct; the file cache was the only issue.

**`theme_dalali.css`**
- `.dalali-hero-section` background rewritten from a single multi-layer `background` shorthand to explicit sub-properties (`background-color`, `background-image`, `background-size`, `background-position`, `background-repeat`) — avoids ambiguous `!important` placement inside multi-layer shorthand values.
- `.dalali-matrix-form` changed from `display: flex; flex-direction: column; gap: 12px` → `display: block` to accommodate the new form-wrapping-section structure.
- Added `.dalali-filter-strip` — white card bar below the hero: `background: var(--dalali-surface)`, `border-bottom: 1px solid var(--dalali-border)`, `box-shadow: 0 4px 16px rgba(26,12,15,0.07)`, `padding: 16px 0`.
- Added `.dalali-filter-strip-inner` — flex row, gap 8px, flex-wrap, max-width 960px centred.
- Added `.dalali-filter-strip .dalali-select` override — ivory background, warm-colour text, dark SVG chevron, claret focus border. This allows the base `.dalali-select` (dark-on-glass, used in the listing-page injected hero) to remain unchanged.
- Added `.dalali-filter-strip .dalali-select option` — explicit background/colour for dropdown options.

**`www/index.html`**
- Removed `{% block head_include %}` diagnostic inline style block.
- Restructured form: `<form>` now wraps both `<section class="dalali-hero-section">` and `<div class="dalali-filter-strip">` as sibling children, keeping a single GET submission for all inputs.
- `<section class="dalali-hero-section">` now contains only: `dalali-hero-container` → title, sub-heading, `dalali-search-row`.
- `<div class="dalali-filter-strip">` → `<div class="dalali-filter-strip-inner">` contains the 4 `<select>` filters and the "Browse Inventory" submit button.
- `.dalali-matrix-row` class removed (replaced by `.dalali-filter-strip-inner` layout).

---

### 2026-05-26 — Tiered Wholesale Pricing Product Cards (v0.5)

**`api/wholesale.py`**
- Added `get_bulk_pricing_tiers(item_codes=None)` — accepts a JSON-encoded list of item codes, returns `{item_code: best_tier_dict}` in one SQL query (JOIN `tabPricing Rule` + `tabPricing Rule Item Code`, ORDER BY `min_qty DESC`, first row per item = best tier). No type annotation to avoid Frappe v17 pydantic validation issue on list params.

**`www/index.py`**
- Added `from frappe.utils import flt`.
- Added `context.featured_products` — fetches up to 8 published `Website Item` records ordered by `ranking desc, modified desc`. Each item is enriched with: `price` (from `Item Price`, selling=1), `currency`, `case_size` (from `Item.custom_case_size`, default 12), `url`.

**`www/index.html`**
- Added `section#dalali-products.dalali-products-section` after the category grid, guarded by `{% if featured_products %}`.
- Structure: section header (title + "View all →") above `div.dalali-product-grid`.
- Each `div.dalali-product-card` carries `data-item-code`, `data-case-size`, `data-price`, `data-currency` attributes for JS enrichment.
- Card anatomy: image wrap (4:3 aspect ratio) → body (category tag, product name, pricing block, tier badge placeholder) → footer CTA.
- Bottle price rendered server-side; `.dalali-case-price` and `.dalali-tier-badge` are empty placeholders filled by `initProductCards()`.

**`public/js/dalali.js`**
- Added `if (document.getElementById("dalali-products")) { initProductCards(); }` to `frappe.ready()`.
- Added `initProductCards()` — collects all card `data-item-code` values, makes a single `get_bulk_pricing_tiers` call, then for each card: fills `.dalali-case-price` using `calcCasePrice()` and fills `.dalali-tier-badge` with a `dalali-tier-tag` span showing the best tier discount.

**`theme_dalali.css`**
- Added full product card component CSS:
  - `.dalali-products-section` — section wrapper, ivory background, bottom padding.
  - `.dalali-product-grid` — 4-col grid; 3-col ≤1024px; 2-col ≤768px; 1-col ≤480px.
  - `.dalali-product-card` — white card, 12px radius, lift+shadow on hover.
  - `.dalali-product-img-wrap` — 4:3 aspect-ratio image container; image scales 1.05× on card hover.
  - `.dalali-product-category` — 10px uppercase muted label.
  - `.dalali-product-name` — 2-line clamp, claret on hover.
  - `.dalali-bottle-price` — 1.15rem bold ink colour.
  - `.dalali-case-price` / `.dalali-case-price-amount` — smaller muted case total; `min-height` reserves layout space while JS loads.
  - `.dalali-tier-badge` / `.dalali-tier-tag` — gold-toned pill badge; `min-height` reserves space while JS loads.
  - `.dalali-product-cta` — full-width claret button, darkens on hover.

---

### 2026-05-26 — Hero CSS Fixes: Full-Width + Selector Scoping (v0.4)

**`www/index.py`** (already applied in v0.3)
- `context.full_width = 1` — removes Bootstrap `container` class from `<main>` so the hero section spans the full viewport width.
- `context.no_breadcrumbs = 1` — suppresses the breadcrumb bar above the hero.

**`theme_dalali.css`**
- **Listing-page hero scoped:** `.dalali-hero-inner` → `.dalali-hero .dalali-hero-inner` and `.dalali-hero-title` (subtitle) → `.dalali-hero .dalali-hero-title`. Prevents these rules from bleeding into the homepage hero.
- **Homepage hero scoped:** `.dalali-hero-inner, .dalali-hero-container` combined rule split — only `.dalali-hero-section .dalali-hero-container` remains (`.dalali-hero-inner` removed from this rule since homepage HTML does not use that class). `.dalali-hero-title` rule changed to `.dalali-hero-section .dalali-hero-title` to eliminate cascade conflict with listing-page subtitle rule.
- **Responsive breakpoint** `@media (max-width: 576px)` hero title selector updated from `.dalali-hero-title` → `.dalali-hero-section .dalali-hero-title`.
- **Hero background image** updated from `.jpg` → `.png` to match the actual file at `public/images/hero-bg.png`.

---

### 2026-05-26 — Category Grid Section: Server-Side Render (v0.3)

**`www/index.py`**
- Added `from frappe.utils import quote`.
- Added `context.category_grid` — fetches Item Groups (`show_in_website=1, is_group=0`, limit 8) with `website_image`, `image`, and `route` fields; enriches each record with `image_url` and `url` (`/webshop?item_group=<quoted name>`).

**`www/index.html`**
- Replaced the bare `#dalali-category-grid-mount` div with a full server-side rendered `section#dalali-category-grid.dalali-category-section`.
- Section only renders when `category_grid` is non-empty (`{% if category_grid %}`).
- Structure: section header row (`h2` + "View all →" link) above a `div.dalali-category-grid` of up to 8 linked cards.
- Each card: `img.dalali-category-img` (or `div.dalali-category-img-placeholder` with 🍷 emoji) + `span.dalali-category-name`.
- The `id="dalali-category-grid"` on the section acts as the JS idempotency guard.

**`theme_dalali.css`**
- Added `.dalali-category-section` — `padding: 56px 0 64px`, ivory background.
- Added `.dalali-section-header` — flex row, space-between, baseline aligned.
- Added `.dalali-section-title` — `1.35rem`, ink colour.
- Added `.dalali-section-link` — claret colour, inline-flex with SVG arrow; hover: gold + translateX(3px) on arrow.
- Updated `.dalali-category-grid` — `border-radius: 12px` (was 10px), removed `margin: 32px 0` (now handled by section padding).
- Updated `.dalali-category-card` — `min-height: 148px`, `padding: 32px 20px 28px`.
- Added `.dalali-category-card:hover .dalali-category-img-placeholder` — semi-transparent background on hover.
- Added `@media (max-width: 400px)` breakpoint: 1-column grid.
- `dalali-category-img-placeholder` transition added.

**`public/js/dalali.js`**
- `injectCategoryGrid()`: upgraded JS-injected version to use `section.dalali-category-section` + `.dalali-section-header` structure to match server-side HTML. Homepage no longer calls the API (server-side guard via `#dalali-category-grid` ID). Listing pages still inject via API.

---

### 2026-05-26 — Hero & Filter Matrix: 4-Select Upgrade + Accessibility (v0.2)

**`www/index.py`**
- Added `context.varietals` — `SELECT DISTINCT custom_wine_varietal FROM tabItem` ordered ASC.

**`www/index.html`**
- Renamed container class from `.dalali-hero-inner` → `.dalali-hero-container` to match semantic structure.
- Changed form `action` from `/all-products` → `/webshop`.
- Added 4th filter dropdown `select[name="custom_varietal"]` populated from `context.varietals`.
- Added `aria-label` attributes on all form controls (input, 4× select, 2× button) to fix accessibility warnings.
- Added HTML comments mapping each element to the wireframe hierarchy.

**`theme_dalali.css`**
- `.dalali-hero-inner, .dalali-hero-container` — both selectors now share the same rule; `max-width` widened to `960px` to accommodate 4 selects.
- `.dalali-matrix-row` — changed `flex-wrap: wrap` → `flex-wrap: nowrap` so all 4 selects + button stay on one line on desktop.
- `.dalali-select` — changed `flex: 1` → `flex: 1 1 0`; `min-width` reduced from `150px` → `120px`.
- Responsive breakpoints restructured:
  - `≤900px` — 2×2 CSS grid for selects (`flex: 1 1 calc(50% - 4px)`), browse button full-width.
  - `≤576px` — full column stack for all controls.

---

### 2026-05-26 — Initial Dalali Build (v0.1)

**Custom Fields**
- Added 10 custom fields to `Item` doctype via `fixtures/custom_field.json`: `custom_dalali_section`, `custom_liquor_category`, `custom_wine_varietal`, `custom_origin_country`, `custom_region`, `custom_dalali_col`, `custom_vintage_year`, `custom_alcohol_content`, `custom_case_size`, `custom_importer`.

**Hooks**
- Registered `web_include_css` for `base.css`, `theme_glass.css`, `theme_dalali.css`.
- Registered `web_include_js` for `theme.js`, `dalali.js`.
- Registered `update_website_context → dt_ecommerce.utils.extend_dalali_context`.
- Registered `jinja.methods → dt_ecommerce.utils.dalali_bootstrap_script`.
- Registered `fixtures` filter for 10 Item custom fields.

**API**
- Created `api/__init__.py` and `api/wholesale.py` with three guest endpoints: `get_pricing_tiers`, `get_item_wholesale_meta`, `get_category_grid`.

**Utils**
- Created `utils.py` with `extend_dalali_context()` (update_website_context hook) and `dalali_bootstrap_script()` (Jinja global).

**CSS**
- Created `public/css/theme_dalali.css` with full brand palette, promo bar, navbar override, toggle, tier table, tier modal, metadata grid, category grid, filter bar, cart buttons, hero section, and filter matrix styles.

**JavaScript**
- Created `public/js/dalali.js` with: `injectPromoBar`, `initWholesalePDP`, `injectUnitCaseToggle`, `injectTierTable`, `openTierModal`, `injectWineMeta`, `injectHeroSection`, `injectCategoryGrid`, `convertFiltersToHorizontal`.

**Templates**
- Created `templates/generators/item/item.html` overriding webshop PDP template: added `dalali-mode` class and server-side `window.dalali_*` bootstrap script block.

**Homepage**
- Created `www/index.py` with `get_context()` fetching categories, brands, regions.
- Created `www/index.html` with Dalali hero section, two-row search + filter matrix form (targeting `/all-products`), and `#dalali-category-grid-mount` div.
