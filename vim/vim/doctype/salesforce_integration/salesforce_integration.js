// Copyright (c) 2022, aavu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Salesforce Integration', {
	refresh: function(frm) {
		cur_frm.add_custom_button("Test Sales Order Upload",function(){
			frappe.call({
				method: 'vim.vim.doctype.salesforce_integration.salesforce_integration.syncOrders',
				callback:(r) => {
						console.log(r);
				}
			});
		});
		cur_frm.add_custom_button("Test Customer Upload",function(){
			frappe.call({
				method: 'vim.vim.doctype.salesforce_integration.salesforce_integration.syncCustomer',
				callback:(r) => {
						console.log(r);
				}
			});
		});
		cur_frm.add_custom_button("Test Sales Invoice Upload",function(){
			frappe.call({
				method: 'vim.vim.doctype.salesforce_integration.salesforce_integration.syncInvoices',
				callback:(r) => {
						console.log(r);
				}
			});
		});
	}
});
