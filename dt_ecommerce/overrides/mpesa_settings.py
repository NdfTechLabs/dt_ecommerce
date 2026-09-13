import frappe

from frappe_mpsa_payments.frappe_mpsa_payments.doctype.mpesa_settings.mpesa_settings import (
    MpesaSettings,
)

from frappe_mpsa_payments.utils.doctype_names import (
    MPESA_EXPRESS_REQUEST_DOCTYPE,
)

from frappe_mpsa_payments.utils.utils import (
    convert_amount_to_kes
)

from frappe.utils import get_url


class CustomMpesaSettings(MpesaSettings):

    def get_payment_url(self, **kwargs):
        phone = kwargs.get("phone") or kwargs.get("phone_number") or ""
        base_amount = kwargs.get("amount", 0.0)
        currency = kwargs.get("currency", "KES")
        setting_name = self.name

        reference_doctype = kwargs.get("reference_doctype")
        reference_name = kwargs.get("reference_docname")

        # Use values supplied by the caller first
        title = kwargs.get("title")
        description = kwargs.get("description")

        # Only generate missing values for Sales Orders
        if reference_doctype == "Payment Request":
            if not title:
                title = f"Requesting to clear Payment Request {reference_name}"

            if not description:
                description = (
                    f"Payment of {base_amount} {currency} "
                    f"for clearing request {reference_name}"
                )

        actual_amount = base_amount

        # ---------------------------------------------------------
        # IMPORTANT:
        # Reuse an already-created M-Pesa Express Request.
        # ---------------------------------------------------------
        existing = frappe.db.get_value(
            MPESA_EXPRESS_REQUEST_DOCTYPE,
            {
                "reference_doctype": reference_doctype,
                "reference_name": reference_name,
            },
            ["name", "request_id", "route", "status"],
            as_dict=True,
        )

        if existing:
            frappe.logger().info(
                f"MPESA: Reusing existing Express Request "
                f"{existing.name} "
                f"request_id={existing.request_id} "
                f"status={existing.status}"
            )

            return get_url(existing.route)

        # ---------------------------------------------------------
        # Currency conversion
        # ---------------------------------------------------------
        if currency != "KES" and base_amount:
            try:
                actual_amount = convert_amount_to_kes(
                    amount=float(base_amount),
                    currency=currency,
                    settings=setting_name,
                )
            except Exception:
                actual_amount = base_amount

        # ---------------------------------------------------------
        # Create Express Request
        # ---------------------------------------------------------
        express_request = frappe.get_doc(
            {
                "doctype": MPESA_EXPRESS_REQUEST_DOCTYPE,
                "payment_gateway": kwargs.get("payment_gateway"),

                "reference_doctype": reference_doctype,
                "reference_name": reference_name,

                "transaction_title": title,
                "transaction_description": description,

                "base_amount": base_amount,
                "currency": currency,
                "amount": actual_amount,
                "status": "In Progress",

                "redirect_to": kwargs.get("redirect_to"),

                "transaction_title": title,
                "description": transaction_description,
            }
        )

        if phone:
            express_request.phone_number = sanitize_mobile_number(phone)

        express_request.insert(ignore_permissions=True)

        return get_url(express_request.route)