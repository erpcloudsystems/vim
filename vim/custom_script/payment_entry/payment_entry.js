
frappe.ui.form.on('Payment Entry', {
    paid_to : function(frm){
        setTimeout(()=>{frm.toggle_reqd(["reference_no", "reference_date"],0);},100);
        
    },
    
});

