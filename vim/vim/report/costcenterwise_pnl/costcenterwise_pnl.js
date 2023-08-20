// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.require("assets/erpnext/js/financial_statements.js", function() {
	// frappe.query_reports["Wakame Profit and Loss Statement"] = $.extend({},
	// 	erpnext.financial_statements);


	frappe.query_reports["Costcenterwise PNL"]={
		"filters": [
			{
				"fieldname":"company",
				"label": __("Company"),
				"fieldtype": "Link",
				"options": "Company",
				"default": frappe.defaults.get_user_default("Company"),
				"reqd": 1
			},
			// {
			// 	"fieldname":"finance_book",
			// 	"label": __("Finance Book"),
			// 	"fieldtype": "Link",
			// 	"options": "Finance Book"
			// },
			{
				"fieldname":"filter_based_on",
				"label": __("Filter Based On"),
				"fieldtype": "Select",
				"options": [ "Date Range"],
				"default": ["Date Range"],
				"reqd": 1,
				on_change: function() {
					let filter_based_on = frappe.query_report.get_filter_value('filter_based_on');
					frappe.query_report.toggle_filter_display('from_fiscal_year', filter_based_on === 'Date Range');
					frappe.query_report.toggle_filter_display('to_fiscal_year', filter_based_on === 'Date Range');
					frappe.query_report.toggle_filter_display('period_start_date', filter_based_on === 'Fiscal Year');
					frappe.query_report.toggle_filter_display('period_end_date', filter_based_on === 'Fiscal Year');
	
					frappe.query_report.refresh();
				}
			},
			{
				"fieldname":"period_start_date",
				"label": __("Start Date"),
				"fieldtype": "Date",
				"reqd": 1,
				"depends_on": "eval:doc.filter_based_on == 'Date Range'"
			},
			{
				"fieldname":"period_end_date",
				"label": __("End Date"),
				"fieldtype": "Date",
				"reqd": 1,
				"depends_on": "eval:doc.filter_based_on == 'Date Range'"
			},
			{
				"fieldname":"from_fiscal_year",
				"label": __("Start Year"),
				"fieldtype": "Link",
				"options": "Fiscal Year",
				"default": frappe.defaults.get_user_default("fiscal_year"),
				"reqd": 1,
				"depends_on": "eval:doc.filter_based_on == 'Fiscal Year'"
			},
			{
				"fieldname":"to_fiscal_year",
				"label": __("End Year"),
				"fieldtype": "Link",
				"options": "Fiscal Year",
				"default": frappe.defaults.get_user_default("fiscal_year"),
				"reqd": 1,
				"depends_on": "eval:doc.filter_based_on == 'Fiscal Year'"
			},
			{
				"fieldname": "periodicity",
				"label": __("Periodicity"),
				"fieldtype": "Select",
				"options": [
					{ "value": "Monthly", "label": __("Monthly") },
					{ "value": "Quarterly", "label": __("Quarterly") },
					{ "value": "Half-Yearly", "label": __("Half-Yearly") },
					{ "value": "Yearly", "label": __("Yearly") }
				],
				"default": "Yearly",
				"reqd": 1,
				"hidden":1
			},
			// Note:
			// If you are modifying this array such that the presentation_currency object
			// is no longer the last object, please make adjustments in cash_flow.js
			// accordingly.
			// {
			// 	"fieldname": "presentation_currency",
			// 	"label": __("Currency"),
			// 	"fieldtype": "Select",
			// 	"options": erpnext.get_presentation_currency_list()
			// },
			{
				"fieldname": "cost_center",
				"label": __("Cost Center"),
				"fieldtype": "MultiSelectList",
				get_data: function(txt) {
					return frappe.db.get_link_options('Cost Center', txt, {
						company: frappe.query_report.get_filter_value("company")
					});
				}
			},
		// {
		// 	"fieldname": "project",
		// 	"label": __("Project"),
		// 	"fieldtype": "MultiSelectList",
		// 	get_data: function(txt) {
		// 		return frappe.db.get_link_options('Project', txt);
		// 	}
		// },
		// {
		// 	"fieldname": "include_default_book_entries",
		// 	"label": __("Include Default Book Entries"),
		// 	"fieldtype": "Check",
		// 	"default": 1
		// },
		{
			"fieldname": "show_cost_center",
			"label": __("Show Cost Center Wise"),
			"fieldtype": "Check",
			"default":1,
			on_change: function() {
				if( frappe.query_report.get_filter_value('show_cost_center')){
									frappe.query_report.set_filter_value('cost_center',[]);
								}
								frappe.query_report.refresh();
			}
		}
	],
	"formatter":erpnext.financial_statements.formatter,
		"tree": true,
		"name_field": "account",
		"parent_field": "parent_account",
		"initial_depth": 3
	}
	erpnext.utils.add_dimensions('Profit and Loss Statement', 10);

});
