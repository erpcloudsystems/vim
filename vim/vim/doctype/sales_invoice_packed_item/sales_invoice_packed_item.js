// Copyright (c) 2022, aavu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Invoice Packed Item', {
	
    update_ledger_entry: function(frm) {
       
        frappe.call({
            // "method": "vim.vim.doctype.sales_invoice_packed_item.sales_invoice_packed_item.update_stock_ledger",
            "method": "vim.vim.doctype.sales_invoice_packed_item.sales_invoice_packed_item.update_stock_ledger_bundle",
            
            freeze: true,
            args: {
				voucher_no: frm.doc.voucher_no
			},
            callback: function (r) {
                
                
            }})


	 },
    //  update_packed_item:function(frm) {
        
    //      frappe.call({
    //         method: "vim.vim.doctype.sales_invoice_packed_item.sales_invoice_packed_item.update_packed_item",
    //         freeze: true,
    //         callback: function (r, rt) {
               
    //             if(r && r.message){
                   
                    
    //             }
    //         }
    //     });

	//  },
     make_gl_entries:function(frm) {
        
        frappe.call({
           method: "vim.vim.doctype.sales_invoice_packed_item.sales_invoice_packed_item.make_gl_entries_bundle",
           freeze: true,
           callback: function (r, rt) {
              
               if(r && r.message){
               
                   
               }
           }
       });

    },
    update_bundle_double_qty:function(frm) {
        
        frappe.call({
           method: "vim.vim.doctype.sales_invoice_packed_item.sales_invoice_packed_item.update_bundle_double_qty",
           freeze: true,
           callback: function (r, rt) {
              
               if(r && r.message){
               
                   
               }
           }
       });

    },
});
