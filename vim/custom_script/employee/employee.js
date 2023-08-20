frappe.ui.form.on('Employee', {
    refresh:function(frm){
        cur_frm.add_custom_button(__('Generate Coupon')	,function(){
            if(!cur_frm.doc.__islocal){
            if(frm.doc.allow_gift_coupon){
                frappe.call({
                    method: "vim.custom_script.employee.employee.generate_coupon",
                    args:{employee:cur_frm.doc.name},
                    callback: function(r) {
                        // console.log(r);
                        frappe.msgprint("Done. Coupon Created");
                        cur_frm.refresh()
                    }
                });
            }
            else{
                frappe.throw("The employee does not have coupon privileges.")
            }
           
        }
         },
        );
         if(frm.doc.availed_coupons!=0){
            cur_frm.set_df_property('allow_create_coupon', 'read_only', 1)
         }
    },
    validate:function(frm){
        if(frm.doc.allow_create_coupon && !frm.doc.allowed_coupons>0){
            frappe.throw("Enter Allowed Coupon Count.")

        }

    },
    allow_create_coupon:function(frm){
        if(!frm.doc.allow_create_coupon && frm.doc.availed_coupons==0 ){
            frm.doc.allowed_coupons=0

        }

    },
    generate_coupon:function(){
        if(!cur_frm.doc.__islocal){

        }
    },
})