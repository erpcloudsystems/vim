# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import frappe.www.list

no_cache = 1

def get_context(context):
	# from erpnext.portal.utils import create_customer_or_supplier
	# create_customer_or_supplier()
	if frappe.session.user=='Guest':
		frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)
	context.show_sidebar=True

@frappe.whitelist()
def check_customer():
	# from erpnext.portal.utils import party_exists
	user = frappe.session.user
	# if party_exists("Customer", user):
	customer =None
	for d in frappe.get_list("Contact", fields=("name"), filters={"email_id": user}):
			contact_name = frappe.db.get_value("Contact", d.name)
			if contact_name:
				contact = frappe.get_doc('Contact', contact_name)
				doctypes = [d.link_doctype for d in contact.links]
				doc_name  = [d.link_name for d in contact.links]
				if  "Customer" in doctypes : 
					cust = doc_name[doctypes.index("Customer")]
					customer = frappe.get_doc('Customer', cust)
					customer = frappe.get_doc('Customer', cust)
					if not customer.first_name or not customer.last_name or not customer.mobile_no or not customer.city:
						return  "/customer_details"
	if not customer : return  "/customer_details"
	return '/'
				