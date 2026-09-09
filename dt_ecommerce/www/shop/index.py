import frappe
import json


def get_context(context):
    context.no_cache = 0
    context.full_width = 1        # remove Bootstrap container from <main> so hero spans full viewport

    slides = []

    # ---------------------------------------------------------
    # Promotional Scheme Heroes
    # ---------------------------------------------------------

    promotional_schemes = frappe.get_all(
        "Promotional Scheme",
        filters={
            "custom_show_in_hero": 1,
            "disable": 0,
        },
        fields=[
            "name",
            "custom_hero_image",
            "custom_hero_title",
            "custom_hero_subtitle",
            "custom_hero_button_label",
            "custom_hero_button_url",
            "custom_hero_priority",
        ],
        order_by="custom_hero_priority asc",
    )

    for promotion in promotional_schemes:
        slides.append({
            "source": "promotional_scheme",
            "name": promotion.name,
            "image": promotion.custom_hero_image,
            "title": promotion.custom_hero_title or promotion.name,
            "subtitle": promotion.custom_hero_subtitle,
            "action": promotion.custom_hero_button_url,
            "label": promotion.custom_hero_button_label or "Shop Now",
            "priority": promotion.custom_hero_priority or 0,
        })

    # ---------------------------------------------------------
    # Campaign Heroes
    # ---------------------------------------------------------

    campaigns = frappe.get_all(
        "Campaign",
        filters={
            "custom_show_in_hero": 1,
        },
        fields=[
            "name",
            "campaign_name",
            "custom_hero_image",
            "custom_hero_title",
            "custom_hero_subtitle",
            "custom_hero_button_label",
            "custom_hero_button_url",
            "custom_hero_priority",
        ],
        order_by="custom_hero_priority asc",
    )

    for campaign in campaigns:
        slides.append({
            "source": "campaign",
            "name": campaign.name,
            "image": campaign.custom_hero_image,
            "title": campaign.custom_hero_title or campaign.campaign_name,
            "subtitle": campaign.custom_hero_subtitle,
            "action": campaign.custom_hero_button_url,
            "label": campaign.custom_hero_button_label or "Shop Now",
            "priority": campaign.custom_hero_priority or 0,
        })

    # ---------------------------------------------------------
    # Sort all hero slides together
    # ---------------------------------------------------------

    slides.sort(key=lambda slide: slide["priority"])

    context.slides = slides

    try:
         config = frappe.get_all(
                "Homepage Configuration Section",
                fields=[
                    "section_id",
                    "source",
                    "value",
                    "limit",
                    "title",
                    "image",
                    "video",
                    "media_type",
                ]
            )

         context.homepage_sections = [
                {
                    "section_id": row.section_id,
                    "source": row.source,
                    "value": row.value,
                    "limit": row.limit or 6,
                    "title": row.title or "",
                    "image": row.image or "",
                    "video": row.video or "",
                    "media_type": row.media_type or "Image",
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