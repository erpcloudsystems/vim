from . import __version__ as app_version

app_name = "vim"
app_title = "VIM"
app_publisher = "aavu"
app_description = "VIM customization"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "dev@avu.net.in"
app_license = "MIT"
fixtures = ["Custom Field","Property Setter","Print Format"]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/vim/css/vim.css"
# app_include_js = "/assets/js/erpnext.min.js"
app_include_js = ["/assets/vim/js/customer_quick_entry.js","//cdnjs.cloudflare.com/ajax/libs/echarts/4.8.0/echarts.min.js","/assets/vim/js/frappe/ui/toolbar/search_utils.js" ]
on_session_creation  = 'vim.api.successful_login'
jenv = {
"methods": [
"get_qr:vim.custom_script.qr_generate.get_qr",
"get_out_time:vim.custom_script.qr_generate.get_out_time"
]

}
calendars = ["Event Booking"]
doctype_js = {
			   "Asset" : "custom_script/asset/asset.js"   , 
				"Item" : "custom_script/item/item.js"   ,
				 "Customer" : "custom_script/customer/customer.js"  ,
				  "Sales Order" : "custom_script/sales_order/sales_order.js",
				  "Stock Entry":"custom_script/stock_entry/stock_entry.js",
				"Work Order":"custom_script/work_order/work_order.js",
				"POS Invoice":"custom_script/pos_invoice/pos_invoice.js"     ,
				"POS Opening Entry":"custom_script/pos_opeing_entry/pos_opening_entry.js",
				"POS Closing Entry":"custom_script/pos_closing_entry/pos_closing_entry.js"   ,
				"Purchase Order":"custom_script/purchase_order/purchase_order.js" ,
				"Purchase Receipt":"custom_script/purchase_receipt/purchase_receipt.js" ,    
				"Purchase Invoice":"custom_script/purchase_invoice/purchase_invoice.js"   ,
				"Selling Settings":"custom_script/selling_settings/selling_settings.js"   ,
				"Sales Invoice":"custom_script/sales_invoice/sales_invoice.js"  ,
				"Product Bundle":"custom_script/product_bundle/product_bundle.js"   ,
				"Payment Entry":"custom_script/payment_entry/payment_entry.js"  ,
				"Material Request":"custom_script/material_request/material_request.js",   
				"Repost Item Valuation" : "custom_script/repost_item_valuation/repost_item_valuation.js",
				 "Employee" : "custom_script/employee/employee.js"  ,
				  "Coupon Code" : "custom_script/coupon_code/coupon_code.js"  ,
				  "Promotional Scheme" : "custom_script/promotional_scheme/promotional_scheme.js"  ,
   

}

doctype_py = {
				"Work Order":"custom_script/work_order/work_order.py"     
}
# include js, css files in header of web template
web_include_css = ["/assets/vim/css/vim.css","/assets/vim/css/vim-website.css"]
# web_include_js = "/assets/vim/js/vim.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "vim/public/scss/website"

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

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "vim.install.before_install"
# after_install = "vim.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "vim.notifications.get_notification_config"

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

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"POS Invoice": "vim.custom_script.pos_invoice.pos_invoice.CustomPOSInvoice",
	"Item": "vim.custom_script.item.item.CustomItem",
	"Communication":"vim.custom_script.communication.email.Customemail",
	"Payment Entry": "vim.custom_script.payment_entry.payment_entry.CustomPaymentEntry"

}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
	
	"Sales Order": {
		"before_submit": "vim.custom_script.sales_order.sales_order.before_submit",
		"on_cancel": "vim.custom_script.sales_order.sales_order.on_cancel",
		"on_submit": "vim.invoice_billing.onSumbmitinvoiceSync",

	},
	 "POS Invoice": {
		"on_submit": "vim.custom_script.pos_invoice.pos_invoice.on_submit",
		"before_cancel": "vim.custom_script.pos_invoice.pos_invoice.on_cancel",
		"validate": "vim.custom_script.pos_invoice.pos_invoice.validate"
	},
	 "Work Order": {
		"validate": "vim.custom_script.work_order.work_order.validate"
	},
	  "Contact": {
		"validate": "vim.custom_script.contact.contact.validate"
	},
	  "Customer": {
		"validate": "vim.custom_script.customer.customer.validate",
		"on_update": "vim.custom_script.customer.customer.reset_syncedflag",
		# "after_insert" :"vim.custom_script.customer.customer.after_insert"
	},
	"Item": {
		"validate": "vim.custom_script.item.item.validate",
	},
	 "Coupon Code": {
		#"after_insert": "vim.custom_script.coupon_code.coupon_code.after_insert",
		"validate": "vim.custom_script.coupon_code.coupon_code.validate",
	},
	#  "POS Closing Entry": {
	#     "before_update_after_submit": "vim.custom_script.pos_closing_entry.pos_closing_entry.before_update_after_submit",
	#     "on_submit": "vim.custom_script.pos_closing_entry.pos_closing_entry.on_submit",
		
	# },

 }

