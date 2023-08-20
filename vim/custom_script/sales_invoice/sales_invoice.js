// var send_invoice_sms=0;
// var sales_invoice=0;
{% include 'erpnext/selling/sales_common.js' %};
frappe.provide("erpnext.accounts");
frappe.ui.form.on('Sales Invoice', {
    refresh:function(frm){
      
    //    frappe.db.get_single_value('Selling Settings', 'send_invoice_sms').then(function(val) {
    //     send_invoice_sms=val;
    // });
      
    // frappe.db.get_single_value('Selling Settings', 'sales_invoice').then(function(val) {
    //     sales_invoice=val;
    // });
  
    },
    is_pos: function(frm){
        console.log("customapp")
		//this.set_pos_data();
	},
    set_pos_data: function() {
		if(this.frm.doc.is_pos) {
			this.frm.set_value("allocate_advances_automatically", 1);
			if(!this.frm.doc.company) {
				this.frm.set_value("is_pos", 0);
				frappe.msgprint(__("Please specify Company to proceed"));
			} else {
				var me = this;
				return this.frm.call({
					doc: me.frm.doc,
					method: "erpnext.accounts.doctype.sales_invoice.sales_invoice.set_missing_values",
					callback: function(r) {
						if(!r.exc) {
							if(r.message && r.message.print_format) {
								me.frm.pos_print_format = r.message.print_format;
							}
							me.frm.trigger("update_stock");
							if(me.frm.doc.taxes_and_charges) {
								me.frm.script_manager.trigger("taxes_and_charges");
							}

							frappe.model.set_default_values(me.frm.doc);
							me.set_dynamic_labels();
							me.calculate_taxes_and_totals();
						}
					}
				});
			}
		}
		else this.frm.trigger("refresh");
	},
    hide_fields: function(frm) {
		let doc = frm.doc;
		var parent_fields = ['project', 'due_date', 'is_opening', 'source', 'get_advances',
		 'from_date', 'to_date'];

		if(cint(doc.is_pos) == 1) {
			hide_field(parent_fields);
		} else {
			for (var i in parent_fields) {
				var docfield = frappe.meta.docfield_map[doc.doctype][parent_fields[i]];
				if(!docfield.hidden) unhide_field(parent_fields[i]);
			}
		}

		// India related fields
		if (frappe.boot.sysdefaults.country == 'India') unhide_field(['c_form_applicable', 'c_form_no']);
		else hide_field(['c_form_applicable', 'c_form_no']);

		frm.toggle_enable("write_off_amount", !!!cint(doc.write_off_outstanding_amount_automatically));

		frm.refresh_fields();
	},
    set_dynamic_labels: function() {
		this._super();
		this.frm.events.hide_fields(this.frm)
	},
    validate: function() {
       // this.calculate_total_advance();
		//this.frm.refresh_fields();
    }
    // on_submit:function(frm){
    //     if(frm.doc.docstatus==1)
    //     {
    //         frm.trigger("make_dialog")
    //     }
        
    // },
    // make_dialog:function(frm){
     
    //     console.log(send_invoice_sms,sales_invoice)
    //     if(send_invoice_sms==1 && sales_invoice==1){
    //         frappe.call({
    //             method: "frappe.client.get_value",
    //             args: {
    //             "doctype": "Customer",
    //             "filters": {"name":frm.doc.customer},
    //             "fieldname": "mobile_no"
    //             }, callback: function(r) {
                
    //             const dialog = new frappe.ui.Dialog({
    //                 title: __('Send sms to'),
    //                 static: true,
    //                 fields: [
    //                     {
    //                         fieldtype: 'Link', label: __('Customer'), fieldname: 'customer_name',
    //                         options: 'Customer', reqd: 1,default:frm.doc.customer,read_only:1
    //                     },
    //                     {
    //                         fieldtype: 'Int', label: __('Mobile No'),
    //                          fieldname: 'mobile_no', reqd: 1,default:r.message["mobile_no"]
    //                     },
                      
    //                 ],
    //                 primary_action: async function({ customer_name,mobile_no }) {
    //                             console.log(mobile_no,customer_name)
                                
    //                     // me.update_discount_approval(discount, remarks);
    //                     dialog.hide();
    //                 },
    //                 primary_action_label: __('Submit')
    //             });
    //             dialog.show();
    //             }});
    //     }
       
    // }
})
frappe.ui.form.on('Sales Invoice Item', {
    sales_order_no: function(frm, cdt, cdn){
        var d = locals[cdt][cdn];
        console.log("sales_order_no",d.sales_order_no)
        
        frappe.model.set_value(d.doctype, d.name, 'sales_order', d.sales_order_no);	
        frm.refresh_fields("items")
    }

})