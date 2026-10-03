import frappe
import re
import secrets
from frappe import _
from frappe.core.doctype.sms_settings.sms_settings import send_sms

import hashlib
import hmac

from frappe.utils import add_to_date, now_datetime

@frappe.whitelist(allow_guest=True)
def check_migration(identifier):
    settings = frappe.get_single("Customer Migration Settings")

    if not settings.enabled:
        return {"available": False}

    # Normalize identifier here
    identifier = identifier.strip()
    print(identifier)
    customer = find_customer(identifier, settings)

    if not customer:
        return {"available": False}

    # Customer already has an online account?
    if customer_has_user(customer):
        return {"available": False}

    return {
        "available": True
    }


def normalize_phone(phone):
    if not phone:
        return None

    # Keep digits only
    phone = "".join(char for char in str(phone) if char.isdigit())

    if not phone:
       return None

    #Kenyan local format: 07XXXXXXXX / 01XXXXXXXX
    if len(phone) == 10 and phone.startswith(("07", "01")):
       return "254" + phone[1:]

    #Already in Kenyan international format
    if len(phone) == 12 and phone.startswith("254"):
       return phone

    return phone

def is_email(identifier):
    return bool(
        re.match(
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
            identifier,
            re.IGNORECASE,
        )
    )


def is_phone(identifier):
    # Remove common formatting characters
    value = re.sub(r"[\s().-]", "", identifier)

    # Kenya/international-style number
    return bool(re.match(r"^\+?\d{9,15}$", value))


def find_customer(identifier, settings):
    identifier = (identifier or "").strip()

    if not identifier:
        return None

    # ---------------------------------------------------------
    # Customer ID
    # ---------------------------------------------------------
    if settings.match_by_customer_id:
        if frappe.db.exists("Customer", identifier):
            return frappe.get_doc("Customer", identifier)

    # ---------------------------------------------------------
    # Email
    # ---------------------------------------------------------
    if settings.match_by_email and is_email(identifier):
        return find_customer_by_email(identifier)

    # ---------------------------------------------------------
    # Mobile number
    # ---------------------------------------------------------
    if settings.match_by_mobile_number and is_phone(identifier):
        return find_customer_by_mobile(identifier)

    return None
    
def customer_has_user(customer):
    contact_name = customer.get("customer_primary_contact")

    if not contact_name:
        return False

    user = frappe.db.get_value(
        "Contact",
        contact_name,
        "user",
    )

    return bool(user)

def find_customer_by_email(email):
    email = email.lower().strip()

    customer = frappe.db.get_value(
        "Customer",
        {"email_id": email},
        "name",
    )

    if customer:
        return frappe.get_doc("Customer", customer)

    contact = frappe.db.get_value(
        "Contact",
        {
            "email_id": email,
            "is_primary_contact": 1,
        },
        "name",
    )

    if contact:
        customer = frappe.db.get_value(
            "Dynamic Link",
            {
                "parent": contact,
                "parenttype": "Contact",
                "parentfield": "links",
                "link_doctype": "Customer",
            },
            "link_name",
        )

        if customer:
            return frappe.get_doc("Customer", customer)

    return None

def find_customer_by_mobile(mobile):
    mobile = normalize_phone(mobile)

    if not mobile:
        return None

    customers = frappe.get_all(
        "Customer",
        filters={
            "mobile_no": ["is", "set"],
        },
        fields=[
            "name",
            "mobile_no",
        ],
    )

    for customer in customers:
        if normalize_phone(customer.mobile_no) == mobile:
            return frappe.get_doc("Customer", customer.name)

    contacts = frappe.get_all(
        "Contact",
        filters={
            "mobile_no": ["is", "set"],
            "is_primary_contact": 1,
        },
        fields=[
            "name",
            "mobile_no",
        ],
    )

    for contact in contacts:
        if normalize_phone(contact.mobile_no) != mobile:
            continue

        customer = frappe.db.get_value(
            "Dynamic Link",
            {
                "parent": contact.name,
                "parenttype": "Contact",
                "parentfield": "links",
                "link_doctype": "Customer",
            },
            "link_name",
        )

        if customer:
            return frappe.get_doc("Customer", customer)

    return None

def get_customer_primary_contact(customer_name):
    contact_name = frappe.db.get_value(
        "Dynamic Link",
        {
            "link_doctype": "Customer",
            "link_name": customer_name,
            "parenttype": "Contact",
            "parentfield": "links",
        },
        "parent",
    )

    if not contact_name:
        return None

    return frappe.db.get_value(
        "Contact",
        {
            "name": contact_name,
            "is_primary_contact": 1,
        },
        [
            "name",
            "email_id",
            "mobile_no",
        ],
        as_dict=True,
    )


