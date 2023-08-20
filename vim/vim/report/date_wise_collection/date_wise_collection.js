// Copyright (c) 2016, aavu and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Date wise collection"] = {
	"filters": [
		// {
		// 	"fieldname":"from_date",
		// 	"label": __("From Date"),
		// 	"fieldtype": "Date",
		// 	"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		// 	"reqd": 1,
		// 	"width": "60px"
		// },
		// {
		// 	"fieldname":"to_date",
		// 	"label": __("To Date"),
		// 	"fieldtype": "Date",
		// 	"default": frappe.datetime.get_today(),
		// 	"reqd": 1,
		// 	"width": "60px"
		// },
		// {
		// 	"fieldname":"closing_id",
		// 	"label": __("Closing ID"),
		// 	"fieldtype": "Link",
		// 	"options":'POS Closing Entry',
		// 	get_query: function () {
		// 		return {
		// 			filters: {
		// 				docstatus: 1,
		// 			},
		// 		};
		// 	},
		// },
		// {
		// 	"fieldname":"cash_method",
		// 	"label": __("Payment Cash"),
		// 	"fieldtype": "Link",
		// 	"options":'Mode of Payment',
		// 	get_query: function () {
		// 		return {
		// 			filters: {
		// 				type: "Cash",
		// 			},
		// 		};
		// 	},
			
		// },
		// {
		// 	"fieldname":"card_method",
		// 	"label": __("Payment Card"),
		// 	"fieldtype": "Link",
		// 	"options":'Mode of Payment',
		// 	get_query: function () {
		// 		return {
		// 			filters: {
		// 				type: "Bank",
		// 			},
		// 		};
		// 	},
			
		// },
		// {
		// 	"fieldname":"cost_center",
		// 	"label": __("Cost Center"),
		// 	"fieldtype": "Link",
		// 	"options":'Cost Center',
		// },
		// {
		// 	"fieldname":"cashier",
		// 	"label": __("Cashier"),
		// 	"fieldtype": "Link",
		// 	"options":"User"
		// },
		{
			"fieldname":"date",
			"label": __("Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "60px"
		},
       
		
	],
};
