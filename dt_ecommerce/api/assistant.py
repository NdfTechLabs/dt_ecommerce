# Copyright (c) 2026, NDF Tech Labs and contributors
# For license information, please see license.txt

import frappe


def _load_assistant_config():
	settings = frappe.get_single("Webshop Assistant Settings")

	if not settings.enabled:
		return {
			"enabled": False,
		}

	return settings.get_config()

@frappe.whitelist(allow_guest=True)
def get_assistant_config():
	"""
	Load the webshop assistant configuration.

	This is the public entry point used by the webshop frontend.
	"""

	return _load_assistant_config()


def load_assistant():
	"""
	Load the enabled webshop assistant configuration.

	This function is intended for server-side page context loading.
	"""

	return _load_assistant_config()

def get_assistant_context():
    assistant = frappe.get_single("Webshop Assistant Settings")

    config = assistant.get_config()

    config["popular_categories"] = frappe.get_all(
        "Item Group",
        filters={
            "is_group": 0,
            "show_in_website": 1,
        },
        fields=[
            "name",
            "item_group_name",
            "route",
        ],
        order_by="item_group_name asc",
    )

    return config
