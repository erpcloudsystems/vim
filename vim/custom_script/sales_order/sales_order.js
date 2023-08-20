frappe.ui.form.on('Sales Order', {
    onload_post_render:function(frm){
        frm.set_query("item_code", "items", function() {
            
            return {
                query: "erpnext.controllers.queries.item_query",
                filters: {'is_sales_item': 1, 'is_fixed_asset':0,
                'is_stock_item':1,
                'has_variants':0}
            }
        });
    },
   setup:function(frm){
    frm.set_query("select_event", function() {
            
        return {
            query: "vim.custom_script.sales_order.sales_order.get_item_list",
            filters: {'is_sales_item': 1, 'is_fixed_asset':0,
            'is_stock_item':1,
            'has_variants':0}
        }
    });
   },
    refresh:function(frm){
        if(frm.doc.docstatus == 1){
            frm.add_custom_button(__('Resend Invoice'), function(){
                if(!frm.doc.payment_invoice_id){
                    frappe.msgprint({message:"Invoice not created.", title:"Validation", indicator:"orange"});
                    return;
                }
    
                frappe.call({
                    method: "vim.invoice_billing.send_invoice_link",
                    args: {
                        "inv_id" : frm.doc.payment_invoice_id
                    },
                    callback: function(r) {
                        if(r.message == true){
                            frappe.msgprint({message:"Link sent successfully.", title:"Success", indicator:"green"})
                        }
                        else{
                            frappe.msgprint({message:"Some error while trying to send invoice link.", title:"Error", indicator:"red"})
                        }
                    }
                });
            }, __("HyperBill"));
            
            frm.add_custom_button(__('Create New Invoice'), function(){
    
                if(!frm.doc.advance_amount || frm.doc.advance_amount == 0){
                    frappe.msgprint({message:"No advance amount specified for payment.", title:"Validation", indicator:"orange"});
                    return;
                }
    
                frappe.call({
                    method: "vim.invoice_billing.recreate_invoice",
                    args: {
                        "doc_name" : frm.doc.name
                    },
                    callback: function(r) {
                        console.log(r);
                        frappe.msgprint({message:"Invoice created and link sent successfully.", title:"Hyperbill", indicator:"green"})
                    }
                });
            }, __("HyperBill"));
        }

        if(frm.doc.__islocal==1 && (cur_frm.doc.amended_from ==undefined)){
            frm.doc.items=[]
        }
      
    //    frm.trigger("item_list_value")
       const fieldname_arr = ['item_code','item_name','delivery_date','qty','uom','description','against_blanket_order','ensure_delivery_based_on_produced_serial_no','additional_notes','delivered_by_supplier','suppplier','rate'];
       cur_frm.fields_dict['items'].grid.grid_rows.forEach((grid_row)=> {
           // check if is it sub-item (not group)
         
           if (grid_row.doc.is_nonsharable_item === 1) {
              
               grid_row.docfields.forEach((df)=>{
                  
                   if (fieldname_arr.includes(df.fieldname)) {
                     
                       df.read_only=1;    // remove bold text formatting
                   }
               });
           } 
       });
       frm.refresh_field('items');
       
        
    },
    before_submit:function(frm){
        if(frm.doc.delivery_date==undefined || (frm.doc.select_event==undefined || frm.doc.select_event=="")){
            frappe.throw("Please Enter Visit Date,Select Event")
            validated=false;
            return true
        }
        if(cur_frm.doc.select_event==undefined || frm.doc.select_event==""){
            frappe.throw("Please Select Event")
            validated=false;
            return true
        }
        // if(cur_frm.doc.select_slot==undefined){
        //     frappe.throw("Please Select Slot")
        //     validated=false;
        //     return true
        // }
    },
    validate:function(frm){
        if(frm.doc.items){
            
            var items=frm.doc.items;
            for(var i=0;i<items.length;i++){
                
                if(items[i]["delivery_date"]=="" || items[i]["delivery_date"]==undefined){
                    frappe.throw("Please Enter Visit Date In Items Row No("+items[i]["idx"]+")")
                    validated=false;
                    return true
                }
            }
        }
    },
    item_list_value: function(frm) {
		var unit_list_data=[];var unitlist=[];var isnew=0;
    
        frappe.call({
            "method": "vim.custom_script.sales_order.sales_order.get_item_list",
            async: true,
            callback: function (r) {
                unit_list_data = (r.message['result_list'] || []);
				Object.entries(unit_list_data).forEach(([key, value]) => {
					var item = "";
					item=(value["name"]);
					unitlist.push(item);
				});
				frm.set_df_property('select_event', 'options', unitlist);
            }})
    },
    select_event:function(frm){
        var unit_list_data=[];var unitlist=[];var isnew=0;
        if(frm.doc.__islocal){
            isnew=1
        }
        if(frm.doc.delivery_date==undefined){
            frappe.throw("Please enter visit date")
        }
        if(!frm.doc.select_event){
            frm.set_value("event_name","")
        }
        if (frm.doc.select_event){
            frappe.call({
                "method": "vim.custom_script.sales_order.sales_order.get_slot_list",
                async: true,
                args:{item_name:frm.doc.select_event,is_new:isnew,delivery_date:frm.doc.delivery_date},
                callback: function (r) {
                    
                    unit_list_data = (r.message['result_list'] || []);
                    Object.entries(unit_list_data).forEach(([key, value]) => {
                        var item = "";
                        item=(value["slot_name"]);
                        unitlist.push(item);
                    });
                    frm.set_df_property('select_slot', 'options', unitlist);
                }})
        }
       
    },
    customer:function(frm){
        if(frm.doc.customer){
            frappe.call({
                "method": "vim.custom_script.sales_order.sales_order.get_family_details",
                async: true,
                args:{customer_name:frm.doc.customer},
                callback: function (r) {
                   
                    if (r.message)
                    {
                        var data=r.message;
                        cur_frm.clear_table("so_family_detail");
                        cur_frm.refresh_fields("so_family_detail");
                        if (data){
                            for(var i=0;i<data.length;i++){
                                var childTable = cur_frm.add_child("so_family_detail");
                                childTable.person_name= data[i]["person_name"]
                                childTable.relation= data[i]["relation"]
                                childTable.dob= data[i]["dob"]
                            }
                            cur_frm.refresh_fields("so_family_detail");
                        }
                       
                    }
                    
                }})
        }
      
    },
    no_of_entries:function(frm){

        frappe.call({
            method:"frappe.client.get_value",
            args: {
            doctype:"Item",
            filters: {
            name: cur_frm.doc.select_event
            },
            fieldname:"minimum_sales_quantity"
            },
            callback: function(r) {
            if(r.message){
                
                if(r.message.minimum_sales_quantity > 0)
                {
                    if (frm.doc.no_of_entries < r.message.minimum_sales_quantity){
                        cur_frm.set_value("no_of_entries","0")
                        frappe.throw("No of entries can't be less thane minimum sales quantity")
                    }
                }
            }
        }
       
    });
    
    },
    delivery_date:function(frm){
        frm.set_value("select_event","")
        frm.set_value("select_slot","")
    },
    // is_nonsharable_item  
    add_in_row:function(frm){
        var list=frm.doc.items;
        if (list){
            var items = $.grep(list, function(element, index) {
                return element.is_nonsharable_item == 1;
                
            });
            if(items){
                if(items.length>0){
                    frappe.throw("Item("+items[0]["item_code"]+") already added. Can not add more than 1 item ")
                }
            }
        }
        if (! cur_frm.doc.select_event && !cur_frm.doc.no_of_entries){
            frappe.throw("Please Select Event & Enter No of entries")
        }
        frappe.call({
            "method": "vim.custom_script.sales_order.sales_order.get_item_details",
            async: true,
            args:{item_name:frm.doc.select_event},
            callback: function (r) {
               
                if (r.message)
                {
                    var data=r.message;
                  
                    if (data){
                        data=data['result_list'][0]
                        if(data.non_sharable_slot==1){
                            if(!frm.doc.select_slot){
                                frappe.throw("Please select slot")
                            }
                        }
                        var row = cur_frm.fields_dict["items"].grid.add_new_row()
		                frappe.model.set_value(row.doctype, row.name, "item_code", data.item_code)
                        frappe.model.set_value(row.doctype, row.name, "item_name",  data.item_name)
                        frappe.model.set_value(row.doctype, row.name, "uom",data.stock_uom)
                        frappe.model.set_value(row.doctype, row.name, "stock_uom", data.stock_uom)
                        frappe.model.set_value(row.doctype, row.name, "is_nonsharable_item",1)
                        frappe.model.set_value(row.doctype, row.name, "qty",cur_frm.doc.no_of_entries)
                        frappe.model.set_value(row.doctype, row.name, "slot_name",cur_frm.doc.select_slot)
                        
                        cur_frm.refresh_fields("items");
                        const fieldname_arr = ['item_code','item_name','delivery_date','qty','uom','description','against_blanket_order','ensure_delivery_based_on_produced_serial_no','additional_notes','delivered_by_supplier','suppplier','rate'];
                        cur_frm.fields_dict['items'].grid.grid_rows.forEach((grid_row)=> {
                            // check if is it sub-item (not group)
                        
                            if (grid_row.doc.is_nonsharable_item === 1) {
                              
                                grid_row.docfields.forEach((df)=>{
                                  
                                    if (fieldname_arr.includes(df.fieldname)) {
                                     
                                        df.read_only=1;    // remove bold text formatting
                                    }
                                });
                            } 
                        });
                        frm.refresh_field('items');
                        
                    }
                   
                }
                
            }})
        
    },
    // items_add:function(frm){
    //     frm.set_query("item_code", "items", function() {
    //         console.log('setqs')
    //         return {
    //             query: "erpnext.controllers.queries.item_query",
    //             filters: {'is_sales_item': 1, 'is_fixed_asset':0,
    //             'is_stock_item':1,
    //             'has_variants':0}
    //         }
    //     });
    // }
});
frappe.ui.form.on('Sales Order Item', {

    before_items_remove :function(frm,cdt,cdn){
        var row = frappe.get_doc(cdt, cdn);
        
        if (row.is_nonsharable_item==1){
            frappe.throw(__("Can't Delete Item ("+row.item_code+")"));
        }
        
    }

});
