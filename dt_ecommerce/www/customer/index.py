import hashlib
import secrets

import frappe
from frappe import _
from frappe.utils import add_to_date, now_datetime
from http.cookies import SimpleCookie

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

def get_customer_status(customer):
    """
    Return the customer-facing status of the Customer account.
    """

    if customer.disabled:
        return {
            "state": "disabled",
            "label": _("Account disabled"),
            "description": _("This customer account has been disabled."),
        }

    if customer.is_frozen:
        return {
            "state": "frozen",
            "label": _("Account restricted"),
            "description": _("This customer account is currently restricted."),
        }

    return {
        "state": "active",
        "label": _("Account active"),
        "description": _("Your customer account is active."),
    }

def get_context(context):
    """
    Customer portal entry point.

    URL:
        /customer?name=CUST-00001&identifier=email_or_phone

    The URL parameters are used to start the access/onboarding flow.

    They are NOT sufficient to authorize access to the Customer.
    """

    context.no_cache = 1
    context.show_sidebar = False
    context.full_width = 1

    customer_name = frappe.form_dict.get("name")
    identifier = frappe.form_dict.get("identifier")

    # ------------------------------------------------------------------
    # 1. Determine authentication state
    # ------------------------------------------------------------------

    user = frappe.session.user
    authenticated = user != "Guest"

    context.authenticated = authenticated
    context.user = user

    # ------------------------------------------------------------------
    # 2. Resolve Customer
    # ------------------------------------------------------------------

    customer = None

    # Explicit customer in URL
    if customer_name:

        if not frappe.db.exists("Customer", customer_name):
            frappe.throw(
                _("Customer not found."),
                frappe.DoesNotExistError,
            )

        customer = frappe.get_doc(
            "Customer",
            customer_name,
        )

    # Authenticated user without customer in URL
    elif authenticated:

        customer = get_customer_for_user(user)

        if not customer:
            context.action = "customer_required"
            context.message = _(
                "No customer account is associated with your user."
            )
            return

        customer_name = customer.name

    # Guest without customer
    else:

        frappe.throw(
            _("Customer is required."),
            frappe.DoesNotExistError,
        )

    context.customer = customer
    context.customer_name = customer_name

    context.customer_account = {
        "name": customer.name,
        "customer_name": customer.customer_name,
        "customer_type": customer.customer_type,
        "customer_group": customer.customer_group,
        "territory": customer.territory,
        "email": customer.email_id,
        "mobile": customer.mobile_no,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "language": customer.language,
    }

    # ------------------------------------------------------------------
    # 3. Guest user
    # ------------------------------------------------------------------

    if not authenticated:

        if not identifier:
            context.action = "identifier_required"
            return

        existing_user = find_user_by_identifier(identifier)

        if existing_user:

            context.action = "login"

            context.login_url = build_login_url(
                return_url=build_customer_return_url(
                    customer.name
                )
            )

            context.message = _(
                "An account already exists. Please sign in to continue."
            )

        else:

            onboarding = create_customer_onboarding_session(
                customer=customer,
                identifier=identifier,
            )

            context.action = "signup"

            context.signup_url = build_signup_url(
                return_url=build_customer_return_url(
                    customer.name
                ),
                identifier=identifier,
                onboarding_token=onboarding["token"],
            )

            context.onboarding_token = onboarding["token"]

            context.message = _(
                "Create an account to access this customer account. "
                "E-mail address will be required to create an account."
            )

        return

    # ------------------------------------------------------------------
    # 4. Authenticated user
    # ------------------------------------------------------------------

    onboarding_token = frappe.request.cookies.get(
        "customer_onboarding_token"
    )

    # ------------------------------------------------------------------
    # 5. Complete onboarding if this login came from onboarding
    # ------------------------------------------------------------------

    if onboarding_token:

        onboarding = complete_customer_onboarding(
            customer=customer,
            user=user,
            onboarding_token=onboarding_token,
        )

        if onboarding["valid"]:

            # One-time onboarding credential is no longer needed.
            context.onboarding_completed = True

            # User has now been linked to the Customer.
            access = get_customer_access(
                customer=customer,
                user=user,
                identifier=identifier,
            )

            context.access = access
            context.action = "dashboard"

            context.customer_contact = access.get(
                "contact"
            )

            context.capabilities = access.get(
                "capabilities",
                {},
            )

            context.customer_status = get_customer_status(customer)

            context.access_status = {
                "state": "verified",
                "label": _("Verified"),
            }

            return
    # ------------------------------------------------------------------
    # 6. Normal authenticated access
    # ------------------------------------------------------------------

    access = get_customer_access(
        customer=customer,
        user=user,
        identifier=identifier,
    )

    context.access = access

    if not access["allowed"]:

        context.action = "access_denied"

        context.message = _(
            "You do not have access to this customer account."
        )

        return

    # ------------------------------------------------------------------
    # 7. Authorized customer
    # ------------------------------------------------------------------

    context.action = "dashboard"

    context.customer_contact = access.get(
        "contact"
    )

    context.capabilities = access.get(
        "capabilities",
        {},
    )

    context.customer_status = get_customer_status(customer)

    context.access_status = {
        "state": "verified",
        "label": _("Verified"),
    }

