# Copyright (c) 2026, NDF Tech Labs and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class WebshopAssistantSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dt_ecommerce.dt_ecommerce.doctype.assistant_capability.assistant_capability import AssistantCapability
		from dt_ecommerce.dt_ecommerce.doctype.assistant_channel.assistant_channel import AssistantChannel
		from frappe.types import DF

		assistant_icon: DF.AttachImage | None
		assistant_name: DF.Data | None
		button_label: DF.Data | None
		capabilities: DF.Table[AssistantCapability]
		channels: DF.Table[AssistantChannel]
		enabled: DF.Check
		greeting: DF.Data | None
		panel_title: DF.Data | None
		position: DF.Literal["Bottom Right", "Bottom Left"]
		show_on_desktop: DF.Check
		show_on_mobile: DF.Check
	# end: auto-generated types

	def get_config(self):
		return {
			"enabled": self.enabled,
			"assistant_name": self.assistant_name,
			"button_label": self.button_label,
			"panel_title": self.panel_title,
			"greeting": self.greeting,
			"position": self.position,
			"show_on_mobile": self.show_on_mobile,
			"show_on_desktop": self.show_on_desktop,
			"assistant_icon": self.assistant_icon,
			"capabilities": self._get_capabilities(),
			"channels": self._get_channels(),
		}

	def _get_capabilities(self):
		return [
			{
				"key": capability.capability,
				"enabled": capability.enabled,
				"description": capability.description,
				"icon": capability.icon,
				"display_order": capability.display_order,
			}
			for capability in self.capabilities
			if capability.enabled
		]

	def _get_channels(self):
		return [
			{
				"key": channel.channel,
				"enabled": channel.enabled,
				"label": channel.label,
				"description": channel.description,
				"icon": channel.icon,
				"display_order": channel.display_order,
				"contact": channel.contact,
				"configuration": channel.configuration,
			}
			for channel in self.channels
			if channel.enabled
		]
