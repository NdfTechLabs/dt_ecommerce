import frappe

from erpnext.selling.doctype.customer.customer import (
    Customer,
    make_contact,
)


class CustomerMixin(Customer):

    def create_primary_contact(self):
        if not self.customer_primary_contact and not self.lead_name:
            if self.mobile_no or self.email_id or self.first_name or self.last_name:
                contact = make_contact(self)
                self.db_set("customer_primary_contact", contact.name)
                self.db_set("mobile_no", self.mobile_no)
                self.db_set("email_id", self.email_id)

        elif self.customer_primary_contact:
            is_primary = frappe.db.get_value(
                "Contact",
                self.customer_primary_contact,
                "is_primary_contact",
            )

            if not is_primary:
                frappe.set_value(
                    "Contact",
                    self.customer_primary_contact,
                    "is_primary_contact",
                    1,
                )