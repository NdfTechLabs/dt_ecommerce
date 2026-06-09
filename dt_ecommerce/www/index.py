import json

import frappe
from frappe.utils import quote, flt


def get_context(context):
	context.full_width = 1        # remove Bootstrap container from <main> so hero spans full viewport
	context.no_breadcrumbs = 1    # suppress the breadcrumb bar above the hero

	# Filter matrix dropdowns
	context.categories = frappe.get_all(
		"Item Group",
		filters={"is_group": 0, "show_in_website": 1},
		fields=["name", "item_group_name"],
		order_by="item_group_name asc",
	)

	context.brands = frappe.get_all(
		"Brand",
		fields=["name"],
		order_by="name asc",
	)

	# Category grid cards (up to 8, with images and browse URLs)
	groups = frappe.get_all(
		"Item Group",
		filters={"show_in_website": 1, "is_group": 0},
		fields=["name", "item_group_name", "route", "image"], #, "website_image"
		order_by="name asc",
		limit_page_length=8,
	)
	for g in groups:
		g["image_url"] = g.get("website_image") or g.get("image") or ""
		g["url"] = f"/catalog?item_group={quote(g['name'])}"
	context.category_grid = groups

	try:
		context.regions = frappe.get_all(
			"Liquor Region",
			fields=["name"],
			order_by="name asc",
		)
	except frappe.DoesNotExistError:
		rows = frappe.db.sql(
			"SELECT DISTINCT custom_region FROM `tabItem` "
			"WHERE custom_region IS NOT NULL AND custom_region != '' "
			"ORDER BY custom_region ASC"
		)
		context.regions = [{"name": r[0]} for r in rows]

	# Distinct wine/spirit varietal values from Item master
	varietal_rows = frappe.db.sql(
		"SELECT DISTINCT custom_wine_varietal FROM `tabItem` "
		"WHERE custom_wine_varietal IS NOT NULL AND custom_wine_varietal != '' "
		"ORDER BY custom_wine_varietal ASC"
	)
	context.varietals = [{"name": r[0]} for r in varietal_rows]

	# Active promotional banners — sourced from live Pricing Rules
	# Note: the `campaign` Link field on Pricing Rule is cleared by the ERPNext
	# controller (cleanup_fields_value) when applicable_for is blank.
	# We query active rules directly by date range + priority instead.
	promo_banners = []
	try:
		rows = frappe.db.sql(
			"""
			SELECT DISTINCT pr.title,
			       pr.discount_percentage, pr.discount_amount,
			       pr.valid_upto, pr.priority
			FROM `tabPricing Rule` pr
			WHERE pr.selling = 1
			  AND pr.disable = 0
			  AND pr.apply_on = 'Item Group'
			  AND (pr.valid_upto IS NULL OR pr.valid_upto >= CURDATE())
			  AND (pr.valid_from  IS NULL OR pr.valid_from  <= CURDATE())
			ORDER BY pr.priority DESC, pr.creation DESC
			LIMIT 4
			""",
			as_dict=True,
		)
		for r in rows:
			badge = ""
			if r.discount_percentage:
				badge = f"{int(r.discount_percentage)}% OFF"
			elif r.discount_amount:
				badge = f"KES {int(flt(r.discount_amount)):,} OFF"
			promo_banners.append({
				"title": r.title,
				"badge": badge,
				"valid_upto": str(r.valid_upto) if r.valid_upto else "",
			})
	except Exception:
		pass
	context.promo_banners = promo_banners

	# Featured products for the tiered pricing cards section (up to 8, ranked)
	web_items = frappe.get_all(
		"Website Item",
		filters={"published": 1},
		fields=["item_code", "web_item_name", "website_image", "item_group", "route"],
		order_by="ranking desc, modified asc",
		limit_page_length=8,
	)
	for item in web_items:
		price_data = frappe.db.get_value(
			"Item Price",
			{"item_code": item["item_code"], "selling": 1},
			["price_list_rate", "currency"],
			as_dict=True,
		) or {}
		item["price"] = flt(price_data.get("price_list_rate") or 0)
		item["currency"] = price_data.get("currency") or "KES"
		item["case_size"] = int(
			frappe.db.get_value("Item", item["item_code"], "custom_case_size") or 12
		)
		item["url"] = f"/{item['route']}" if item.get("route") else "#"
	context.featured_products = web_items

	# Curated Wholesale Bundles — Product Bundle records with a published Website Item
	bundles = []
	try:
		pb_records = frappe.get_all(
			"Product Bundle",
			fields=["name", "new_item_code", "description"],
			limit_page_length=6,
		)
		for pb in pb_records:
			wi = frappe.db.get_value(
				"Website Item",
				{"item_code": pb["new_item_code"], "published": 1},
				["web_item_name", "website_image", "route"],
				as_dict=True,
			)
			if not wi:
				continue
			component_count = frappe.db.count(
				"Product Bundle Item",
				{"parent": pb["name"]},
			)
			price_data = frappe.db.get_value(
				"Item Price",
				{"item_code": pb["new_item_code"], "selling": 1},
				["price_list_rate", "currency"],
				as_dict=True,
			) or {}
			bundles.append({
				"item_code": pb["new_item_code"],
				"title": wi["web_item_name"],
				"image": wi.get("website_image") or "",
				"url": f"/{wi['route']}" if wi.get("route") else "#",
				"description": (pb.get("description") or "")[:120],
				"item_count": component_count,
				"price": flt(price_data.get("price_list_rate") or 0),
				"currency": price_data.get("currency") or "KES",
			})
	except Exception:
		pass
	context.wholesale_bundles = bundles

	try:
		config = frappe.get_all(
			"Homepage Configuration Section",
			fields=[
				"section_id",
				"source",
				"value",
				"limit",
				"title"
			]
		)

		context.homepage_sections = [
			{
				"section_id": row.section_id,
				"source": row.source,
				"value": row.value,
				"limit": row.limit or 6,
				"title": getattr(row, "title", ""),
			}
			for row in config
			if row.section_id
		]

		context.homepage_sections_json = json.dumps(
			context.homepage_sections
		)

	except Exception:
		context.homepage_sections = []
		context.homepage_sections_json = "[]"

	return context
