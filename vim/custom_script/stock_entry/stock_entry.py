# -*- coding: utf-8 -*-
# Copyright (c) 2021, Avu and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from collections import OrderedDict
from frappe import _
from frappe.model.document import Document
from frappe.desk.reportview import get_match_cond, get_filters_cond
from frappe.utils import nowdate, getdate


@frappe.whitelist()
def get_batch_list(warehouse=None,item_code=None):
	result_list = []
	batch_list = """select B.name 'batch_no',B.expiry_date 'expiry_date',sum(SL.actual_qty) 'available_qty',0 'qty' from `tabBatch` as B 
				inner join `tabStock Ledger Entry` as SL on SL.batch_no=B.name
				where B.item_name='{0}' and B.batch_qty> 0 and SL.warehouse='{1}' group by B.name order by B.expiry_date asc""".format(item_code,warehouse)
	
	batchlist= frappe.db.sql(batch_list, as_dict=True)	
	
	return batchlist	

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def item_query(doctype, txt, searchfield, start, page_len, filters, as_dict=False):
	conditions = []
	
	#Get searchfields from meta and use in Item Link field query
	meta = frappe.get_meta("Item", cached=True)
	searchfields = meta.get_search_fields()

	if "description" in searchfields:
		searchfields.remove("description")
	
	columns = ''
	extra_searchfields = [field for field in searchfields
		if not field in ["name", "item_group", "description"]]

	if extra_searchfields:
		columns = ", " + ", ".join(extra_searchfields)

	searchfields = searchfields + [field for field in[searchfield or "name", "item_code", "item_group", "item_name"]
		if not field in searchfields]
	searchfields = " or ".join([field + " like %(txt)s" for field in searchfields])
	if filters !=None:
		if filters.get('supplier'):
			item_group_list = frappe.get_all('Supplier Item Group', filters = {'supplier': filters.get('supplier')}, fields = ['item_group'])
			
			item_groups = []
			for i in item_group_list:
				item_groups.append(i.item_group)

			del filters['supplier']

			if item_groups:
				filters['item_group'] = ['in', item_groups]
		
	description_cond = ''
	if frappe.db.count('Item', cache=True) < 50000:
		# scan description only if items are less than 50000
		description_cond = 'or tabItem.description LIKE %(txt)s'
	return frappe.db.sql("""select tabItem.name,
		if(length(tabItem.item_name) > 40,
			concat(substr(tabItem.item_name, 1, 40), "..."), item_name) as item_name,
		tabItem.item_group,
		if(length(tabItem.description) > 40, \
			concat(substr(tabItem.description, 1, 40), "..."), description) as description
		{columns}
		from tabItem
		where tabItem.docstatus < 2
			and tabItem.disabled=0
			and tabItem.has_variants=0
			and (tabItem.end_of_life > %(today)s or ifnull(tabItem.end_of_life, '0000-00-00')='0000-00-00')
			and ({scond} or tabItem.item_code IN (select parent from `tabItem Barcode` where barcode LIKE %(txt)s)
				{description_cond})
			{fcond} {mcond}
		order by
			if(locate(%(_txt)s, name), locate(%(_txt)s, name), 99999),
			if(locate(%(_txt)s, item_name), locate(%(_txt)s, item_name), 99999),
			idx desc,
			name, item_name
		limit %(start)s, %(page_len)s """.format(
			columns=columns,
			scond=searchfields,
			fcond=get_filters_cond(doctype, filters, conditions).replace('%', '%%'),
			mcond=get_match_cond(doctype).replace('%', '%%'),
			description_cond = description_cond),
			{
				"today": nowdate(),
				"txt": "%%%s%%" % txt,
				"_txt": txt.replace("%", ""),
				"start": start,
				"page_len": page_len
			}, as_dict=as_dict)

