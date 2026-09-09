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

		image: DF.AttachImage | None
		limit: DF.Int
		media_type: DF.Literal["Image", "Video"]
		section_id: DF.Data | None
		source: DF.Literal["trending", "best_sellers", "recommended", "category", "offer", "promotion"]
		title: DF.Data | None
		value: DF.Data | None
		video: DF.Attach | None
	# end: auto-generated types

	pass
