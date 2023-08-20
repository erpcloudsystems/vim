from __future__ import unicode_literals
import frappe, json
from frappe.utils.nestedset import get_root_of
from frappe.utils import cint
from erpnext.accounts.doctype.pos_profile.pos_profile import get_item_groups
from erpnext.accounts.doctype.pos_invoice.pos_invoice import get_stock_availability

from six import string_types
@frappe.whitelist()
def get_Item(so):
	# frappe.errprint(str("get_record"))
	if so:
		return frappe.db.sql("SELECT name from tabItem where name =(select select_event FROM `tabSales Order` where name='{0}' ".format(so), as_dict=True)
	else:
		return frappe.db.sql("SELECT name from tabItem where allowed_hrs>0 or non_sharable_slot=1 ", as_dict=True)

		