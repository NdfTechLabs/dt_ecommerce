import frappe
from webshop.webshop.shopping_cart.cart import (
    get_party as original_get_party,
)

from dt_ecommerce.api.account_migration import (
    get_migration_customer,
)

def ensure_utm_record(doctype, value):
    """
    Ensure a UTM Source/Medium/Campaign record exists.

    The UTM doctypes use user-defined names, so the incoming
    UTM value becomes the document name.
    """
    if not value:
        return None

    if not frappe.db.exists(doctype, value):
        frappe.get_doc({
            "doctype": doctype,
            "name": value,
        }).insert(ignore_permissions=True)

    return value


@frappe.whitelist(allow_guest=True)
def create_lead_for_item_inquiry(lead, subject, message):
    lead = frappe.parse_json(lead)

    lead_doc = frappe.new_doc("Lead")

    # ---------------------------------------------------------
    # Contact Information
    # ---------------------------------------------------------

    for fieldname in (
        "lead_name",
        "company_name",
        "email_id",
        "phone",
    ):
        lead_doc.set(fieldname, lead.get(fieldname))

    lead_doc.set("lead_owner", "")

    # ---------------------------------------------------------
    # UTM Source
    # ---------------------------------------------------------

    utm_source = lead.get("utm_source")

    # If no UTM source was captured, use Product Inquiry.
    if not utm_source:
        utm_source = "Product Inquiry"

    ensure_utm_record(
        "UTM Source",
        utm_source
    )

    lead_doc.set("utm_source", utm_source)

    # ---------------------------------------------------------
    # UTM Medium
    # ---------------------------------------------------------

    utm_medium = lead.get("utm_medium")

    if utm_medium:
        ensure_utm_record(
            "UTM Medium",
            utm_medium
        )

        lead_doc.set("utm_medium", utm_medium)

    # ---------------------------------------------------------
    # UTM Campaign
    # ---------------------------------------------------------

    utm_campaign = lead.get("utm_campaign")

    if utm_campaign:
        ensure_utm_record(
            "UTM Campaign",
            utm_campaign
        )

        lead_doc.set("utm_campaign", utm_campaign)

    # ---------------------------------------------------------
    # UTM Content
    #
    # This is a Data field, so it does NOT need a DocType.
    # ---------------------------------------------------------

    utm_content = lead.get("utm_content")

    if utm_content:
        lead_doc.set("utm_content", utm_content)

    # ---------------------------------------------------------
    # UTM Term
    #
    # This is also a Data field.
    # ---------------------------------------------------------

    # utm_term = lead.get("utm_term")

    # if utm_term:
    #     lead_doc.set("utm_term", utm_term)

    # ---------------------------------------------------------
    # Save Lead
    # ---------------------------------------------------------

    try:
        lead_doc.save(ignore_permissions=True)

    except frappe.exceptions.DuplicateEntryError:
        frappe.clear_messages()

        lead_doc = frappe.get_doc(
            "Lead",
            {"email_id": lead["email_id"]}
        )

    # ---------------------------------------------------------
    # Add Inquiry Comment
    # ---------------------------------------------------------

    lead_doc.add_comment(
        "Comment",
        text="""
            <div>
                <h5>{subject}</h5>
                <p>{message}</p>
            </div>
        """.format(
            subject=subject,
            message=message
        ),
    )

    return lead_doc

def get_party(user=None):
    migration_customer = get_migration_customer()

    if migration_customer:
        return migration_customer

    return original_get_party(user)
