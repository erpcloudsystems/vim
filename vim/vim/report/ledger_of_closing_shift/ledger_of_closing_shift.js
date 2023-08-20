// Copyright (c) 2016, aavu and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Ledger of closing shift"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1,
			// "hidden":1,
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"closing_id",
			"label": __("Closing ID"),
			"fieldtype": "Link",
			"options": "POS Closing Entry",
			"width": "60px"
		},
		{
			"fieldname":"against_account",
			"label": __("Against Account"),
			"fieldtype": "Link",
			"options": "Account",
			"width": "60px"
		},


	]
}

// erpnext.utils.add_dimensions('General Ledger', 15)

