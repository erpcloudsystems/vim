frappe.ui.form.on('POS Opening Entry', {
    refresh:function(frm){
		console.log("pos Opening")
        cur_frm.fields_dict["balance_details"].grid.wrapper.find('.grid-add-row').hide();
    },
    setup: function (frm, cdt, cdn) {
		cur_frm.set_query("mode_of_payment", "balance_details", function (doc, cdt, cdn) {
			var d = locals[cdt][cdn];
			return {
				filters: [
					['Mode of Payment', 'type', '=', 'Cash']
				]
			}
		});
    },
    pos_profile: (frm) => {
        var payment_type=''
		if (frm.doc.pos_profile) {
			frappe.db.get_doc("POS Profile", frm.doc.pos_profile)
				.then(({ payments }) => {
					if (payments.length) {
						frm.doc.balance_details = [];
						payments.forEach(({ mode_of_payment }) => {
                            frappe.db.get_value('Mode of Payment', mode_of_payment, 'type').then(({ message }) => {
                             
                            if(String(message.type)=='Cash')
                            {
                                console.log(String(message.type),mode_of_payment,"mode_of_payment")
							    frm.add_child("balance_details", { mode_of_payment });
                                frm.refresh_field("balance_details");
                            }
                        });
                       
						})
						
					}
				});
		}
	}
})