frappe.ui.form.on('Item', {
    refresh:function(frm){
       
    },
    setup:function(frm){
        frm.set_query("extended_possible_item", function() {
            return {
                "filters": {
                    "is_sales_item":1
                }
            };
        });
        frm.set_query("uom","slot_list", function(frm,cdt,cdn) {
            var uom_list = [];
            for (var i = 0;i<cur_frm.doc.uoms.length;i++){
                uom_list.push(cur_frm.doc.uoms[i].uom)
            }
            console.log(uom_list)
            if (uom_list.length>0)
            return {
                "filters": {
                    "name":["in",uom_list]
                }
            };
            else return {}
        });
    },
  
    extended_possible_item:function(frm){
        
        var item = frappe.get_doc("Item", frm.doc.extended_possible_item);
        
        if(item){
            if (item.is_sales_item==0){
                frm.set_value("extended_possible_item","")
            }
        }
    },
    allowed_hrs:function(frm){
        
        if (frm.doc.allowed_hrs < 0){
            frm.set_value("allowed_hrs","")
        }
    },
    extra_allowed_hrs:function(frm){
        
        if (frm.doc.extra_allowed_hrs < 0){
            frm.set_value("extra_allowed_hrs","")
        }
    },
    minimum_sales_quantity:function(frm){
        
        if (frm.doc.minimum_sales_quantity < 0){
            frm.set_value("minimum_sales_quantity",0)
        }
    },
    maximum_usage_count:function(frm){
        
        if (frm.doc.maximum_usage_count < 0){
            frm.set_value("maximum_usage_count",0)
        }
    },
    maximum_sales_quantity:function(frm){
        
        if (frm.doc.maximum_sales_quantity < frm.doc.minimum_sales_quantity){
            frm.set_value("maximum_sales_quantity",frm.doc.minimum_sales_quantity)
            frappe.throw("Maximum Sales Quantity should be greater or equal to Minimum Sales Quantity");
        }
    },
    validate : function(frm){
        if (frm.doc.maximum_sales_quantity < frm.doc.minimum_sales_quantity){
            frm.set_value("maximum_sales_quantity",frm.doc.minimum_sales_quantity)
            frappe.throw("Maximum Sales Quantity should be greater or equal to Minimum Sales Quantity");
        }
    }
});
