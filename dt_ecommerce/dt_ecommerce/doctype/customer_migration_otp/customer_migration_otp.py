# Copyright (c) 2026, NDF Tech Labs and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CustomerMigrationOTP(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		attempts: DF.Int
		channel: DF.Literal["Email", "SMS"]
		consumed: DF.Check
		customer: DF.Link | None
		expires_at: DF.Datetime | None
		identifier_hash: DF.Data | None
		identifier_type: DF.Literal["Email", "Mobile Number", "Customer ID"]
		maximum_attempts: DF.Int
		otp_hash: DF.Data | None
		verification_id: DF.Data | None
		verified: DF.Check
	# end: auto-generated types

	pass
