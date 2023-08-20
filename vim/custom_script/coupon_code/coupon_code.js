frappe.ui.form.on('Coupon Code', {
    refresh:function(frm){
        
        frappe.db.get_value("Employee", {"user_id":frappe.session.user} ,"allow_create_coupon", (r)=> {
            console.log(r.allow_create_coupon)
            if(r.allow_create_coupon){
                set_field_options("coupon_type", ["Gift Card"])
                frm.set_value("valid_from", frappe.datetime.now_date())
                console.log(new Date(new Date().getFullYear(), 11, 31).toISOString().slice(0, 10), frappe.datetime.now_date())
                frm.set_value("valid_upto", new Date(new Date().getFullYear(), 11, 31).toISOString().slice(0, 10))
                frm.set_df_property("valid_from","read_only",1)
                frm.set_df_property("valid_upto","read_only",1)
            }
           // 

        })
        
    },
   
})