# Copyright (c) 2026, NDF Tech Labs and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CustomerMigrationSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		auto_enable_user: DF.Check
		enabled: DF.Check
		match_by_customer_id: DF.Check
		match_by_email: DF.Check
		match_by_mobile_number: DF.Check
		maximum_attempts: DF.Int
		otp_enabled: DF.Check
		otp_expiry: DF.Int
		require_address: DF.Check
		require_email: DF.Check
		require_phone: DF.Check
		user_type: DF.Literal["Website User", "System User"]
	# end: auto-generated types

	pass
