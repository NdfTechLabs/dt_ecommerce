# dt_ecommerce — Dalali B2B Wholesale Liquor Webshop

A high-converting B2B wholesale liquor distribution portal built on top of Frappe's `webshop` app. Developed by **NDF Tech Labs** for the **Dalali Wine Wholesaler** brand.

The app is a pure overlay — it uses Frappe's hook and template-override system and **does not modify any core `frappe/`, `webshop/`, or `erpnext/` files**.

---

## Features

- **Dalali brand theme** — claret + gold palette, dark navbar, full-bleed hero
- **Homepage** — hero search, 4-select filter strip, category grid, featured products, bundles section, promo banners
- **Catalog page (`/catalog`)** — left-sidebar (category tree, profile locator, dual-thumb price slider, brand directory) + 5-col dense product grid with pagination and active-filter pills
- **Product detail page (PDP)** — bottle/case unit toggle, wholesale price display, volume tier table & modal, wine/spirits metadata grid, **Add to Cart + Buy Now CTA buttons**, **Recommended Items grid**
- **Wholesale API** — volume pricing tiers, item metadata, bulk tier fetching, recommended items, category grid
- **Custom fields** — 10 wholesale/beverage fields on the `Item` doctype (varietal, region, vintage, ABV, case size, importer, etc.)
- **Catalog guard** — `Website Item` validate hook blocks accidental publishing of internal-operation items
- **Seed utilities** — item group tree, sample items/prices/bundles, promotional campaigns, image patching

---

## Requirements

- Frappe v17
- ERPNext (for Item, Item Price, Brand, Supplier doctypes)
- `webshop` app (declared as `required_apps`)

---

## Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app git@github.com:NdfTechLabs/dt_ecommerce.git --branch develop
bench --site <sitename> install-app dt_ecommerce
```

### Deploy custom fields

```bash
bench --site <sitename> import-fixtures --app dt_ecommerce
```

### Build frontend assets

```bash
bench build --app dt_ecommerce
bench --site <sitename> clear-cache
```

### Seed sample data (optional)

```bash
# 1. Build the Item Group tree first
bench --site <sitename> execute dt_ecommerce.restructure_groups.run

# 2. Create items, prices, bundles, and download product images
bench --site <sitename> execute dt_ecommerce.seed.run

# 3. Seed promotional campaigns and pricing rules
bench --site <sitename> execute dt_ecommerce.seed_campaigns.run

# 4. Patch website_image paths directly (bypasses tabFile validation)
bench --site <sitename> execute dt_ecommerce.fix_images.run
```

---

## Directory Structure

```
dt_ecommerce/
├── api/
│   └── wholesale.py          # Guest API: pricing tiers, item meta, recommendations, category grid
├── fixtures/
│   └── custom_field.json     # 10 custom fields on Item doctype
├── public/
│   ├── css/
│   │   ├── base.css
│   │   ├── theme_glass.css
│   │   └── theme_dalali.css  # Full brand theme + all component CSS
│   └── js/
│       ├── theme.js           # Navbar scroll + search typeahead
│       └── dalali.js          # All wholesale UI logic
├── templates/
│   └── generators/item/
│       └── item.html          # PDP override (shadows webshop template)
├── www/
│   ├── index.py / index.html  # Homepage context + template
│   └── catalog.py / catalog.html  # /catalog listing & filter page
├── catalog_guard.py           # Blocks internal items from webshop publishing
├── fix_images.py              # Direct DB image path patcher
├── hooks.py                   # All Frappe hook registrations
├── restructure_groups.py      # Builds two-branch Item Group tree
├── seed.py                    # Sample items, prices, bundles, images
├── seed_campaigns.py          # Sample campaigns + pricing rules
└── utils.py                   # Server-side context helpers (extend_dalali_context)
```

---

## Cache Busting

CSS/JS files are served with `Cache-Control: max-age=43200` by Frappe's dev server. When making changes, bump `_V` in `hooks.py` and rebuild:

```bash
bench build --app dt_ecommerce
bench --site <sitename> clear-cache
```

---

## Contributing

This app uses `pre-commit` for code formatting and linting. Install and enable it:

```bash
cd apps/dt_ecommerce
pre-commit install
```

Configured tools: `ruff`, `eslint`, `prettier`, `pyupgrade`.

---

## Documentation

Full implementation reference: [`DALALI_WEBSHOP.md`](DALALI_WEBSHOP.md)

Operational data guide: [`DALALI_DATA_GUIDE.md`](DALALI_DATA_GUIDE.md)

---

## License

agpl-3.0