def determine_identifier_type(identifier, settings):
    """
    Determine the identifier type and resolve the corresponding customer.

    Customer ID is checked first because a Customer name can potentially
    look like a phone number or other identifier.
    """

    identifier = (identifier or "").strip()

    if not identifier:
        return None, None

    # ---------------------------------------------------------
    # Customer ID
    # ---------------------------------------------------------

    if settings.match_by_customer_id:
        if frappe.db.exists("Customer", identifier):
            return "Customer ID", frappe.get_doc("Customer", identifier)

    # ---------------------------------------------------------
    # Email
    # ---------------------------------------------------------

    if settings.match_by_email and is_email(identifier):
        customer = find_customer_by_email(identifier)

        if customer:
            return "Email", customer

    # ---------------------------------------------------------
    # Mobile Number
    # ---------------------------------------------------------

    if settings.match_by_mobile_number and is_phone(identifier):
        customer = find_customer_by_mobile(identifier)

        if customer:
            return "Mobile Number", customer

    return None, None


def hash_value(value):
    """
    SHA-256 hash for identifiers and OTPs.

    The plaintext value is never stored in Customer Migration OTP.
    """

    return hashlib.sha256(
        str(value).encode("utf-8")
    ).hexdigest()


def normalize_identifier(identifier, identifier_type):
    """
    Normalize the identifier before hashing it.
    """

    identifier = (identifier or "").strip()

    if identifier_type == "Email":
        return identifier.lower()

    if identifier_type == "Mobile Number":
        return normalize_phone(identifier)

    return identifier


def mask_email(email):
    email = (email or "").strip()

    if "@" not in email:
        return "***"

    local, domain = email.split("@", 1)

    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = local[0] + ("*" * (len(local) - 1))

    return f"{masked_local}@{domain}"


def mask_phone(phone):
    phone = normalize_phone(phone)

    if not phone:
        return "***"

    if len(phone) <= 4:
        return "*" * len(phone)

    return "*" * (len(phone) - 4) + phone[-4:]


def resolve_otp_destination(customer, identifier_type, identifier):
    """
    Determine the destination to which the OTP should be sent.

    Email identifier:
        Send to the email identifier that matched the customer.

    Mobile identifier:
        Send to the mobile identifier that matched the customer.

    Customer ID:
        Resolve the customer's primary contact.
        Prefer email, otherwise use mobile.
    """

    # ---------------------------------------------------------
    # Email identifier
    # ---------------------------------------------------------

    if identifier_type == "Email":
        email = (identifier or "").strip().lower()

        if email:
            return {
                "channel": "Email",
                "destination": email,
                "masked_destination": mask_email(email),
            }

    # ---------------------------------------------------------
    # Mobile identifier
    # ---------------------------------------------------------

    if identifier_type == "Mobile Number":
        mobile = normalize_phone(identifier)

        if mobile:
            return {
                "channel": "SMS",
                "destination": mobile,
                "masked_destination": mask_phone(mobile),
            }

    # ---------------------------------------------------------
    # Customer ID
    # ---------------------------------------------------------

    if identifier_type == "Customer ID":
        contact = get_customer_primary_contact(customer.name)

        if contact:
            # Prefer email
            if contact.get("email_id"):
                email = contact.email_id.strip().lower()

                return {
                    "channel": "Email",
                    "destination": email,
                    "masked_destination": mask_email(email),
                }

            # Fallback to mobile
            if contact.get("mobile_no"):
                mobile = normalize_phone(contact.mobile_no)

                if mobile:
                    return {
                        "channel": "SMS",
                        "destination": mobile,
                        "masked_destination": mask_phone(mobile),
                    }

    return None


def generate_otp():
    """
    Generate a cryptographically secure six-digit OTP.
    """

    return f"{secrets.randbelow(1_000_000):06d}"


def generate_verification_id():
    """
    Generate a non-guessable verification ID.
    """

    return secrets.token_urlsafe(32)


def send_email_otp(email, otp, expiry_minutes):
    frappe.set_user("Administrator")
    frappe.sendmail(
        recipients=[email],
        subject=_("Your customer migration verification code"),
        message=_(
            """
            <p>Your customer migration verification code is:</p>

            <h2>{0}</h2>

            <p>This code will expire in {1} minutes.</p>

            <p>
                If you did not request this verification,
                you can ignore this email.
            </p>
            """
        ).format(
            otp,
            expiry_minutes,
        ),
        now=True,
    )


def send_sms_otp(mobile, otp, expiry_minutes):
    message = _(
        "Your customer migration verification code is {0}. "
        "It expires in {1} minutes."
    ).format(
        otp,
        expiry_minutes,
    )
    frappe.set_user("Administrator")
    send_sms(
        receiver_list=[mobile],
        msg=message,
    )