def complete_customer_onboarding(customer, user, onboarding_token):

    def checkpoint(step, **data):
        frappe.logger("customer_onboarding").warning(
            f"[ONBOARDING] {step} | {data}"
        )

    checkpoint(
        "START",
        customer=customer.name if customer else None,
        user=user,
        has_token=bool(onboarding_token),
    )

    # 1. Token
    if not onboarding_token:
        checkpoint("STOP: missing_token")
        return {"valid": False, "reason": "missing_token"}

    # 2. Find session
    session_name = frappe.db.get_value(
        "Customer Onboarding Session",
        {"token": onboarding_token},
        "name",
    )

    checkpoint(
        "SESSION_LOOKUP",
        session_name=session_name,
    )

    if not session_name:
        checkpoint("STOP: invalid_token")
        return {"valid": False, "reason": "invalid_token"}

    session = frappe.get_doc(
        "Customer Onboarding Session",
        session_name,
    )

    checkpoint(
        "SESSION_LOADED",
        status=session.status,
        customer=session.customer,
        identifier_type=session.identifier_type,
    )

    # 3. Status
    if session.status != "Pending":
        checkpoint(
            "STOP: session_not_pending",
            status=session.status,
        )
        return {
            "valid": False,
            "reason": "session_not_pending",
        }

    # 4. Expiry
    if (
        session.expires_at
        and session.expires_at < frappe.utils.now_datetime()
    ):
        checkpoint("STOP: session_expired")

        session.status = "Expired"
        session.save(ignore_permissions=True)

        return {
            "valid": False,
            "reason": "session_expired",
        }

    # 5. Customer match
    if session.customer != customer.name:
        checkpoint(
            "STOP: customer_mismatch",
            session_customer=session.customer,
            actual_customer=customer.name,
        )

        return {
            "valid": False,
            "reason": "customer_mismatch",
        }

    # 6. Authenticated User
    if not user or user == "Guest":
        checkpoint(
            "STOP: user_not_authenticated",
            user=user,
        )

        return {
            "valid": False,
            "reason": "user_not_authenticated",
        }

    checkpoint(
        "SESSION_AUTHORIZED",
        customer=customer.name,
        user=user,
        identifier_type=session.identifier_type,
    )

    # 7. Resolve Customer Contact
    contact_name = get_customer_contact(customer)

    if not contact_name:
        checkpoint("STOP: customer_contact_not_found")

        return {
            "valid": False,
            "reason": "customer_contact_not_found",
        }

    contact = frappe.get_doc(
        "Contact",
        contact_name,
    )

    checkpoint(
        "CONTACT_LOADED",
        contact=contact.name,
        contact_user=contact.user,
    )

    # 8. Make sure Contact is not linked to another User
    if contact.user and contact.user != user:
        checkpoint(
            "STOP: contact_already_linked",
            existing_user=contact.user,
        )

        return {
            "valid": False,
            "reason": "contact_already_linked",
        }

    # 9. Link Contact -> User
    contact.user = user
    contact.flags.ignore_permissions = True
    contact.save(ignore_permissions=True)

    checkpoint(
        "CONTACT_LINKED",
        contact=contact.name,
        user=user,
    )

    # 10. Add User to Customer Portal Users
    portal_user_exists = any(
        portal_user.user == user
        for portal_user in (customer.portal_users or [])
    )

    if not portal_user_exists:
        customer.append(
            "portal_users",
            {
                "user": user,
            },
        )

        customer.flags.ignore_permissions = True
        customer.flags.ignore_mandatory = True
        customer.save(ignore_permissions=True)

        checkpoint(
            "PORTAL_USER_SAVED",
            user=user,
        )

    # 11. Complete session
    session.user = user
    session.status = "Completed"
    session.completed_at = frappe.utils.now_datetime()
    session.save(ignore_permissions=True)

    checkpoint(
        "SESSION_COMPLETED",
        session=session.name,
    )

    frappe.db.commit()

    return {
        "valid": True,
        "customer": customer.name,
        "contact": contact.name,
        "user": user,
        "session": session.name,
    }


