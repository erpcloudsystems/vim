// Copyright (c) 2016, aavu and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Closing Shift report - sales invoice wise"] = {
	"filters": [
		{
			"fieldname":"closing_id",
			"label": __("Closing ID"),
			"fieldtype": "Link",
			"options":'POS Closing Entry',
			get_query: function () {
				return {
					filters: {
						docstatus: 1,
					},
				};
			},
		},
		{
			"fieldname":"cashier",
			"label": __("Cashier"),
			"fieldtype": "Link",
			"options":"User"
		},
       
		
	],
	// "formatter": function(value, row, column, data, default_formatter) {
	// 	value = default_formatter(value, row, column, data);
	// 	if (data && data.bold) {
	// 		value = value.bold();

	// 	}
	// 	return value;
	// }
};
