frappe.ui.form.on('POS Closing Entry', {
	onload:function(frm){
		if (cur_frm.doc.__islocal == 1 ) {
			$.each(cur_frm.doc.payment_reconciliation, function (i, v) {
            frappe.db.get_doc("Mode of Payment", v.mode_of_payment)
			.then(({ type }) => {
                if(type=="Cash"){
                    frappe.model.set_value(v.doctype, v.name, "closing_amount", frm.doc.cash_closing_amont)
                }
                else{
                    frappe.model.set_value(v.doctype, v.name, "closing_amount", v.expected_amount)
                }
				
            })
			});
			cur_frm.refresh_fields()
		}
	},
    pos_opening_entry(frm) {
		frm.set_value("change_amount",0)
		for (let row of frm.doc.pos_transactions) {
			frappe.db.get_doc("POS Invoice", row.pos_invoice).then(doc => {
				frm.doc.change_amount += flt(doc.change_amount);
				refresh_payments_pos(frm);
				
			});
		}
	},
   
	before_save: function(frm) {
        frappe.freeze
        frm.set_value("change_amount",0)
		for (let row of frm.doc.pos_transactions) {
			
			frappe.db.get_doc("POS Invoice", row.pos_invoice).then(doc => {
				if(doc.change_amount>0){
					frm.doc.change_amount += flt(doc.change_amount);
				}
				
				refresh_payments_pos(frm);
				
			});
		}
        
		frappe.unfreeze
	},
    validate:function(frm){
        frappe.freeze
        if(calculate_total(frm)){
            frappe.validate=true
        }
        else{
            frameElement.validate=false
            frappe.unfreeze

            frappe.throw("Difference in calculated and selected amount.Please try Again.........",)
        }
        frappe.unfreeze


    }
   
})
frappe.ui.form.on('POS Closing Entry Detail', {
	closing_amount: (frm, cdt, cdn) => {
		
		const row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "difference", flt(row.expected_amount- row.closing_amount-row.change_amount));
		
	}
})

function refresh_payments_pos( frm) {
	
	frm.doc.payment_reconciliation.forEach(p => {
		
		if (p) {
			frappe.db.get_value("Mode of Payment", p.mode_of_payment ,"type", (r)=> {
				if(r.type=="Cash"){
					 frappe.model.set_value(p.doctype, p.name , "change_amount", frm.doc.change_amount?frm.doc.change_amount:0);
					 frappe.model.set_value(p.doctype, p.name , "difference", frm.doc.difference-frm.doc.change_amount?frm.doc.change_amount:0);
					
					
				}
			}
			)
            
			

			//payment.difference = payment.closing_amount - payment.expected_amount;
		} 
	})
	
	frm.refresh_field("payment_reconciliation");
}
async function calculate_total(frm) {
    var grand_total=0;var net_total=0;var i=0;var retval=true;
    for (let row of frm.doc.pos_transactions) {
          
        await frappe.db.get_value("POS Invoice", row.pos_invoice ,["grand_total","net_total"], (r)=> {
        
        grand_total+=parseFloat(r.grand_total)
        net_total+=parseFloat(r.net_total)
        console.log(i,frm.doc.pos_transactions.length)
       
        
    })  
    
    
}

console.log(grand_total,frm.doc.grand_total, net_total,frm.doc.net_total,"bar")
if(grand_total!=frm.doc.grand_total || net_total!=frm.doc.net_total)
{  
    retval=false   
}
return retval
}
  