# Scheduled Tasks
# ---------------

scheduler_events = {
	"cron": {
		# Sync data to salesforce every 5 minutes
		"*/5 * * * *": [
            #"vim.api.send_renew_sms",
			"vim.vim.doctype.salesforce_integration.salesforce_integration.syncCustomer",
		    "vim.vim.doctype.salesforce_integration.salesforce_integration.syncCustomerFamily",
		    "vim.vim.doctype.salesforce_integration.salesforce_integration.syncOrders",
		    "vim.vim.doctype.salesforce_integration.salesforce_integration.syncInvoices",
			"vim.vim.doctype.salesforce_integration.salesforce_integration.syncItems",
			"vim.vim.doctype.salesforce_integration.salesforce_integration.updateItems",

		]
		
	},
	"monthly_long": [
		"vim.custom_script.employee.employee.generate_coupon"
	],
	"daily":[
		"vim.vim.doctype.biostar_settings.biostar_settings.syn_attendance"
	]
}
# Testing
# -------

# before_tests = "vim.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"erpnext.e_commerce.shopping_cart.product_info.get_product_info_for_website": "vim.api.get_product_info_for_website",
	"erpnext.e_commerce.shopping_cart.cart.update_cart": "vim.api.update_cart",
	"erpnext.e_commerce.shopping_cart.cart.place_order": "vim.api.place_order",
	"erpnext.selling.doctype.sales_order.sales_order.make_work_orders": "vim.custom_script.sales_order.sales_order.make_work_orders",
	"frappe.core.doctype.user.user.sign_up": "vim.api.sign_up",
	"frappe.core.doctype.user.user.update_password": "vim.api.update_password"
}
#f
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "vim.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"vim.auth.validate"
# ]

# from frappe.core.doctype.communication.email import email


# def prepare_to_notify(doc, print_html=None, print_format=None, attachments=None):
# 		frappe.throw("shhhhhhhhhhhh")
# 		"""Prepare to make multipart MIME Email

# 		:param print_html: Send given value as HTML attachment.
# 		:param print_format: Attach print format of parent document."""

# 		view_link = frappe.utils.cint(frappe.db.get_value("System Settings", "System Settings", "attach_view_link"))

# 		if print_format and view_link:
		
# 			doc.content = get_attach_link(doc, print_format)

# 		set_incoming_outgoing_accounts(doc)

# 		if not doc.sender:
# 			doc.sender = doc.outgoing_email_account.email_id

# 		if not doc.sender_full_name:
# 			doc.sender_full_name = doc.outgoing_email_account.name or _("Notification")

# 		if doc.sender:
# 			# combine for sending to get the format 'Jane <jane@example.com>'
# 			doc.sender = get_formatted_email(doc.sender_full_name, mail=doc.sender)

# 		doc.attachments = []

# 		if print_html or print_format:
# 			doc.attachments.append({"print_format_attachment":1, "doctype":doc.reference_doctype,
# 				"name":doc.reference_name, "print_format":print_format, "html":print_html})

# 		if attachments:
# 			if isinstance(attachments, string_types):
# 				attachments = json.loads(attachments)

# 			for a in attachments:
# 				if isinstance(a, string_types):
# 					# is it a filename?
# 					try:
# 						# check for both filename and file id
# 						file_id = frappe.db.get_list('File', or_filters={'file_name': a, 'name': a}, limit=1)
# 						if not file_id:
# 							frappe.throw(_("Unable to find attachment {0}").format(a))
# 						file_id = file_id[0]['name']
# 						_file = frappe.get_doc("File", file_id)
# 						_file.get_content()
# 						# these attachments will be attached on-demand
# 						# and won't be stored in the message
# 						doc.attachments.append({"fid": file_id})
# 					except IOError:
# 						frappe.throw(_("Unable to find attachment {0}").format(a))
# 				else:
# 					doc.attachments.append(a)


# email.prepare_to_notify = prepare_to_notify
# import vim.custom_script.sales_invoice.sales_invoice
# from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals
# calculate_taxes_and_totals.calculate_outstanding_amount = vim.custom_script.sales_invoice.sales_invoice.calculate_outstanding_amount

import erpnext.selling.doctype.customer.customer as _erp_customer
import vim.custom_script.customer.customer as _vim_customer
_erp_customer.make_contact = _vim_customer.make_contact


import erpnext.controllers.queries as _erp_itemqry
import vim.custom_script.stock_entry.stock_entry as _vim_itemqry
_erp_itemqry.item_query = _vim_itemqry.item_query

import erpnext.portal.utils as _erp_utils
import vim.api as _vim_api
_erp_utils.party_exists = _vim_api.party_exists


import  frappe.core.doctype.user.user as _erp_user
_erp_user.create_contact = _vim_api.create_contact

_erp_user.create_party_contact = _vim_api.create_party_contact

_erp_user.create_customer_or_supplier = _vim_api.create_customer_or_supplier

from  frappe.core.doctype.user.user import User
User.reset_password = _vim_api.reset_password
