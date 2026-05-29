import frappe


@frappe.whitelist(allow_guest=True)
def get_pricing_tiers(item_code: str) -> list[dict]:
	"""Return volume-discount tiers from active Pricing Rules for an item.

	Returns rows sorted ascending by min_qty so the frontend can render a tier table.
	Only rules that carry a meaningful discount, amount, or fixed rate are returned.
	"""
	tiers = frappe.db.sql(
		"""
		SELECT
			pr.min_qty,
			pr.max_qty,
			pr.discount_percentage,
			pr.discount_amount,
			pr.rate,
			pr.price_or_product_discount
		FROM `tabPricing Rule` pr
		INNER JOIN `tabPricing Rule Item Code` pric ON pric.parent = pr.name
		WHERE
			pric.item_code = %(item_code)s
			AND pr.disable = 0
			AND pr.selling = 1
			AND (pr.valid_upto IS NULL OR pr.valid_upto >= CURDATE())
			AND (pr.valid_from  IS NULL OR pr.valid_from  <= CURDATE())
		ORDER BY pr.min_qty ASC
		""",
		{"item_code": item_code},
		as_dict=True,
	)

	return [
		t for t in tiers
		if t.get("discount_percentage") or t.get("discount_amount") or t.get("rate")
	]


@frappe.whitelist(allow_guest=True)
def get_item_wholesale_meta(item_code: str) -> dict:
	"""Return wholesale and beverage metadata stored on the Item master."""
	fields = [
		"custom_liquor_category",
		"custom_wine_varietal",
		"custom_origin_country",
		"custom_region",
		"custom_vintage_year",
		"custom_alcohol_content",
		"custom_case_size",
		"custom_importer",
	]
	data: dict = frappe.db.get_value("Item", item_code, fields, as_dict=True) or {}

	if data.get("custom_importer"):
		data["custom_importer_name"] = (
			frappe.db.get_value("Supplier", data["custom_importer"], "supplier_name")
			or data["custom_importer"]
		)
	else:
		data["custom_importer_name"] = None

	return data


@frappe.whitelist(allow_guest=True)
def get_bulk_pricing_tiers(item_codes: str | None = None):
	"""Return the single best pricing tier per item for a list of item codes.

	item_codes: JSON-encoded list of item code strings.
	Returns: {item_code: {min_qty, discount_percentage, discount_amount, rate}}
	Used by the product card grid to show a tier badge without N individual calls.
	"""
	import json

	if not item_codes:
		return {}

	try:
		codes = json.loads(item_codes) if isinstance(item_codes, str) else list(item_codes)
	except (ValueError, TypeError):
		return {}

	if not codes:
		return {}

	escaped = ", ".join([frappe.db.escape(c) for c in codes])

	rows = frappe.db.sql(
		f"""
		SELECT
			pric.item_code,
			pr.min_qty,
			pr.max_qty,
			pr.discount_percentage,
			pr.discount_amount,
			pr.rate
		FROM `tabPricing Rule` pr
		INNER JOIN `tabPricing Rule Item Code` pric ON pric.parent = pr.name
		WHERE
			pric.item_code IN ({escaped})
			AND pr.disable = 0
			AND pr.selling = 1
			AND (pr.valid_upto IS NULL OR pr.valid_upto >= CURDATE())
			AND (pr.valid_from  IS NULL OR pr.valid_from  <= CURDATE())
			AND (pr.discount_percentage > 0 OR pr.discount_amount > 0 OR pr.rate > 0)
		ORDER BY pric.item_code ASC, pr.min_qty DESC
		""",
		as_dict=True,
	)

	# Keep only the highest-min_qty (best) tier per item
	best: dict = {}
	for row in rows:
		if row["item_code"] not in best:
			best[row["item_code"]] = row

	return best


@frappe.whitelist(allow_guest=True)
def get_recommended_items(item_code: str, limit: int = 8) -> list[dict]:
	"""Return items similar to item_code (same group > same brand > same region).

	Scores each candidate: +4 same group, +2 same brand, +1 same region.
	Returns up to `limit` items ordered by score DESC, ranking DESC.
	"""
	item_data = frappe.db.get_value(
		"Item", item_code,
		["item_group", "brand", "custom_region"],
		as_dict=True,
	) or {}

	group  = item_data.get("item_group") or ""
	brand  = item_data.get("brand") or ""
	region = item_data.get("custom_region") or ""

	if not group and not brand and not region:
		return []

	rows = frappe.db.sql(
		"""
		SELECT
			wi.item_code, wi.web_item_name, wi.website_image,
			wi.item_group, wi.route,
			i.brand, i.custom_case_size,
			COALESCE(ip.price_list_rate, 0)  AS price,
			COALESCE(ip.currency, 'KES')     AS currency,
			(
				  CASE WHEN i.item_group = %(group)s  AND %(group)s  != '' THEN 4 ELSE 0 END
				+ CASE WHEN i.brand       = %(brand)s  AND %(brand)s  != '' THEN 2 ELSE 0 END
				+ CASE WHEN i.custom_region = %(region)s AND %(region)s != '' THEN 1 ELSE 0 END
			) AS relevance
		FROM `tabWebsite Item` wi
		INNER JOIN `tabItem` i ON i.name = wi.item_code
		LEFT JOIN `tabItem Price` ip
			ON ip.item_code = wi.item_code
		   AND ip.selling = 1
		   AND ip.price_list = 'Standard Selling'
		WHERE wi.published = 1
		  AND wi.item_code != %(item_code)s
		  AND (
			  (%(group)s  != '' AND i.item_group   = %(group)s)
			  OR (%(brand)s  != '' AND i.brand       = %(brand)s)
			  OR (%(region)s != '' AND i.custom_region = %(region)s)
		  )
		ORDER BY relevance DESC, wi.ranking DESC, wi.modified DESC
		LIMIT %(limit)s
		""",
		{
			"item_code": item_code,
			"group":     group,
			"brand":     brand,
			"region":    region,
			"limit":     int(limit),
		},
		as_dict=True,
	)

	for r in rows:
		r["url"]        = f"/{r['route']}" if r.get("route") else "#"
		case_sz         = int(r.get("custom_case_size") or 12)
		bottle          = float(r.get("price") or 0)
		r["case_size"]  = case_sz
		r["case_price"] = bottle * case_sz

	return rows


@frappe.whitelist(allow_guest=True)
def get_category_grid(limit: int = 8) -> list[dict]:
	"""Return Item Groups visible on the website for the category grid."""
	groups = frappe.db.get_all(
		"Item Group",
		filters={"show_in_website": 1, "is_group": 0},
		fields=["name", "route", "website_image", "image"],
		order_by="name asc",
		limit_page_length=int(limit),
	)

	for g in groups:
		g["image_url"] = g.get("website_image") or g.get("image") or ""
		g["url"] = f"/all-products?item_group={frappe.utils.quote(g['name'])}"

	return groups