def invalidate_otp(otp_doc, consumed=False):
    """
    Invalidate an OTP.

    If consumed=True, the OTP was successfully verified and should
    never be usable again.
    """

    otp_doc.db_set(
        {
            "consumed": 1,
            "verified": 1 if consumed else otp_doc.verified,
        },
        update_modified=False,
    )


def store_otp(
    customer,
    identifier,
    identifier_type,
    channel,
    destination,
    otp,
    expiry_minutes,
    maximum_attempts,
):
    """
    Create the OTP challenge record.

    Neither the raw identifier nor OTP is stored.
    """

    normalized_identifier = normalize_identifier(
        identifier,
        identifier_type,
    )

    verification_id = generate_verification_id()

    expires_at = add_to_date(
        now_datetime(),
        minutes=expiry_minutes,
    )

    otp_doc = frappe.get_doc(
        {
            "doctype": "Customer Migration OTP",
            "verification_id": verification_id,
            "customer": customer,
            "identifier_type": identifier_type,
            "identifier_hash": hash_value(normalized_identifier),
            "channel": channel,
            "otp_hash": hash_value(otp),
            "expires_at": expires_at,
            "attempts": 0,
            "maximum_attempts": maximum_attempts,
            "verified": 0,
            "consumed": 0,
        }
    )

    otp_doc.insert(ignore_permissions=True)

    return otp_doc


def request_otp(identifier):
    """
    Resolve the customer from the supplied identifier and send
    an OTP through the appropriate channel.

    The client does not provide customer or identifier_type.
    """

    settings = frappe.get_single("Customer Migration Settings")

    if not settings.enabled:
        frappe.throw(
            _("Customer migration is disabled.")
        )

    identifier = (identifier or "").strip()

    if not identifier:
        frappe.throw(
            _("Please provide an identifier."),
            title=_("Identifier Required"),
        )

    # ---------------------------------------------------------
    # Resolve identifier and customer
    # ---------------------------------------------------------

    identifier_type, customer = determine_identifier_type(
        identifier,
        settings,
    )

    if not customer:
        frappe.throw(
            _("We could not find a matching customer."),
            title=_("Customer Not Found"),
        )

    # ---------------------------------------------------------
    # Prevent migration of existing online accounts
    # ---------------------------------------------------------

    if customer_has_user(customer):
        frappe.throw(
            _("This customer already has an online account."),
            title=_("Account Already Exists"),
        )

    # ---------------------------------------------------------
    # OTP disabled
    # ---------------------------------------------------------

    if not settings.otp_enabled:
        return {
            "success": True,
            "otp_required": False,
            "customer": customer.name,
        }

    # ---------------------------------------------------------
    # Resolve OTP destination
    # ---------------------------------------------------------

    destination = resolve_otp_destination(
        customer,
        identifier_type,
        identifier,
    )

    if not destination:
        frappe.throw(
            _(
                "We could not find an email address or mobile number "
                "to verify this customer."
            ),
            title=_("Verification Contact Not Found"),
        )

    expiry_minutes = settings.otp_expiry or 5
    maximum_attempts = settings.maximum_attempts or 5

    otp = generate_otp()

    # ---------------------------------------------------------
    # Store challenge
    # ---------------------------------------------------------

    otp_doc = store_otp(
        customer=customer.name,
        identifier=identifier,
        identifier_type=identifier_type,
        channel=destination["channel"],
        destination=destination["destination"],
        otp=otp,
        expiry_minutes=expiry_minutes,
        maximum_attempts=maximum_attempts,
    )

    # ---------------------------------------------------------
    # Send OTP
    # ---------------------------------------------------------

    try:
        if destination["channel"] == "Email":
            send_email_otp(
                destination["destination"],
                otp,
                expiry_minutes,
            )

        elif destination["channel"] == "SMS":
            send_sms_otp(
                destination["destination"],
                otp,
                expiry_minutes,
            )

        else:
            frappe.throw(
                _("Unsupported OTP channel.")
            )

    except Exception:
        # Do not leave a usable OTP if delivery failed.
        otp_doc.db_set(
            "consumed",
            1,
            update_modified=False,
        )

        raise

    return {
        "success": True,
        "otp_required": True,
        "verification_id": otp_doc.verification_id,
        "identifier_type": identifier_type,
        "channel": destination["channel"],
        "destination": destination["masked_destination"],
        "expires_in": expiry_minutes,
    }


def get_pending_otp(verification_id):
    """
    Get the active OTP challenge.
    """

    if not verification_id:
        return None

    otp_name = frappe.db.get_value(
        "Customer Migration OTP",
        {
            "verification_id": verification_id,
            "consumed": 0,
        },
        "name",
    )

    if not otp_name:
        return None

    return frappe.get_doc(
        "Customer Migration OTP",
        otp_name,
    )


