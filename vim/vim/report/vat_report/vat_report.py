# Copyright (c) 2013, aavu and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import json
from vim.vim.report.utils import get_columns, get_values_list

def execute(filters=None):
	if not filters: filters = {}

	# dict=frappe.db.sql("Select * from `VATReport_GLEntry_Final` where `01#Posting Date:Date:100`>=(%s) and `01#Posting Date:Date:100`<=(%s) ", (filters['from_date'], filters['to_date']), as_dict=1)
	# dict = "call VAT_Report('', {0}, {1}, {2})".format(filters.get('from_date'), filters.get('to_date'), json.dumps(filters.get("grouping_for_vat_report")))
	# frappe.errprint(dict)
	sql="call VAT_Report({0}, {1}, {2}, {3})".format(json.dumps(filters.get('company')), json.dumps(filters.get('from_date')), json.dumps(filters.get('to_date')), json.dumps(filters.get("grouping_for_vat_report")))
	frappe.errprint(str(sql))
	dict = frappe.db.sql("call VAT_Report({0}, {1}, {2}, {3})".format(json.dumps(filters.get('company')), json.dumps(filters.get('from_date')), json.dumps(filters.get('to_date')), json.dumps(filters.get("grouping_for_vat_report"))), as_dict=1)
	
	
	columns = get_columns(dict)
	data = get_values_list(dict)
	frappe.errprint(str(data))
	frappe.errprint(str(columns))
	return columns, data