# ======================================================================
# User lookup
# ======================================================================

def find_user_by_identifier(identifier):
    """
    Find an existing Website User using email or mobile number.

    IMPORTANT:
    This function only identifies whether an account exists.
    It does NOT grant access to a Customer.
    """

    identifier = (identifier or "").strip()

    if not identifier:
        return None

    # Email
    if "@" in identifier:
        user = frappe.db.get_value(
            "User",
            {
                "email": identifier,
                "enabled": 1,
                "user_type": "Website User"
            },
            "name"
        )

        if user:
            return user

    # Mobile
    user = frappe.db.get_value(
        "User",
        {
            "mobile_no": identifier,
            "enabled": 1,
            "user_type": "Website User"
        },
        "name"
    )

    return user


# ======================================================================
# Customer authorization
# ======================================================================

def get_customer_access(customer, user, identifier=None):
    """
    Determine whether an authenticated user can access a Customer.

    Authorization is based on the ERPNext Customer/Contact/User
    relationship, not on the URL parameters.
    """

    result = {
        "allowed": False,
        "customer": customer.name,
        "contact": None,
        "capabilities": {}
    }

    # ------------------------------------------------------------------
    # Customer Portal Users
    # ------------------------------------------------------------------

    for portal_user in customer.get("portal_users") or []:
        if portal_user.user == user:
            result["allowed"] = True
            break

    # ------------------------------------------------------------------
    # Contact -> User relationship
    # ------------------------------------------------------------------

    contact = get_customer_contact(customer)

    if contact:
        contact_user = frappe.db.get_value(
            "Contact",
            contact,
            "user"
        )

        if contact_user == user:
            result["allowed"] = True

    # ------------------------------------------------------------------
    # Not authorized
    # ------------------------------------------------------------------

    if not result["allowed"]:
        return result

    result["contact"] = contact

    # ------------------------------------------------------------------
    # Capabilities
    #
    # Keep this server-controlled.
    # Do not determine permissions from JavaScript.
    # ------------------------------------------------------------------

    result["capabilities"] = {

            "view": True,

            "edit_profile": True,

            "edit_customer": bool(
                customer.get("custom_allow_portal_editing") if customer.get("custom_allow_portal_editing") else True
            ),

            "view_orders": True,

            "view_shipments": True,

            "manage_addresses": True,

        }

    return result


# ======================================================================
# Customer Contact
# ======================================================================

