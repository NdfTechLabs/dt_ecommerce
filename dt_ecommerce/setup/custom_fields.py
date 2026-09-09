import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def setup_storefront_custom_fields():
    custom_fields = {
        "Promotional Scheme": [
            {
                "fieldname": "custom_show_in_hero",
                "label": "Show in Hero Slider",
                "fieldtype": "Check",
                "insert_after": "product_discount_slabs",
                "default": 0,
            },
            {
                "fieldname": "custom_hero_image",
                "label": "Hero Image",
                "fieldtype": "Attach Image",
                "insert_after": "custom_show_in_hero",
            },
            {
                "fieldname": "custom_hero_title",
                "label": "Hero Title",
                "fieldtype": "Data",
                "insert_after": "custom_hero_image",
            },
            {
                "fieldname": "custom_hero_subtitle",
                "label": "Hero Subtitle",
                "fieldtype": "Small Text",
                "insert_after": "custom_hero_title",
            },
            {
                "fieldname": "custom_hero_button_label",
                "label": "Hero Button Label",
                "fieldtype": "Data",
                "insert_after": "custom_hero_subtitle",
            },
            {
                "fieldname": "custom_hero_button_url",
                "label": "Hero Button URL",
                "fieldtype": "Data",
                "options": "URL",
                "insert_after": "custom_hero_button_label",
            },
            {
                "fieldname": "custom_hero_priority",
                "label": "Hero Priority",
                "fieldtype": "Int",
                "insert_after": "custom_hero_button_url",
                "default": 0,
            },
        ],

        "Campaign": [
            {
                "fieldname": "custom_show_in_hero",
                "label": "Show in Hero Slider",
                "fieldtype": "Check",
                "insert_after": "description",
                "default": 0,
            },
            {
                "fieldname": "custom_hero_image",
                "label": "Hero Image",
                "fieldtype": "Attach Image",
                "insert_after": "custom_show_in_hero",
            },
            {
                "fieldname": "custom_hero_title",
                "label": "Hero Title",
                "fieldtype": "Data",
                "insert_after": "custom_hero_image",
            },
            {
                "fieldname": "custom_hero_subtitle",
                "label": "Hero Subtitle",
                "fieldtype": "Small Text",
                "insert_after": "custom_hero_title",
            },
            {
                "fieldname": "custom_hero_button_label",
                "label": "Hero Button Label",
                "fieldtype": "Data",
                "insert_after": "custom_hero_subtitle",
            },
            {
                "fieldname": "custom_hero_button_url",
                "label": "Hero Button URL",
                "fieldtype": "Data",
                "options": "URL",
                "insert_after": "custom_hero_button_label",
            },
            {
                "fieldname": "custom_hero_priority",
                "label": "Hero Priority",
                "fieldtype": "Int",
                "insert_after": "custom_hero_button_url",
                "default": 0,
            },
        ],
    }

    create_custom_fields(custom_fields, update=True)