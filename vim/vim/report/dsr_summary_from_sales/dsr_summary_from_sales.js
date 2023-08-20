// Copyright (c) 2016, aavu and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["DSR Summary From Sales"] = {
    "filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_days(frappe.datetime.get_today(), -1),
			"width": "80"
		},
        {
			"fieldname":"posting_time",
			"label": __("Time From"),
			"fieldtype": "Time",
			"default": "06:00:00",
			"reqd": 1,
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
        {
			"fieldname":"posting_timeto",
			"label": __("Time to"),
			"fieldtype": "Time",
			"default": "06:00:00",
			"reqd": 1,
		},
        {
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname":"cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center"
		},
	]
};
