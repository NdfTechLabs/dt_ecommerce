import frappe


def execute():
    fields = [
        {
            "fieldname": "custom_latitude",
            "label": "Latitude",
            "fieldtype": "Float",
            "insert_after": "links",
        },
        {
            "fieldname": "custom_longitude",
            "label": "Longitude",
            "fieldtype": "Float",
            "insert_after": "custom_latitude",
        },
        {
            "fieldname": "custom_delivery_location",
            "label": "Delivery Location",
            "fieldtype": "Geolocation",
            "insert_after": "custom_longitude",
        },
    ]

    for field in fields:
        if not frappe.db.exists(
            "Custom Field",
            {
                "dt": "Address",
                "fieldname": field["fieldname"],
            },
        ):
            frappe.get_doc(
                {
                    "doctype": "Custom Field",
                    "dt": "Address",
                    **field,
                }
            ).insert(ignore_permissions=True)

    frappe.db.commit()