app_name = "dt_ecommerce"
app_title = "Dt Ecommerce"
app_publisher = "NDF Tech Labs"
app_description = "Ecommerce Themes developed by NDF Tech Labs"
app_email = "info@ndftechlabs.com"
app_license = "agpl-3.0"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# Added app entry for dt_ecommerce in the apps screen, with a logo and route to the app.
# add_to_apps_screen = [
# 	{
# 		"name": "dt_ecommerce",
# 		"logo": "/assets/dt_ecommerce/images/logo.png",
# 		"title": "E-commerce",
# 		"route": "/desk",
		# "has_permission": "dt_ecommerce.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/dt_ecommerce/css/dt_ecommerce.css"
# app_include_js = "/assets/dt_ecommerce/js/dt_ecommerce.js"

# app_include_css = [
#     "/assets/dt_ecommerce/css/base.css",
#     "/assets/dt_ecommerce/css/theme_glass.css",
# ]

# app_include_js = [
#     "/assets/dt_ecommerce/js/theme.js",
# ]

# include js, css files in header of web template
# web_include_css = "/assets/dt_ecommerce/css/dt_ecommerce.css"
# web_include_js = "/assets/dt_ecommerce/js/dt_ecommerce.js"
required_apps = ["webshop"]

# v=1.2 — bump this whenever CSS/JS changes to force all browsers to re-fetch
# (Werkzeug ignores query strings for static files; browsers treat each ?v= as a new URL)
_V = "?v=2.9"

web_include_css = [
    "/assets/dt_ecommerce/css/base.css"        + _V,
    "/assets/dt_ecommerce/css/theme_glass.css" + _V,
    "/assets/dt_ecommerce/css/hero/index.css" + _V,
]

web_include_js = [
    "/assets/dt_ecommerce/js/theme.js"  + _V,
    "assets/dt_ecommerce/js/hero/index.js" + _V,
    "assets/dt_ecommerce/js/search/index.js" + _V,
    "/assets/dt_ecommerce/js/utm.js" + _V,
]

fixtures = [
    {
        "dt": "Custom Field",
        "filters": [["dt", "=", "Item"], ["fieldname", "in", [
            "custom_dalali_section", "custom_liquor_category", "custom_wine_varietal",
            "custom_origin_country", "custom_region", "custom_dalali_col",
            "custom_vintage_year", "custom_alcohol_content", "custom_case_size", "custom_importer",
        ]]],
    }
]

# Inject wholesale bootstrap data (case_size, item_code) into item page context
update_website_context = ["dt_ecommerce.utils.extend_dalali_context"]

# Expose dalali_item_code / dalali_case_size as window.* vars via an inline script
jinja = {
    "methods": ["dt_ecommerce.utils.dalali_bootstrap_script"],
}


# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "dt_ecommerce/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "dt_ecommerce/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "dt_ecommerce.utils.jinja_methods",
# 	"filters": "dt_ecommerce.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "dt_ecommerce.install.before_install"
after_install = "dt_ecommerce.installs.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "dt_ecommerce.uninstall.before_uninstall"
# after_uninstall = "dt_ecommerce.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "dt_ecommerce.utils.before_app_install"
# after_app_install = "dt_ecommerce.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "dt_ecommerce.utils.before_app_uninstall"
# after_app_uninstall = "dt_ecommerce.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "dt_ecommerce.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    # Block publishing internal-operation items to the webshop.
    # Fires on every Website Item save/update.
    "Website Item": {
        "validate": "dt_ecommerce.catalog_guard.block_internal_publish",
    },
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"dt_ecommerce.tasks.all"
# 	],
# 	"daily": [
# 		"dt_ecommerce.tasks.daily"
# 	],
# 	"hourly": [
# 		"dt_ecommerce.tasks.hourly"
# 	],
# 	"weekly": [
# 		"dt_ecommerce.tasks.weekly"
# 	],
# 	"monthly": [
# 		"dt_ecommerce.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "dt_ecommerce.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "dt_ecommerce.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "dt_ecommerce.event.get_events"
# }

override_whitelisted_methods = {
    "webshop.webshop.shopping_cart.cart.create_lead_for_item_inquiry":
        "dt_ecommerce.api.shopping_cart.create_lead_for_item_inquiry"
}

#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "dt_ecommerce.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["dt_ecommerce.utils.before_request"]
# after_request = ["dt_ecommerce.utils.after_request"]

# Job Events
# ----------
# before_job = ["dt_ecommerce.utils.before_job"]
# after_job = ["dt_ecommerce.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"dt_ecommerce.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
export_python_type_annotations = True

# Require all whitelisted methods to have type annotations
require_type_annotated_api_methods = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

