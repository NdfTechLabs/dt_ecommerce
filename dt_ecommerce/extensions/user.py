import frappe
from frappe.core.doctype.user.user import User
from frappe import _
from frappe.utils import get_url
from urllib.parse import quote

class CustomerUserMixin(User):
    def send_welcome_mail_to_user(self):
        # Generate the normal Frappe registration link
        link = self._reset_password()# Generate normal Frappe registration link

        # ---------------------------------------------------------
        # Customer onboarding
        # ---------------------------------------------------------

        onboarding_token = frappe.request.cookies.get(
            "customer_onboarding_token"
        )

        if onboarding_token:
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
                customer_url = (
                    f"/customer"
                    f"?name={quote(session.customer, safe='')}"
                )

                link = (
                    f"{link}"
                    f"&redirect-to={quote(customer_url, safe='')}"
                )
        # ---------------------------------------------------------
        # CUSTOMER ONBOARDING CUSTOMIZATION
        # ---------------------------------------------------------

        # ---------------------------------------------------------

        subject = None

        method = frappe.get_hooks("welcome_email")
        if method:
            subject = frappe.get_attr(method[-1])()

        if not subject:
            site_name = (
                frappe.db.get_default("site_name")
                or frappe.get_conf().get("site_name")
            )

            if site_name:
                subject = _("Welcome to {0}").format(site_name)
            else:
                subject = _("Complete Registration")

        welcome_email_template = frappe.db.get_system_setting(
            "welcome_email_template"
        )

        self.send_login_mail(
            subject,
            "new_user",
            {
                "link": link,
                "site_url": get_url(),
            },
            custom_template=welcome_email_template,
        )