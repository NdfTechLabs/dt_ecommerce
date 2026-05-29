# Dalali Webshop — Data Population Guide

**App:** `dt_ecommerce`  
**Site:** `erpnext.localhost`  
**Company:** `NdfTechLabs`  
**Last updated:** 2026-05-27

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Seed Scripts Reference](#2-seed-scripts-reference)
3. [Item Group Hierarchy](#3-item-group-hierarchy)
4. [Brands](#4-brands)
5. [Items (Product Master)](#5-items-product-master)
6. [Website Items](#6-website-items)
7. [Item Prices](#7-item-prices)
8. [Promotional Campaigns & Pricing Rules](#8-promotional-campaigns--pricing-rules)
9. [Product Bundles](#9-product-bundles)
10. [Opening Stock](#10-opening-stock)
11. [Webshop Settings](#11-webshop-settings)
12. [Catalog Guard — Internal vs External](#12-catalog-guard--internal-vs-external)
13. [Order → Accounting Flow](#13-order--accounting-flow)
14. [Adding New Products](#14-adding-new-products)
15. [Changelog](#15-changelog)

---

## 1. Architecture Overview

The Dalali webshop is powered by four linked data layers in ERPNext:

```
┌─────────────────────────────────────────────────────────────┐
│  WEBSHOP (Frappe Webshop app)                               │
│  Reads: Website Item (published=1) + Item Price             │
│  Stock check: Item.item_defaults[company].default_warehouse │
└─────────────────────────────────────────────────────────────┘
         ↑ published from
┌─────────────────────────────────────────────────────────────┐
│  CATALOG LAYER                                              │
│  Item Group → Item → Website Item → Item Price             │
│  Images stored in: sites/erpnext.localhost/public/files/   │
└─────────────────────────────────────────────────────────────┘
         ↑ stock held in
┌─────────────────────────────────────────────────────────────┐
│  INVENTORY LAYER                                            │
│  Warehouse: Stores - NDF                                   │
│  Valuation: FIFO, Perpetual Inventory enabled              │
│  Opening stock entry: MAT-STE-2026-00003                   │
└─────────────────────────────────────────────────────────────┘
         ↑ flows through
┌─────────────────────────────────────────────────────────────┐
│  ACCOUNTING LAYER  (Chart of Accounts — NdfTechLabs)       │
│  Revenue  : Sales - NDF                                    │
│  COGS     : Cost of Goods Sold - NDF                       │
│  Stock    : Stock In Hand - NDF                            │
│  Opening  : Temporary Opening - NDF  (reconcile later)     │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Seed Scripts Reference

All seed scripts live inside the `dt_ecommerce` Python package and are run with `bench execute`. They are **idempotent** — safe to re-run; existing records are skipped or updated.

| Script module | Command | What it does |
|---|---|---|
| `dt_ecommerce.seed` | `bench --site erpnext.localhost execute dt_ecommerce.seed.run` | Creates all catalog data: Item Groups, Brands, Items, Website Items, Prices, Product Bundles. Downloads product images from Unsplash CDN. |
| `dt_ecommerce.restructure_groups` | `bench --site erpnext.localhost execute dt_ecommerce.restructure_groups.run` | Builds the two-branch Item Group tree (Wholesale Catalog / Internal Operations) and unpublishes any accidental internal listings. |
| `dt_ecommerce.setup_stock` | `bench --site erpnext.localhost execute dt_ecommerce.setup_stock.run` | Creates opening stock entry (`Material Receipt`), sets default warehouse on Items, enables price/availability display in Webshop Settings. |
| `dt_ecommerce.seed_campaigns` | `bench --site erpnext.localhost execute dt_ecommerce.seed_campaigns.run` | Creates 6 Campaign records and 10 linked Pricing Rules covering all liquor categories. Uses correct `apply_on = Item Group` + `item_groups` child table structure. |

**After any run:**
```bash
bench --site erpnext.localhost clear-cache
```

---

## 3. Item Group Hierarchy

The tree uses two top-level parent branches to enforce catalog/internal separation.

```
All Item Groups  (root)
├── Dalali Wholesale Catalog     show_in_website = YES  📁
│   ├── Whisky & Scotch          show_in_website = YES
│   ├── Red Wine                 show_in_website = YES
│   ├── White Wine               show_in_website = YES
│   ├── Champagne & Sparkling    show_in_website = YES
│   ├── Beer & Cider             show_in_website = YES
│   ├── Gin & Vodka              show_in_website = YES
│   ├── Brandy & Cognac          show_in_website = YES
│   └── Rum & Tequila            show_in_website = YES
└── Internal Operations          show_in_website = NO   📁
    ├── Products                 show_in_website = NO
    ├── Raw Material             show_in_website = NO
    ├── Services                 show_in_website = NO
    ├── Sub Assemblies           show_in_website = NO
    └── Consumable               show_in_website = NO
```

**DocType:** `Item Group`  
**Key fields:** `item_group_name`, `parent_item_group`, `is_group`, `show_in_website`, `website_image`, `route`

Category images are stored as `/files/dalali-cat-<slug>.jpg` in the site's public files directory and referenced via `website_image`.

---

## 4. Brands

**DocType:** `Brand`  
**Key field:** `brand` (autoname = `field:brand`)

| Brand |
|---|
| Absolut |
| Bacardi |
| Hennessy |
| Jack Daniel's |
| Jameson |
| Johnnie Walker |
| Moët & Chandon |
| Tusker |

> Legacy phone brands (Nokia, Oppo, Huawei, Google Pixel, Techno) remain but belong to the Internal Operations tree and are never visible on the webshop.

---

## 5. Items (Product Master)

**DocType:** `Item`  
**Custom fields** (added by `dt_ecommerce` fixtures):

| Fieldname | Label | Type |
|---|---|---|
| `custom_case_size` | Bottles per Case | Int |
| `custom_alcohol_content` | Alcohol Content (%) | Float |
| `custom_vintage_year` | Vintage / Age Statement | Int |
| `custom_region` | Region / Distillery | Data |
| `custom_origin_country` | Origin Country | Data |
| `custom_wine_varietal` | Varietal / Style | Small Text |
| `custom_liquor_category` | Liquor Category | Select |

### Seeded Items

| Item Code | Item Name | Group | Brand | Region | Country | Varietal | ABV% | Vintage | Case |
|---|---|---|---|---|---|---|---|---|---|
| `DAL-JWB-750` | Johnnie Walker Black Label 750ml | Whisky & Scotch | Johnnie Walker | Speyside | Scotland | Blended Scotch Whisky | 40 | — | 12 |
| `DAL-JWG-750` | Johnnie Walker Gold Label 750ml | Whisky & Scotch | Johnnie Walker | Highlands | Scotland | Blended Scotch Whisky | 40 | — | 12 |
| `DAL-JAM-700` | Jameson Irish Whiskey 700ml | Whisky & Scotch | Jameson | Cork | Ireland | Blended Irish Whiskey | 40 | — | 12 |
| `DAL-JD-700` | Jack Daniel's Old No.7 700ml | Whisky & Scotch | Jack Daniel's | Tennessee | USA | Tennessee Whiskey | 40 | — | 12 |
| `DAL-CAB-750` | Château Reserve Cabernet 750ml | Red Wine | Johnnie Walker | Bordeaux | France | Cabernet Sauvignon | 13.5 | 2019 | 12 |
| `DAL-MALBEC-750` | Mendoza Malbec 750ml | Red Wine | Jameson | Mendoza | Argentina | Malbec | 14 | 2020 | 12 |
| `DAL-CHARD-750` | Stellenbosch Chardonnay 750ml | White Wine | Absolut | Stellenbosch | South Africa | Chardonnay | 13 | 2021 | 12 |
| `DAL-MOET-750` | Moët Impérial Brut 750ml | Champagne & Sparkling | Moët & Chandon | Épernay | France | Brut Champagne | 12 | — | 6 |
| `DAL-TUSK-500` | Tusker Lager 500ml | Beer & Cider | Tusker | Nairobi | Kenya | Lager | 4.2 | — | 24 |
| `DAL-ABSV-1L` | Absolut Vodka 1 Litre | Gin & Vodka | Absolut | Åhus | Sweden | Premium Vodka | 40 | — | 12 |
| `DAL-HENN-700` | Hennessy VS Cognac 700ml | Brandy & Cognac | Hennessy | Cognac | France | VS Cognac | 40 | — | 12 |
| `DAL-BAC-700` | Bacardi Carta Blanca 700ml | Rum & Tequila | Bacardi | Puerto Rico | Puerto Rico | White Rum | 37.5 | — | 12 |

**Bundle parent Items** (non-stock, `is_stock_item = 0`):

| Item Code | Item Name | Group |
|---|---|---|
| `DAL-BND-WHISKY` | Dalali Whisky Tasting Bundle | Whisky & Scotch |
| `DAL-BND-WINE` | Dalali Red Wine Case Mix | Red Wine |
| `DAL-BND-PARTY` | Dalali Party Starter Pack | Rum & Tequila |

---

## 6. Website Items

**DocType:** `Website Item`  
Published Website Items are the **only** records visible on the webshop. Every item requires a corresponding published Website Item.

**Key fields:** `item_code`, `web_item_name`, `published` (must be `1`), `website_image`, `ranking` (higher = shown first in featured grid), `route` (auto-generated URL slug)

| Item Code | Web Name | Ranking | Image file |
|---|---|---|---|
| `DAL-JWB-750` | Johnnie Walker Black Label 750ml | 100 | `dalali-prod-jwblack.jpg` |
| `DAL-MOET-750` | Moët Impérial Brut | 95 | `dalali-prod-moet.jpg` |
| `DAL-JWG-750` | Johnnie Walker Gold Label 750ml | 90 | `dalali-prod-jwgold.jpg` |
| `DAL-HENN-700` | Hennessy VS Cognac 700ml | 88 | `dalali-prod-hennessy.jpg` |
| `DAL-JAM-700` | Jameson Irish Whiskey 700ml | 85 | `dalali-prod-jameson.jpg` |
| `DAL-JD-700` | Jack Daniel's Old No.7 700ml | 80 | `dalali-prod-jd.jpg` |
| `DAL-CAB-750` | Château Reserve Cabernet Sauvignon | 75 | `dalali-prod-cab.jpg` |
| `DAL-MALBEC-750` | Mendoza Malbec | 70 | `dalali-prod-malbec.jpg` |
| `DAL-ABSV-1L` | Absolut Vodka 1 Litre | 72 | `dalali-prod-absolut.jpg` |
| `DAL-CHARD-750` | Stellenbosch Chardonnay | 65 | `dalali-prod-chard.jpg` |
| `DAL-TUSK-500` | Tusker Lager 500ml | 60 | `dalali-prod-tusker.jpg` |
| `DAL-BAC-700` | Bacardi Carta Blanca Rum 700ml | 55 | `dalali-prod-bacardi.jpg` |
| `DAL-BND-WHISKY` | Dalali Whisky Tasting Bundle | 50 | `dalali-bnd-whisky.jpg` |
| `DAL-BND-WINE` | Dalali Red Wine Case Mix | 45 | `dalali-bnd-wine.jpg` |
| `DAL-BND-PARTY` | Dalali Party Starter Pack | 40 | `dalali-bnd-party.jpg` |

**Image files** are stored at:  
`sites/erpnext.localhost/public/files/dalali-*.jpg`

They are downloaded at seed time from the Unsplash CDN and cached locally. The seed script skips already-downloaded files (idempotent).

---

## 7. Item Prices

**DocType:** `Item Price`  
**Price List:** `Standard Selling` (KES, selling = Yes)

All prices are per individual **bottle** (not per case). The webshop JS layer calculates and displays the case price dynamically using `custom_case_size`.

| Item Code | Selling Price (KES/btl) | Cost / Valuation (KES/btl) | Gross Margin |
|---|---|---|---|
| `DAL-JWB-750` | 3,200 | 1,920 | 40% |
| `DAL-JWG-750` | 6,500 | 3,900 | 40% |
| `DAL-JAM-700` | 2,800 | 1,680 | 40% |
| `DAL-JD-700` | 2,500 | 1,500 | 40% |
| `DAL-CAB-750` | 1,900 | 1,140 | 40% |
| `DAL-MALBEC-750` | 1,600 | 960 | 40% |
| `DAL-CHARD-750` | 1,450 | 870 | 40% |
| `DAL-MOET-750` | 9,800 | 5,880 | 40% |
| `DAL-TUSK-500` | 280 | 168 | 40% |
| `DAL-ABSV-1L` | 3,600 | 2,160 | 40% |
| `DAL-HENN-700` | 8,500 | 5,100 | 40% |
| `DAL-BAC-700` | 1,950 | 1,170 | 40% |
| `DAL-BND-WHISKY` | 29,500 | — | — |
| `DAL-BND-WINE` | 9,500 | — | — |
| `DAL-BND-PARTY` | 14,200 | — | — |

> Valuation rates (cost) are seeded as ~60% of selling price to approximate wholesale landed cost. Update these from actual Purchase Invoices as stock is replenished.

---

## 8. Promotional Campaigns & Pricing Rules

Two ERPNext doctypes work together:

| DocType | Role |
|---|---|
| `Campaign` | CRM/marketing label — used for reporting, pipeline attribution, Sales Order tagging |
| `Pricing Rule` | The actual discount engine — evaluated at order/quote creation to apply price reductions |

**Campaign records and Pricing Rules are separate objects.** The `campaign` Link field on `Pricing Rule` is cleared by the ERPNext controller (`cleanup_fields_value`) whenever `applicable_for` is not set to `"Campaign"`. For automatic webshop promotions that apply to **all customers**, leave `applicable_for` empty — the discount is applied by date range and item group, not by CRM campaign assignment.

The Campaign records seeded here serve as a reference / reporting grouping and match the homepage promotional banner copy. The actual discount enforcement is entirely in the Pricing Rules.

---

### Important: Pricing Rule structure for Item Group discounts

The Pricing Rule controller uses `apply_on` (not `applicable_for`) to determine which child table holds the targets:

| `apply_on` value | Child table | Field in row |
|---|---|---|
| `Item Code` | `items` | `item_code` |
| **`Item Group`** | **`item_groups`** | **`item_group`** |
| `Brand` | `brands` | `brand` |

When creating via `frappe.get_doc`, always set **`apply_on = "Item Group"`** and populate the **`item_groups`** child table:
```python
"apply_on":    "Item Group",
"item_groups": [{"item_group": "Whisky & Scotch"}],
```

Leave `applicable_for` blank so the rule fires for **all customers** automatically.

---

### Seeded Campaigns

All 6 campaigns and 10 pricing rules were created by `dt_ecommerce.seed_campaigns` on 2026-05-27.

#### 1. May Case Bonanza
> End-of-month whisky clearance — 15% off all scotch and Irish whiskey cases.

| Rule Title | Item Group | Discount | Min Qty | Valid (days) | Priority |
|---|---|---|---|---|---|
| May Case Bonanza — 15% Off All Whisky | Whisky & Scotch | 15% | — | 30 | 5 |

---

#### 2. Wine Week
> Annual wine promotion covering all red and white wine categories.

| Rule Title | Item Group | Discount | Min Qty | Valid (days) | Priority |
|---|---|---|---|---|---|
| Wine Week — 10% Off Red Wine | Red Wine | 10% | — | 14 | 5 |
| Wine Week — 10% Off White Wine | White Wine | 10% | — | 14 | 5 |

---

#### 3. Champagne Flash Sale
> 48-hour flash promotion on all sparkling wines and champagne.

| Rule Title | Item Group | Discount | Min Qty | Valid (days) | Priority |
|---|---|---|---|---|---|
| Champagne Flash Sale — KES 2,000 Off Per Case | Champagne & Sparkling | KES 2,000 off | — | 7 | 8 |

---

#### 4. Festive Season Sale
> Year-end festive promotion across all spirits — biggest discount of the year.

| Rule Title | Item Group | Discount | Min Qty | Valid (days) | Priority |
|---|---|---|---|---|---|
| Festive Season — 20% Off Whisky & Scotch | Whisky & Scotch | 20% | 12 btl (1 case) | 60 | 10 |
| Festive Season — 15% Off Brandy & Cognac | Brandy & Cognac | 15% | 12 btl (1 case) | 60 | 10 |
| Festive Season — 15% Off Champagne & Sparkling | Champagne & Sparkling | 15% | 6 btl (1 case) | 60 | 9 |

`min_qty` enforces case-level ordering: the discount only applies when the customer orders at least 1 full case.

---

#### 5. Trade Account Welcome
> Ongoing discount for newly verified trade accounts.

| Rule Title | Item Group | Discount | Min Qty | Valid | Priority |
|---|---|---|---|---|---|
| Trade Welcome — 5% Off Gin & Vodka | Gin & Vodka | 5% | — | No expiry | 2 |
| Trade Welcome — 5% Off Rum & Tequila | Rum & Tequila | 5% | — | No expiry | 2 |

These rules have no `valid_upto` date — they remain active until manually disabled.

---

#### 6. Beer & Cider Summer
> Summer push on local and imported beers — ideal for restaurant and bar accounts.

| Rule Title | Item Group | Discount | Min Qty | Valid (days) | Priority |
|---|---|---|---|---|---|
| Summer Beer Deal — 12% Off Beer & Cider (5+ Cases) | Beer & Cider | 12% | 120 btl (5 cases × 24) | 21 | 6 |

---

> **Note:** Valid dates are set relative to the day the seed script runs. Re-run the seed to extend them (existing records are skipped), or edit Pricing Rule records directly in ERPNext.

---

### Creating a new promotional campaign

1. **CRM → Campaign** → New → set `campaign_name` and `description` (for reporting/attribution)
2. **Accounts → Pricing Rule** → New:
   - `apply_on = Item Group`  ← controls which child table is used
   - `applicable_for` = leave **blank** (applies to all customers automatically)
   - Add the target Item Group in the **Item Groups** child table
   - `selling = Yes`, `disable = No`
   - `price_or_product_discount = Price`
   - `rate_or_discount = Discount Percentage` (or `Discount Amount`)
   - Set `discount_percentage` OR `discount_amount`
   - Set `valid_from` / `valid_upto`; leave `valid_upto` blank for no expiry
   - Set `priority` (higher = applied first when multiple rules match)
   - Set `min_qty` to enforce case-level ordering (e.g. 12 for a standard case, 6 for champagne)
3. The discount fires automatically on all matching Sales Orders / Quotations within the date range.

> **Do not** set `applicable_for = "Campaign"` unless you want the discount to only apply when a staff member manually tags an order with that Campaign — that is a different (CRM attribution) use case.

---

## 9. Product Bundles

**DocType:** `Product Bundle`  
A bundle requires: (1) a parent non-stock `Item`, (2) a `Product Bundle` record with component items, (3) a published `Website Item` for the parent, (4) an `Item Price` for the parent.

### Seeded Bundles

#### DAL-BND-WHISKY — Dalali Whisky Tasting Bundle (KES 29,500)
> Curated selection of 4 premium whiskies — Johnnie Walker Black, Gold, Jameson, and Jack Daniel's.

| Component | Qty |
|---|---|
| DAL-JWB-750 — JW Black Label 750ml | 2 |
| DAL-JWG-750 — JW Gold Label 750ml | 1 |
| DAL-JAM-700 — Jameson Irish Whiskey 700ml | 1 |
| DAL-JD-700 — Jack Daniel's Old No.7 700ml | 2 |

#### DAL-BND-WINE — Dalali Red Wine Case Mix (KES 9,500)
> Mixed case of 6 bottles — Bordeaux Cabernet, Mendoza Malbec, Stellenbosch Chardonnay.

| Component | Qty |
|---|---|
| DAL-CAB-750 — Château Reserve Cabernet 750ml | 2 |
| DAL-MALBEC-750 — Mendoza Malbec 750ml | 2 |
| DAL-CHARD-750 — Stellenbosch Chardonnay 750ml | 2 |

#### DAL-BND-PARTY — Dalali Party Starter Pack (KES 14,200)
> Bacardi, Absolut, Jack Daniel's, and Tusker lager. Serves up to 30 guests.

| Component | Qty |
|---|---|
| DAL-BAC-700 — Bacardi Carta Blanca 700ml | 2 |
| DAL-ABSV-1L — Absolut Vodka 1 Litre | 1 |
| DAL-JD-700 — Jack Daniel's Old No.7 700ml | 1 |
| DAL-TUSK-500 — Tusker Lager 500ml | 6 |

---

## 10. Opening Stock

**DocType:** `Stock Entry` (type: Material Receipt)  
**Entry:** `MAT-STE-2026-00003`  
**Date:** 2026-05-27  
**Warehouse:** `Stores - NDF`

| Item Code | Opening Qty | Valuation Rate (KES) | Stock Value (KES) |
|---|---|---|---|
| DAL-JWB-750 | 48 btl (4 cases) | 1,920 | 92,160 |
| DAL-JWG-750 | 24 btl (2 cases) | 3,900 | 93,600 |
| DAL-JAM-700 | 36 btl (3 cases) | 1,680 | 60,480 |
| DAL-JD-700 | 36 btl (3 cases) | 1,500 | 54,000 |
| DAL-CAB-750 | 24 btl (2 cases) | 1,140 | 27,360 |
| DAL-MALBEC-750 | 24 btl (2 cases) | 960 | 23,040 |
| DAL-CHARD-750 | 24 btl (2 cases) | 870 | 20,880 |
| DAL-MOET-750 | 12 btl (2 cases × 6) | 5,880 | 70,560 |
| DAL-TUSK-500 | 96 btl (4 cases × 24) | 168 | 16,128 |
| DAL-ABSV-1L | 24 btl (2 cases) | 2,160 | 51,840 |
| DAL-HENN-700 | 24 btl (2 cases) | 5,100 | 122,400 |
| DAL-BAC-700 | 24 btl (2 cases) | 1,170 | 28,080 |
| **TOTAL** | | | **KES 660,528** |

### GL Posting (Perpetual Inventory)
```
DR  Stock In Hand - NDF          KES 660,528   ← asset on balance sheet
CR  Temporary Opening - NDF      KES 660,528   ← opening balance placeholder
```

> `Temporary Opening - NDF` is the standard ERPNext holding account for opening balances. Reconcile it against `Opening Balance Equity - NDF` when performing the formal opening balance setup.

### Stock check on the webshop
Each `DAL-*` Item has `item_defaults[company=NdfTechLabs].default_warehouse = Stores - NDF`. The webshop reads stock availability from this per-company default warehouse.

---

## 11. Webshop Settings

**DocType:** `Webshop Settings` (Single)

| Field | Value | Notes |
|---|---|---|
| `enabled` | Yes | Webshop is live |
| `company` | NdfTechLabs | |
| `price_list` | Standard Selling | KES prices shown |
| `show_price` | **Yes** | Prices visible to all visitors |
| `show_stock_availability` | **Yes** | In Stock / Out of Stock badge shown |
| `show_quantity_in_website` | No | Exact qty hidden (wholesale — no need to expose) |
| `allow_items_not_in_stock` | **No** | Checkout blocked when qty = 0 |
| `enable_checkout` | Yes | |
| `payment_gateway_account` | Mpesa-Daraja3.0 - KES - NDF | M-Pesa payment at checkout |
| `payment_success_url` | Orders | Redirects to order list after payment |
| `enable_wishlist` | Yes | |
| `enable_reviews` | Yes | |
| `default_customer_group` | Individual | |

---

## 12. Catalog Guard — Internal vs External

Three defensive layers prevent internal operation items from appearing on the webshop.

### Layer 1 — Item Group hierarchy (structural)
Items under `Internal Operations` have `show_in_website = 0`. They never appear in the webshop filter dropdowns or the category grid, regardless of whether a Website Item is created for them.

### Layer 2 — Website Item publication (primary gate)
An item is **only visible on the webshop** if it has a `Website Item` record with `published = 1`. Internal items (Raw Material, Consumable, etc.) must never have a published Website Item.

### Layer 3 — Validation hook (code enforcement)
Registered in `hooks.py`:
```python
doc_events = {
    "Website Item": {
        "validate": "dt_ecommerce.catalog_guard.block_internal_publish",
    },
}
```
The hook in `dt_ecommerce/catalog_guard.py` raises a `ValidationError` if someone attempts to save a Website Item as `published = 1` when the underlying Item's group either:
- Lives under the `Internal Operations` subtree, **or**
- Has `show_in_website = 0`

The error message explicitly names the group and instructs the user to move the item to the Wholesale Catalog first.

### Adding a new internal item type
1. Create the Item under any group inside `Internal Operations`
2. No further action needed — it cannot be published to the webshop by any means

### Adding a new webshop category
1. Create an `Item Group` with `parent_item_group = Dalali Wholesale Catalog` and `show_in_website = 1`
2. Upload a category image (`website_image`)
3. Create Items in that group → they are immediately eligible for webshop publication

---

## 13. Order → Accounting Flow

A webshop order goes through three stages before appearing in the ledgers.

```
Customer checkout (webshop + M-Pesa)
        │
        ▼ AUTOMATIC
┌──────────────────────────────────────────────────────────────┐
│  Sales Order                                                 │
│  • Created by webshop on successful payment                  │
│  • Status: "To Deliver"                                      │
│  • NO GL entries  |  NO stock movement                       │
└──────────────────────────────────────────────────────────────┘
        │
        ▼ STAFF ACTION — Stock > Delivery Note > Submit
┌──────────────────────────────────────────────────────────────┐
│  Delivery Note                                               │
│  DR  Cost of Goods Sold - NDF   (valuation × qty)           │
│  CR  Stock In Hand - NDF        (reduces stock asset)        │
│                                                              │
│  Stock Ledger Entry created → bin qty decremented           │
└──────────────────────────────────────────────────────────────┘
        │
        ▼ STAFF ACTION — Delivery Note > Make Invoice > Submit
┌──────────────────────────────────────────────────────────────┐
│  Sales Invoice                                               │
│  DR  Accounts Receivable - NDF  (or cash if walk-in)        │
│  CR  Sales - NDF                (revenue recognised)         │
└──────────────────────────────────────────────────────────────┘
        │
        ▼ AUTO-LINKED (M-Pesa payment already collected)
┌──────────────────────────────────────────────────────────────┐
│  Payment Entry                                               │
│  DR  Mpesa-Daraja3.0 - NDF      (cash received)             │
│  CR  Accounts Receivable - NDF  (receivable cleared)        │
└──────────────────────────────────────────────────────────────┘
```

**Accounts used (NdfTechLabs):**

| Account | Type | Role |
|---|---|---|
| Sales - NDF | Income | Revenue from webshop sales |
| Cost of Goods Sold - NDF | Expense (COGS) | Landed cost of goods delivered |
| Stock In Hand - NDF | Asset (Stock) | On-hand inventory value |
| Accounts Receivable - NDF | Asset | Outstanding customer balances |
| Mpesa-Daraja3.0 - NDF | Asset (Bank) | M-Pesa settlement account |
| Temporary Opening - NDF | Asset | Opening stock balance (reconcile vs equity) |
| Opening Balance Equity - NDF | Equity | Reconciliation target for opening entries |

---

## 14. Adding New Products

Follow this checklist for each new SKU:

### Step 1 — Item master
```
Stock → Item → New
  item_code         : DAL-<BRAND>-<SIZE>   (e.g. DAL-GLENL-700)
  item_group        : (choose from Dalali Wholesale Catalog branches)
  brand             : (existing Brand or create new)
  stock_uom         : Nos
  is_stock_item     : Yes
  custom_case_size  : 12 (or 6 for champagne, 24 for beer)
  custom_region     : e.g. Speyside
  custom_origin_country : Scotland
  custom_wine_varietal  : e.g. Single Malt Scotch
  custom_alcohol_content: 43
  Item Defaults → company: NdfTechLabs, default_warehouse: Stores - NDF
```

### Step 2 — Website Item
```
E-Commerce → Website Item → New
  item_code      : (link to item above)
  web_item_name  : full display name
  published      : Yes
  website_image  : /files/your-image.jpg
  ranking        : 50–100 (higher = more prominent)
```

### Step 3 — Item Price
```
Stock → Item Price → New
  item_code        : (link)
  price_list       : Standard Selling
  selling          : Yes
  currency         : KES
  price_list_rate  : bottle price
```

### Step 4 — Stock receipt
When physical stock arrives:
```
Stock → Purchase Receipt → New   (preferred — links to Purchase Order)
  OR
Stock → Stock Entry → Material Receipt   (for ad-hoc top-ups)
  item_code   : DAL-xxx
  qty         : received qty
  t_warehouse : Stores - NDF
  basic_rate  : landed cost per bottle
```

Submitting the receipt automatically posts:
```
DR  Stock In Hand - NDF
CR  Stock Received But Not Billed - NDF   (if Purchase Receipt)
    OR Temporary Opening - NDF            (if Stock Entry)
```

---

## 16. Catalog Page  (`/catalog`)

The `/catalog` route is the primary B2B product listing page — a left-sidebar split layout with a 5-column dense product grid. It completely replaces the default webshop listing pages for Dalali.

### Files

| File | Role |
|---|---|
| `dt_ecommerce/www/catalog.py` | Server-side `get_context()` — reads all URL params, builds SQL query, returns items + facet data |
| `dt_ecommerce/www/catalog.html` | Jinja2 template — breadcrumb, sidebar form, 5-col grid, pagination |
| `dt_ecommerce/public/css/theme_dalali.css` | CSS section "Catalog Page" appended at end of file |
| `dt_ecommerce/public/js/dalali.js` | `initCatalogPage()` and 5 sub-functions appended at end |

### URL params

| Param | Type | Example |
|---|---|---|
| `item_group` | string | `?item_group=Red+Wine` |
| `custom_region` | string | `?custom_region=Bordeaux` |
| `custom_varietal` | string | `?custom_varietal=Cabernet+Sauvignon` |
| `custom_vintage` | integer | `?custom_vintage=2020` |
| `min_price` / `max_price` | KES integer | `?min_price=500&max_price=3000` |
| `search` | string | `?search=Jameson` |
| `brand` | string (single) | `?brand=Absolut` |
| `brands` | repeatable | `?brands=Jameson&brands=Absolut` |
| `packaging` | `bottle` \| `case` | `?packaging=case` |
| `show_vol_only` | `1` | `?show_vol_only=1` |
| `page` | integer | `?page=2` (default 1) |

### Sidebar sections

1. **Category Tree** — `Dalali Wholesale Catalog` nested set traversal using lft/rgt; shows sub-groups with item counts + sibling pivot at leaf nodes.
2. **Profile Locator Widget** — three selects (varietal / region / vintage) + "Find Compatible Stock" submit button.
3. **Packaging** — radio group (All / Bottle / Case) + "Volume discount only" checkbox.
4. **Price Range** — dual-thumb `<input type="range">` synced to number text inputs via `initPriceRangeSlider()`.
5. **Brand Directory** — scrollable checkbox list (max-height 180px) with client-side typeahead via `initBrandSearch()`.

### Product card anatomy

- **Square 1:1 image** with hover zoom + absolute wishlist ♡ button (top-right) + category pill (bottom-left)
- **Name** (2-line clamp) + brand · vintage · ABV meta row
- **Pricing block**: bottle price → case price + "Why is the price variable?" button (→ `openTierModal()`)
- **Split CTA footer**: `[🛒]` outline icon-button (add to cart) + `[Buy Now]` solid claret anchor

### Homepage integration

All "View all" and category card links on the homepage (`index.html`) and category grid builder (`injectCategoryGrid()` in `dalali.js`) now point to `/catalog`. The homepage filter-strip form action is also `/catalog`.

---

## 15. Changelog

| Version | Date | Description |
|---|---|---|
| v1.0 | 2026-05-27 | Initial data population: 8 Item Groups, 8 Brands, 12 Items + 3 bundle parents, 15 Website Items, 15 Item Prices, 3 Product Bundles, opening stock MAT-STE-2026-00003 (KES 660,528) |
| v1.0 | 2026-05-27 | Item Group tree restructured: Dalali Wholesale Catalog / Internal Operations two-branch hierarchy |
| v1.0 | 2026-05-27 | Catalog guard registered (catalog_guard.py + hooks.py doc_event) |
| v1.0 | 2026-05-27 | Webshop Settings: show_price and show_stock_availability enabled |
| v1.1 | 2026-05-27 | Campaigns: 6 Campaign records (CRM/reporting) and 10 Pricing Rules (discount engine) seeded via seed_campaigns.py. Fixed: `apply_on = "Item Group"` + `item_groups` child table; `applicable_for` left blank so discounts fire automatically for all customers. Campaign link on Pricing Rule intentionally omitted (ERPNext controller clears it when applicable_for is blank). |
| v1.2 | 2026-05-27 | Catalog page `/catalog`: B2B left-sidebar split layout (240px sidebar + 5-col dense grid). Files: `www/catalog.py`, `www/catalog.html`, CSS + JS extensions. Homepage links updated from `/webshop` to `/catalog`. |
