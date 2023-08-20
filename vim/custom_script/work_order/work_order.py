# -*- coding: utf-8 -*-
# Copyright (c) 2021, Avu and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from collections import OrderedDict
from frappe import _
from frappe.model.document import Document

# @frappe.whitelist()
def validate(self,method):
	# check_asset_name(self)
	set_reusable_items(self)

@frappe.whitelist()
def check_asset_name(item_code):
	if frappe.db.exists({"doctype":"Asset","item_code":item_code}) :
				return {"asset":True}
	else :
				return {"asset":False}
			

def set_reusable_items(self):
	if self.bom_no and self.reusable_items == [] :
		items = get_item_list(self.bom_no)
		maximum_usage_count = 0
		used_count =0 
		balance_count =0
		for item in items:
			if not frappe.db.exists({"doctype":"Asset","item_code":item}):
				item_doc = frappe.get_doc("Item",{"item_code":item})
				maximum_usage_count = item_doc.maximum_usage_count
				used_count = item_doc.used_count
				balance_count = maximum_usage_count-used_count
			self.append('reusable_items', {
				"item_code": item,
				"maximum_usage_count":maximum_usage_count,
				"used_count":used_count,
				"balance_count":balance_count
			})


@frappe.whitelist()
def get_item_list(bom):
	result_list = []
	bom_doc = frappe.get_doc("BOM",bom)
	for item in bom_doc.items:
		item = frappe.get_doc("Item",{"item_code":item.item_code})
		if item  and item.reusable_item:
			result_list.append(item.item_code)

	# unitdetail= frappe.db.sql(unitdetail, as_dict=True)	
	# for tkt in unitdetail:
	# 	unitdetail_data = OrderedDict()
	# 	unitdetail_data['name'] = tkt.get('name') or ''				
	# 	result_list.append(unitdetail_data)
	
	return result_list	

@frappe.whitelist()
def get_asset_list(doctype, txt, searchfield, start, page_len, filters):
	# frappe.errprint([filters,"""select name from `tabAsset` where maximum_usage_count > used_count and item_code = '{}'""".format(filters["item_code"])])
	return frappe.db.sql("""select name from `tabAsset` where maximum_usage_count > used_count and item_code ='{}'""".format(filters["item_code"]))
