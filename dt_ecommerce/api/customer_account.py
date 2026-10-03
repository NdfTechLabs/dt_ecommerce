
import frappe
from frappe import _

CUSTOMER_EDITABLE_FIELDS = {
    "customer_name",
    "first_name",
    "last_name",
    "mobile_no",
    "email_id",
    "language",
}

def get_customer_for_user(user):
    if not user or user == "Guest":
        return None

    customer_name = frappe.db.get_value(
        "Portal User",
        {
            "user": user,
            "parenttype": "Customer",
        },
        "parent",
    )

    if not customer_name:
        return None

    return frappe.get_doc("Customer", customer_name)

@frappe.whitelist()
def update_customer_profile(customer_name, data):
    """
    Update the customer-editable fields from the customer portal.

    Only explicitly whitelisted fields can be changed.
    """

    customer = get_customer_for_user(frappe.session.user)

    if not customer:
        frappe.throw(_("No customer account is associated with your user."))

    if customer.name != customer_name:
        frappe.throw(_("You do not have access to this customer account."))

    if customer.disabled or customer.is_frozen:
        frappe.throw(_("This customer account cannot be edited."))

    if not (customer.get("custom_allow_portal_editing") if customer.get("custom_allow_portal_editing") else True):
        frappe.throw(_("Customer profile editing is not enabled."))

    data = frappe.parse_json(data)

    for fieldname in CUSTOMER_EDITABLE_FIELDS:
        if fieldname in data:
            customer.set(
                fieldname,
                data[fieldname]
            )

    customer.save()

    return {
        "success": True,
        "customer": {
            "name": customer.name,
            "customer_name": customer.customer_name,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "email": customer.email_id,
            "mobile": customer.mobile_no,
            "language": customer.language,
        },
    }

@frappe.whitelist()
def get_customer_contacts(customer_name):
    """
    Get all contacts associated with the customer.

    Only contacts belonging to the authenticated customer's
    account are returned.
    """

    customer = get_customer_for_user(frappe.session.user)

    if not customer:
        frappe.throw(
            _("No customer account is associated with your user.")
        )

    if customer.name != customer_name:
        frappe.throw(
            _("You do not have access to this customer account.")
        )

    contact_names = frappe.get_all(
        "Dynamic Link",
        filters={
            "link_doctype": "Customer",
            "link_name": customer.name,
            "parenttype": "Contact",
        },
        pluck="parent",
    )

    if not contact_names:
        return {
            "success": True,
            "contacts": [],
        }

    contacts = frappe.get_all(
        "Contact",
        filters={
            "name": ["in", contact_names],
        },
        fields=[
            "name",
            "first_name",
            "middle_name",
            "last_name",
            "full_name",
            "email_id",
            "phone",
            "mobile_no",
            "is_primary_contact",
            "is_billing_contact",
        ],
        order_by="is_primary_contact desc, full_name asc",
    )

    return {
        "success": True,
        "contacts": contacts,
    }

def _get_customer_for_contact_operation(customer_name):
    """
    Return the authenticated customer's document after verifying access.
    """

    customer = get_customer_for_user(frappe.session.user)

    if not customer:
        frappe.throw(
            _("No customer account is associated with your user.")
        )

    if customer.name != customer_name:
        frappe.throw(
            _("You do not have access to this customer account.")
        )

    if customer.disabled or customer.is_frozen:
        frappe.throw(
            _("This customer account cannot be modified.")
        )

    return customer


def _get_customer_contact(customer_name, contact_name):
    """
    Get a Contact only if it is actually linked to the given Customer.
    """

    customer = _get_customer_for_contact_operation(
        customer_name
    )

    linked = frappe.db.exists(
        "Dynamic Link",
        {
            "parent": contact_name,
            "parenttype": "Contact",
            "link_doctype": "Customer",
            "link_name": customer.name,
        },
    )

    if not linked:
        frappe.throw(
            _("This contact does not belong to this customer account.")
        )

    return customer, frappe.get_doc(
        "Contact",
        contact_name,
    )

