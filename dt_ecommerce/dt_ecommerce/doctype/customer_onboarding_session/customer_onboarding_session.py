# Copyright (c) 2026, NDF Tech Labs and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CustomerOnboardingSession(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		completed_at: DF.Datetime | None
		customer: DF.Link | None
		expires_at: DF.Datetime | None
		identifier_hash: DF.Data | None
		identifier_type: DF.Literal["Email", "Mobile Number", "Customer ID"]
		signup_email: DF.Data | None
		status: DF.Literal["Pending", "Signup", "Completed", "Expired", "Cancelled"]
		token: DF.Data | None
		user: DF.Link | None
		verification_id: DF.Data | None
	# end: auto-generated types

	pass
