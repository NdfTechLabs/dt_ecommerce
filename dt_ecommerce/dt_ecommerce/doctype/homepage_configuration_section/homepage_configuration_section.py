# Copyright (c) 2026, NDF Tech Labs and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class HomepageConfigurationSection(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		limit: DF.Int
		section_id: DF.Data | None
		source: DF.Data | None
		title: DF.Data | None
		value: DF.Data | None
	# end: auto-generated types

	pass
