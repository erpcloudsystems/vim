// Copyright (c) 2022, aavu and contributors
// For license information, please see license.txt

frappe.ui.form.on('UPDATE POS CLOSING ENTRY', {
	update_closing: function(frm) {
        frappe.call({
            // "method": "vim.vim.doctype.sales_invoice_packed_item.sales_invoice_packed_item.update_stock_ledger",
            "method": "vim.vim.doctype.update_pos_closing_entry.update_pos_closing_entry.update_pos_closing_entry",
            
            freeze: true,
            args: {
				doc_no: frm.doc.name
			},
            callback: function (r) {
                
                
            }})
        console.log("hiiiiiiiiiiiii")

	}
});