@frappe.whitelist()
def create_customer_contact(customer_name, data):
    """
    Create a new Contact and associate it with the customer.
    """

    customer = _get_customer_for_contact_operation(
        customer_name
    )

    data = frappe.parse_json(data)

    first_name = (data.get("first_name") or "").strip()
    middle_name = (data.get("middle_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    email = (data.get("email_id") or "").strip()
    mobile = (data.get("mobile_no") or "").strip()
    phone = (data.get("phone") or "").strip()

    if not first_name:
        frappe.throw(
            _("First name is required.")
        )

    contact = frappe.new_doc("Contact")

    contact.first_name = first_name
    contact.middle_name = middle_name
    contact.last_name = last_name

    contact.append(
        "links",
        {
            "link_doctype": "Customer",
            "link_name": customer.name,
        },
    )

    if email:
        contact.add_email(
            email,
            is_primary=True,
        )

    if mobile:
        contact.add_phone(
            mobile,
            is_primary_mobile_no=True,
        )

    if phone:
        contact.add_phone(
            phone,
            is_primary_phone=True,
        )

    contact.insert()

    return {
        "success": True,
        "contact": {
            "name": contact.name,
            "first_name": contact.first_name,
            "middle_name": contact.middle_name,
            "last_name": contact.last_name,
            "full_name": contact.full_name,
            "email_id": contact.email_id,
            "phone": contact.phone,
            "mobile_no": contact.mobile_no,
            "is_primary_contact": contact.is_primary_contact,
            "is_billing_contact": contact.is_billing_contact,
        },
    }

@frappe.whitelist()
def remove_customer_contact(customer_name, contact_name):
    """
    Remove the Contact ↔ Customer association.

    The customer's primary contact cannot be removed.
    The Contact document itself is not deleted.
    """

    customer, contact = _get_customer_contact(
        customer_name,
        contact_name,
    )

    # A customer must always retain a primary contact.
    if customer.customer_primary_contact == contact.name:
        frappe.throw(
            _("The primary contact cannot be removed. "
              "Please assign another contact as primary first.")
        )

    # Remove only this customer's Dynamic Link.
    frappe.db.delete(
        "Dynamic Link",
        {
            "parent": contact.name,
            "parenttype": "Contact",
            "link_doctype": "Customer",
            "link_name": customer.name,
        },
    )

    return {
        "success": True,
        "contact_name": contact.name,
    }


@frappe.whitelist()
def make_customer_contact_primary(
    customer_name,
    contact_name,
):
    """
    Make a Contact the primary contact for the Customer.

    The existing primary contact is automatically changed
    to a normal contact.
    """

    customer, contact = _get_customer_contact(
        customer_name,
        contact_name,
    )

    # Already primary.
    if customer.customer_primary_contact == contact.name:
        return {
            "success": True,
            "primary_contact": {
                "name": contact.name,
                "full_name": contact.full_name,
                "email_id": contact.email_id,
                "mobile_no": contact.mobile_no,
            },
        }

    # Get the current primary contact, if one exists.
    previous_contact = None

    if customer.customer_primary_contact:

        previous_contact = frappe.get_doc(
            "Contact",
            customer.customer_primary_contact,
        )

        previous_contact.db_set(
            "is_primary_contact",
            0,
        )

    # Set the new contact as primary.
    contact.db_set(
        "is_primary_contact",
        1,
    )

    # Update Customer's primary contact.
    customer.db_set(
        "customer_primary_contact",
        contact.name,
    )

    # Keep Customer's derived contact information synchronized.
    customer.db_set(
        "email_id",
        contact.email_id or "",
    )

    customer.db_set(
        "mobile_no",
        contact.mobile_no or "",
    )

    frappe.db.commit()

    return {
        "success": True,
        "primary_contact": {
            "name": contact.name,
            "full_name": contact.full_name,
            "email_id": contact.email_id,
            "mobile_no": contact.mobile_no,
        },
    }


@frappe.whitelist()
def remove_customer_contact_primary(
    customer_name,
    contact_name,
):
    """
    A customer's primary contact cannot simply be unset.

    The primary designation can only be changed by selecting
    another contact as primary.
    """

    customer, contact = _get_customer_contact(
        customer_name,
        contact_name,
    )

    if customer.customer_primary_contact != contact.name:
        return {
            "success": True,
            "already_primary": False,
        }

    frappe.throw(
        _("A customer must always have a primary contact. "
          "Please select another contact as primary instead.")
    )

@frappe.whitelist()
def update_customer_contact(customer_name, contact_name, data):
    """
    Update a Contact belonging to the current Customer.

    Only explicitly allowed contact fields can be modified.
    """

    customer, contact = _get_customer_contact(
        customer_name,
        contact_name,
    )

    data = frappe.parse_json(data)

    first_name = (data.get("first_name") or "").strip()
    middle_name = (data.get("middle_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    email = (data.get("email_id") or "").strip()
    mobile = (data.get("mobile_no") or "").strip()
    phone = (data.get("phone") or "").strip()

    if not first_name:
        frappe.throw(
            _("First name is required.")
        )

    contact.first_name = first_name
    contact.middle_name = middle_name
    contact.last_name = last_name

    # Clear existing email/phone values that are
    # managed by this portal before rebuilding them.
    contact.set("email_ids", [])
    contact.set("phone_nos", [])

    if email:
        contact.add_email(
            email,
            is_primary=True,
        )

    if mobile:
        contact.add_phone(
            mobile,
            is_primary_mobile=True,
        )

    if phone:
        contact.add_phone(
            phone,
            is_primary_phone=True,
        )

    contact.save()

    # Keep Customer's derived contact information
    # synchronized when editing its primary contact.
    if customer.customer_primary_contact == contact.name:

        customer.db_set(
            "email_id",
            contact.email_id or "",
        )

        customer.db_set(
            "mobile_no",
            contact.mobile_no or "",
        )

    return {
        "success": True,
        "contact": {
            "name": contact.name,
            "first_name": contact.first_name,
            "middle_name": contact.middle_name,
            "last_name": contact.last_name,
            "full_name": contact.full_name,
            "email_id": contact.email_id,
            "phone": contact.phone,
            "mobile_no": contact.mobile_no,
            "is_primary_contact": contact.is_primary_contact,
            "is_billing_contact": contact.is_billing_contact,
        },
    }

@frappe.whitelist()
def get_customer_contact(customer_name, contact_name):
    """
    Get a Contact belonging to the current Customer.
    """

    customer, contact = _get_customer_contact(
        customer_name,
        contact_name,
    )

    return {
        "success": True,
        "contact": {
            "name": contact.name,
            "first_name": contact.first_name,
            "middle_name": contact.middle_name,
            "last_name": contact.last_name,
            "full_name": contact.full_name,
            "email_id": contact.email_id,
            "phone": contact.phone,
            "mobile_no": contact.mobile_no,
            "is_primary_contact": contact.is_primary_contact,
            "is_billing_contact": contact.is_billing_contact,
        },
    }

# =========================================================
# Customer Dashboard
# =========================================================

DASHBOARD_LIMIT = 5


def _get_dashboard_customer(customer_name=None):
    """
    Resolve the customer associated with the current user.

    If customer_name is supplied, make sure the user actually
    has access to that customer.
    """

    customer = get_customer_for_user(frappe.session.user)

    if not customer:
        frappe.throw(
            _("No customer account is associated with your user.")
        )

    if customer_name and customer.name != customer_name:
        frappe.throw(
            _("You do not have access to this customer account.")
        )

    return customer


# =========================================================
# Customer summary
# =========================================================

def get_customer_dashboard_summary(customer):
    """
    Return the customer information required by the dashboard.
    """

    return {
        "name": customer.name,
        "customer_name": customer.customer_name,
        "customer_type": customer.customer_type,
        "customer_group": customer.customer_group,
        "territory": customer.territory,
        "disabled": bool(customer.disabled),
        "is_frozen": bool(customer.is_frozen),
        "email": customer.email_id,
        "mobile": customer.mobile_no,
        "language": customer.language,
        "primary_contact": customer.customer_primary_contact,
    }


# =========================================================
# Orders
# =========================================================

def get_customer_dashboard_orders(customer):
    """
    Get the 5 most recent Sales Orders belonging to the customer.
    """

    orders = frappe.get_all(
        "Sales Order",
        filters={
            "customer": customer.name,
        },
        fields=[
            "name",
            "transaction_date",
            "grand_total",
            "currency",
            "status",
            "per_delivered",
            "per_billed",
        ],
        order_by="transaction_date desc, creation desc",
        limit_page_length=DASHBOARD_LIMIT,
    )

    for order in orders:
        order["url"] = f"/orders/{frappe.utils.quote(order.name)}"

    return {
        "items": orders,
        "count": frappe.db.count(
            "Sales Order",
            {
                "customer": customer.name,
            },
        ),
        "more_url": "/orders",
    }


# =========================================================
# Addresses
# =========================================================

def get_customer_dashboard_addresses(customer):
    """
    Get the 5 most recently modified addresses belonging
    to the customer.
    """

    address_names = frappe.get_all(
        "Dynamic Link",
        filters={
            "parenttype": "Address",
            "link_doctype": "Customer",
            "link_name": customer.name,
        },
        pluck="parent",
    )

    if not address_names:
        return {
            "items": [],
            "count": 0,
            "more_url": "/address/list",
        }

    addresses = frappe.get_all(
        "Address",
        filters={
            "name": ["in", address_names],
        },
        fields=[
            "name",
            "address_title",
            "address_type",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "country",
            "pincode",
            "phone",
            "email_id",
            "is_primary_address",
            "is_shipping_address",
            "modified",
        ],
        order_by="modified desc",
        limit_page_length=DASHBOARD_LIMIT,
    )

    for address in addresses:
        address["url"] = (
            f"/address/{frappe.utils.quote(address.name)}"
        )

    return {
        "items": addresses,
        "count": len(address_names),
        "more_url": "/address/list",
    }


# =========================================================
# Shipments
# =========================================================

def get_customer_dashboard_shipments(customer):
    """
    Get the 5 most recent Delivery Notes belonging to the customer.
    """

    shipments = frappe.get_all(
        "Delivery Note",
        filters={
            "customer": customer.name,
        },
        fields=[
            "name",
            "posting_date",
            "status",
            "grand_total",
            "currency",
        ],
        order_by="posting_date desc, creation desc",
        limit_page_length=DASHBOARD_LIMIT,
    )

    for shipment in shipments:
        shipment["url"] = (
            f"/shipments/{frappe.utils.quote(shipment.name)}"
        )

    return {
        "items": shipments,
        "count": frappe.db.count(
            "Delivery Note",
            {
                "customer": customer.name,
            },
        ),
        "more_url": "/shipments",
    }

def get_customer_dashboard_data(customer_name=None):
    """
    Build the complete customer dashboard payload.
    """

    customer = _get_dashboard_customer(customer_name)

    return {
        "customer": get_customer_dashboard_summary(customer),
        "orders": get_customer_dashboard_orders(customer),
        "addresses": get_customer_dashboard_addresses(customer),
        "shipments": get_customer_dashboard_shipments(customer),
    }


@frappe.whitelist()
def get_customer_dashboard(customer_name=None):
    """
    API endpoint for the customer dashboard.
    """

    return {
        "success": True,
        "data": get_customer_dashboard_data(customer_name),
    }