def increment_otp_attempts(otp_doc):
    """
    Increment failed verification attempts.
    """

    otp_doc.db_set(
        "attempts",
        (otp_doc.attempts or 0) + 1,
        update_modified=False,
    )

@frappe.whitelist(allow_guest=True)
def verify_otp(verification_id, otp):
    """
    Verify an OTP challenge.

    The verification ID is used instead of the original identifier,
    so the client does not need to resend the customer's identifier.
    """

    otp = (otp or "").strip()

    if not verification_id or not otp:
        frappe.throw(
            _("Verification ID and OTP are required."),
            title=_("Verification Required"),
        )

    otp_doc = get_pending_otp(verification_id)

    if not otp_doc:
        frappe.throw(
            _("The verification code is invalid or has already been used."),
            title=_("Invalid Verification"),
        )

    # ---------------------------------------------------------
    # Expiry
    # ---------------------------------------------------------

    if otp_doc.expires_at <= now_datetime():
        invalidate_otp(otp_doc)

        frappe.throw(
            _("The verification code has expired."),
            title=_("OTP Expired"),
        )

    # ---------------------------------------------------------
    # Attempts
    # ---------------------------------------------------------

    if otp_doc.attempts >= otp_doc.maximum_attempts:
        invalidate_otp(otp_doc)

        frappe.throw(
            _("Maximum verification attempts exceeded."),
            title=_("Verification Failed"),
        )

    # ---------------------------------------------------------
    # Compare hashes
    # ---------------------------------------------------------

    supplied_hash = hash_value(otp)

    if not hmac.compare_digest(
        supplied_hash,
        otp_doc.otp_hash,
    ):
        increment_otp_attempts(otp_doc)

        # Invalidate immediately when this attempt consumed
        # the final allowed attempt.
        if otp_doc.attempts + 1 >= otp_doc.maximum_attempts:
            otp_doc.db_set(
                "consumed",
                1,
                update_modified=False,
            )

        frappe.throw(
            _("Invalid verification code."),
            title=_("Verification Failed"),
        )

    # ---------------------------------------------------------
    # Successful verification
    # ---------------------------------------------------------

    otp_doc.db_set(
        {
            "verified": 1,
            "consumed": 1,
        },
        update_modified=False,
    )

    return {
        "success": True,
        "verified": True,
        "customer": otp_doc.customer,
        "verification_id": otp_doc.verification_id,
    }

@frappe.whitelist(allow_guest=True)
def activate_account(identifier):
    settings = frappe.get_single("Customer Migration Settings")

    if not settings.enabled:
        frappe.throw(
            _("Customer migration is disabled."),
            title=_("Migration Disabled"),
        )

    identifier = (identifier or "").strip()

    if not identifier:
        frappe.throw(
            _("Please provide an identifier."),
            title=_("Identifier Required"),
        )

    identifier_type, customer = determine_identifier_type(
        identifier,
        settings,
    )

    if not customer:
        frappe.throw(
            _("We could not find a matching customer."),
            title=_("Customer Not Found"),
        )

    if customer_has_user(customer):
        frappe.throw(
            _("This customer already has an online account."),
            title=_("Account Already Exists"),
        )

    # ---------------------------------------------------------
    # OTP required
    # ---------------------------------------------------------

    if settings.otp_enabled:
        otp_result = request_otp(identifier)

        return {
            "success": True,
            "next_step": "otp",
            **otp_result,
        }

    # ---------------------------------------------------------
    # No OTP required
    # ---------------------------------------------------------

    return {
        "success": True,
        "next_step": "account_update",
        "customer": customer.name,
    }

def cleanup_expired_otps():
    frappe.db.delete(
        "Customer Migration OTP",
        {
            "expires_at": ["<", now_datetime()],
        },
    )

    frappe.db.commit()

def get_valid_onboarding_session(onboarding_token):
    session = frappe.db.get_value(
        "Customer Onboarding Session",
        {
            "token": onboarding_token,
            "status": "Pending",
        },
        [
            "name",
            "customer",
            "token",
            "expires_at",
        ],
        as_dict=True,
    )

    if session and (
        not session.expires_at
        or session.expires_at > frappe.utils.now_datetime()
    ):
        return session

def get_migration_customer():
    token = frappe.request.cookies.get("customer_onboarding_token")

    if not token:
        return None

    onboarding = get_valid_onboarding_session(token)

    if not onboarding:
        return None

    customer_name = onboarding.customer

    if not customer_name:
        return None

    if not frappe.db.exists("Customer", customer_name):
        return None

    return frappe.get_doc("Customer", customer_name)