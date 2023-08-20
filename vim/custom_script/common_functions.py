from __future__ import unicode_literals
import frappe
from collections import OrderedDict
from frappe import _
from erpnext.controllers.queries import *
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
### filter for item according to supplier in po,pr,pi by Tushar 21-10-2021
def item_query(doctype, txt, searchfield, start, page_len, filters, as_dict=False):
	conditions = []
	sup_cond = ''
	if filters.get("supplier") and filters.get("supplier") != '' :
		item_list =  frappe.db.sql("""
		select distinct parent as name 
		from `tabItem Supplier` where parenttype = 'Item'
		and supplier = "{}"
		""".format(
				filters.get("supplier", "")
			))
		if len(item_list) == 0 :
			frappe.msgprint("No Items found for given supplier")
			return {}
		sup_cond = " and name in (" 
		for item in item_list:
			if item != item_list[0] : sup_cond += " ,"
			sup_cond += "'" +item[0].replace("'","''") + "'"
		sup_cond += ")"
	else : 	return {}
	if isinstance(filters, str):
		filters = json.loads(filters)

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

	if filters and isinstance(filters, dict) and filters.get('supplier'):
		item_group_list = frappe.get_all('Supplier Item Group',
			filters = {'supplier': filters.get('supplier')}, fields = ['item_group'])

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
			{fcond} {mcond} {sup_cond}
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
			sup_cond = sup_cond,
			description_cond = description_cond),
			{
				"today": nowdate(),
				"txt": "%%%s%%" % txt,
				"_txt": txt.replace("%", ""),
				"start": start,
				"page_len": page_len
			}, as_dict=as_dict)