def get_customer_contact(customer):
    """
    Resolve the Contact associated with the Customer.

    Primary Contact is preferred.
    """

    if customer.customer_primary_contact:
        if frappe.db.exists(
            "Contact",
            customer.customer_primary_contact
        ):
            return customer.customer_primary_contact

    # Fallback: find a Contact linked to the Customer.
    contact = frappe.db.sql(
        """
        SELECT dl.parent
        FROM `tabDynamic Link` dl
        INNER JOIN `tabContact` c
            ON c.name = dl.parent
        WHERE dl.link_doctype = 'Customer'
          AND dl.link_name = %s
          AND dl.parenttype = 'Contact'
        ORDER BY c.creation ASC
        LIMIT 1
        """,
        customer.name,
        as_dict=True
    )

    if contact:
        return contact[0].parent

    return None


# ======================================================================
# Redirect URLs
# ======================================================================

def build_customer_return_url(customer_name):
    """
    Return URL used after Frappe authentication.
    """

    return frappe.utils.get_url(
        "/customer?name={}".format(
            frappe.utils.quote(customer_name)
        )
    )


def build_login_url(return_url):
    """
    Frappe login page.
    """

    return "/login?redirect-to={}".format(
        frappe.utils.quote(return_url)
    )

def determine_identifier_type(identifier, customer=None):
    identifier = (identifier or "").strip()

    if "@" in identifier:
        return "Email"

    if customer and identifier == customer.name:
        return "Customer ID"

    return "Mobile Number"


def set_onboarding_cookie(token):
    cookie = SimpleCookie()

    cookie["customer_onboarding_token"] = token
    cookie["customer_onboarding_token"]["max-age"] = 1800
    cookie["customer_onboarding_token"]["httponly"] = True
    cookie["customer_onboarding_token"]["samesite"] = "Lax"

    if frappe.conf.get("ssl_certificate"):
        cookie["customer_onboarding_token"]["secure"] = True

    frappe.local.response = frappe.local.response or {}
    frappe.local.response["Set-Cookie"] = cookie.output(header="").strip()

def build_signup_url(
    return_url,
    identifier=None,
    onboarding_token=None,
):

    params = [
        "redirect-to={}".format(
            frappe.utils.quote(return_url, safe="")
        )
    ]

    if identifier:
        params.append(
            "identifier={}".format(
                frappe.utils.quote(identifier, safe="")
            )
        )

    return "/login?{}#signup".format(
        "&".join(params)
    )

def hash_token(token):
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

def create_customer_onboarding_session(customer, identifier):
    identifier = (identifier or "").strip()

    if not identifier:
        frappe.throw(_("Identifier is required."))

    identifier_type = determine_identifier_type(
        identifier,
        customer,
    )

    normalized_identifier = (
        identifier.lower()
        if identifier_type == "Email"
        else identifier
    )

    identifier_hash = hash_token(normalized_identifier)

    # Invalidate previous pending sessions
    existing_sessions = frappe.get_all(
        "Customer Onboarding Session",
        filters={
            "customer": customer.name,
            "identifier_hash": identifier_hash,
            "status": "Pending",
        },
        pluck="name",
    )

    for session_name in existing_sessions:
        frappe.db.set_value(
            "Customer Onboarding Session",
            session_name,
            "status",
            "Cancelled",
            update_modified=False,
        )

    # Generate a new secure token
    token = secrets.token_urlsafe(32)

    session = frappe.get_doc({
        "doctype": "Customer Onboarding Session",

        "token": token,

        "customer": customer.name,

        "identifier_type": identifier_type,

        "identifier_hash": identifier_hash,

        "status": "Pending",

        "expires_at": add_to_date(
            now_datetime(),
            minutes=30,
        ),
        "signup_email": (
            normalized_identifier
            if identifier_type == "Email"
            else None
        ),
    })

    session.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "name": session.name,
        "token": token,
        "customer": customer.name,
    }