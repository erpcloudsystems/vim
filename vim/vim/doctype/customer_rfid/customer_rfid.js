// Copyright (c) 2022, aavu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer RFID', {
	refresh: function(frm) {
       set_readonly(frm)
       if(frm.doc.__islocal==1){
            
            frm.set_df_property('add_gusts', 'hidden', 1) 
            frm.set_df_property('no_of_gusts', 'hidden', 1) 
       }
       else{
            frm.set_df_property('add_gusts', 'hidden', 0) 
            frm.set_df_property('no_of_gusts', 'hidden', 0) 
       }

	},
    setup: function (frm, cdt, cdn) {
        var child = locals[cdt][cdn];       
		cur_frm.add_fetch('pos_invoice',  'customer', 'customer');
        cur_frm.add_fetch('pos_invoice',  'sales_order', 'sales_order');
        cur_frm.set_query('pos_invoice', function () {
            return {
                filters: {
                    'rfid_attached': 0

                }
            }
        })
        if(child.family_member){
            frm.set_df_property('rfid', 'reqd', 1) 
        }
        else{
            frm.set_df_property('rfid', 'reqd', 0) 
        }
    },
    pos_invoice:function(frm){
        if(frm.doc.customer && frm.doc.pos_invoice)
        {    if(frm.doc.gust_detail && frm.doc.gust_detail.length>0)   
            {
                cur_frm.get_field("gust_detail").grid.grid_rows[0].remove();  
            }     
            
            var gust_detail = []
            frappe.call({
                "method": "vim.vim.doctype.customer_rfid.customer_rfid.get_family_details",
                args:{"customer":frm.doc.customer},
                async: false,
                callback: function (r) {
                 
                    gust_detail = (r.message['familyllist'] || []);
                  
               
                    if (gust_detail.length > 0) {
    
                        Object.entries(gust_detail).forEach(([key, value]) => {
    
                            var row = cur_frm.fields_dict["gust_detail"].grid.add_new_row()
                            frappe.model.set_value(row.doctype, row.name, "gust_name", value["person_name"])
                            frappe.model.set_value(row.doctype, row.name, "phone_no", value["phone_no"])
                            frappe.model.set_value(row.doctype, row.name, "family_member", 1)
                            cur_frm.set_df_property('pos_invoice', 'read_only', 1) 
    
    
                        });
                        cur_frm.refresh_field('gust_detail')
                    }
    
                }
            });
        }
        else{
           // cur_frm.clear_table("gust_detail")
           // cur_frm.refresh_field("gust_detail")
        }
        
    },
    
    add_gusts:function(frm){
        
        if(frm.doc.no_of_gusts>0)
        {
            if (frm.doc.gust_detail.length>0) {
                var check_gust = cur_frm.doc.gust_detail.filter(item => 
                (item.family_member === 0));
                if(check_gust.length==0){
                    cur_frm.refresh_field('gust_detail')       
                    for(var i =1 ; i<=frm.doc.no_of_gusts ; i++)
                    {
                        var row = cur_frm.fields_dict["gust_detail"].grid.add_new_row()
                        frappe.model.set_value(row.doctype, row.name, "gust_name", 'Guest-'+String(i))
                    }
                    cur_frm.refresh_field('gust_detail')
                }
                
            }
            else{
                
                cur_frm.refresh_field('gust_detail')  
                for(var i =1 ; i<=frm.doc.no_of_gusts ; i++)
                    {
                        var row = cur_frm.fields_dict["gust_detail"].grid.add_new_row()
                        frappe.model.set_value(row.doctype, row.name, "gust_name", 'Guest-'+String(i))
                    }
                    cur_frm.refresh_field('gust_detail')

            }
            set_readonly(frm)
            // frappe.call({
            //     method: "add_child",
			// 	doc: frm.doc,
            //     callback: function (r, rt) {
            //         cur_frm.refresh_field('gust_detail')
            //         frm.refresh_field()
            //     }
            // });
        }
        else{
            frappe.throw("enter no of gusts")
        }
        
    },
    validate:function(frm){
        var tbl_del = frm.doc.gust_detail || [];
        var d = tbl_del.length;
         while (d--) {
            if(frm.doc.gust_detail[d].family_member && !frm.doc.gust_detail[d].rfid){               
                frappe.validated=false;
                frappe.throw("Enter RFID");
            }
             else if(!frm.doc.gust_detail[d].rfid ){
                 frm.get_field("gust_detail").grid.grid_rows[d].remove();
                    frm.refresh_field("gust_detail")
                    frappe.validated=true;
                }
                
            }
            if(cur_frm.doc.__islocal){
                frappe.call({
                    method: "frappe.client.get_value",
                    args: {
                        doctype: 'POS Invoice',
                        fieldname: ['name'],
                        filters: { rfid_attached: '0',name:cur_frm.doc.pos_invoice},
                    },
                    callback: function (r) {
                        console.log	(r.message,"msg")
                        if(r.message.name)	{
                            frappe.validated=true;
    
                        }	
                        else{
                            frappe.validated=false;
                            frappe.throw("Duplicate POS Invoice Entry")
                        //     cur_frm.set_value('pos_invoice',  undefined)
                        //     cur_frm.set_value('customer',  undefined)
                        //     cur_frm.set_value('sales_order',  undefined)
                        //    cur_frm.clear_table("gust_detail")
                        //    cur_frm.refresh_field("gust_detail")
    
                            
                        }	
                            
                            
                        }
                        
                });
            }
           
    },
    
});
frappe.ui.form.on('Customer RFID Child', {
    gust_detail_remove: function(frm,cdt,cdn) {
        set_readonly(frm)      
        
    },
    gust_detail_delete: function(frm,cdt,cdn) {
        set_readonly(frm)
        
    },
    
   
    // before_gust_detail_remove: function(frm,cdt,cdn) {
       
    //     var child = locals[cdt][cdn];
    //     frappe.call({
    //         method: "remove_child",            
	// 		doc: frm.doc,
    //         args: {               
    //             docname: child.name
    //         },
            
    //     });
        
    // },
    // before_gust_detail_delete: function(frm,cdt,cdn) {
       
    //     var child = locals[cdt][cdn];
        
    //     frappe.call({
    //         method: "remove_child",            
	// 		doc: frm.doc,
    //         args: {               
    //             docname: child.name
    //         },
           
    //     });
    // },
    rfid: function(frm,cdt,cdn) {
       
        var child = locals[cdt][cdn]; 
        var check_item = frm.doc.gust_detail.filter(item => 
            (item.rfid === child.rfid && child.name!=item.name));
            if(check_item.length>0)
            {   
                //frappe.model.set_value(child.doctype, child.name , "rfid",  undefined);
                child.rfid=''
                frm.refresh_field('gust_detail')
                 frappe.throw("Duplicate RFID  ")
            }  
            else{
                if(child.rfid && child.rfid!=''){
                    frappe.call({
                        method: "updte_rfid",            
                        doc: frm.doc,
                        args: {               
                            docname: child.name,
                            rfid: child.rfid,
                            gust_name: child.gust_name,
                            idx: child.idx
            
                            
                        }
                    });

                }
                
            }  
       
    }

})
function set_readonly(frm)
{
    if(frm.doc.gust_detail && frm.doc.gust_detail.length>0){
        if(frm.doc.pos_invoice && frm.doc.gust_detail.length>0){
            frm.set_df_property('pos_invoice', 'read_only', 1) 
        }
        else{
            frm.set_df_property('pos_invoice', 'read_only', 0) 
        }
        if(frm.doc.no_of_gusts>0 && frm.doc.gust_detail.length>0){
            
            frm.set_df_property("no_of_gusts","read_only",1)
        }
        else{
            frm.set_df_property("no_of_gusts","read_only",0)
        }

    }
    
}
function check_duplicate(frm, cdt, cdn) {
    var child =locals[cdt][cdn];
    if(child.rfid && child.gust_name)
         {
            var check_item = frm.doc.gust_detail.filter(item => 
                (item.rfid === child.rfid && item.idx!=child.idx));
                if(check_item.length>0)
                {
                   
                   return true;
                }
         }
        
            return false;
    

}