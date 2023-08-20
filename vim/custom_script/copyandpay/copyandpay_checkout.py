
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint
import json
from six import string_types


@frappe.whitelist(allow_guest=True)
def make_payment(copyandpay_payment_id, options, reference_doctype, reference_docname, token,checkoutid):
	data = {}

	if isinstance(options, string_types):
		data = json.loads(options)

	data.update({
		"copyandpay_payment_id": copyandpay_payment_id,
		"reference_docname": reference_docname,
		"reference_doctype": reference_doctype,
		"token": token,
		"checkoutid":checkoutid
	})
	
	data =  frappe.get_doc("CopyandPay Settings").create_request(data)
	frappe.db.commit()
	return data
