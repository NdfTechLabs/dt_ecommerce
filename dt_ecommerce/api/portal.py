# dt_ecommerce/api/portal.py

import frappe

from erpnext.portal import utils as portal_utils
from dt_ecommerce.api.account_migration import get_migration_customer

original_create_customer_or_supplier = (
    portal_utils.create_customer_or_supplier
)


def link_migration_user_to_customer(customer):
    user = frappe.session.user

    contact_name = customer.customer_primary_contact

    if not contact_name:
        return

    contact = frappe.get_doc("Contact", contact_name)

    # Attach the new Frappe user
    contact.user = user

    # Use the signup email as the Contact email
    contact.email_id = user

    # Keep Email IDs child table in sync
    existing_email = next(
        (
            row
            for row in contact.email_ids
            if row.email_id == user
        ),
        None,
    )

    if existing_email:
        existing_email.is_primary = True
    else:
        contact.append(
            "email_ids",
            {
                "email_id": user,
                "is_primary": True,
            },
        )

    contact.save(ignore_permissions=True)

def create_customer_or_supplier():
    migration_customer = get_migration_customer()

    if migration_customer:
        link_migration_user_to_customer(migration_customer)
        return migration_customer

    return original_create_customer_or_supplier()