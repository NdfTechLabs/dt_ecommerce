# Copyright (c) 2026, NDF Tech Labs and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class AssistantChannel(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		channel: DF.Literal["whatsapp", "web_chat"]
		configuration: DF.Code | None
		contact: DF.Data | None
		description: DF.SmallText | None
		display_order: DF.Int
		enabled: DF.Check
		icon: DF.Data | None
		label: DF.Data | None
		name: DF.Int | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
	# end: auto-generated types

	pass
