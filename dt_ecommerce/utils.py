import frappe


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
