frappe.ui.form.on("Product Bundle Item", {
    refresh: (frm,cdt,cdn) => {
        var child = locals[cdt][cdn];
		// if(child.item){
    },
    form_render: (frm,cdt,cdn) =>{
        var child = locals[cdt][cdn];
		if(child.default_item_in_pos == 1){
            frappe.utils.filter_dict(cur_frm.fields_dict["items"].grid.grid_rows_by_docname[cdn].docfields, {"fieldname": "set_no"})[0].hidden = true;
        }
        else {
            frappe.utils.filter_dict(cur_frm.fields_dict["items"].grid.grid_rows_by_docname[cdn].docfields, {"fieldname": "set_no"})[0].hidden = false;

        }
        cur_frm.refresh_fields();
    },
    default_item_in_pos: (frm,cdt,cdn) => {
        var child = locals[cdt][cdn];
		if(child.default_item_in_pos == 1){
            frappe.utils.filter_dict(cur_frm.fields_dict["items"].grid.grid_rows_by_docname[cdn].docfields, {"fieldname": "set_no"})[0].hidden = true;
            child.set_no = 0;
        }
        else {
            frappe.utils.filter_dict(cur_frm.fields_dict["items"].grid.grid_rows_by_docname[cdn].docfields, {"fieldname": "set_no"})[0].hidden = false;

        }
        cur_frm.refresh_fields();
    },
    item_code: function(frm, cdt, cdn)
        {
        var d = locals[cdt][cdn];
        if(d.item_code)
        frappe.call(
        {
        method: "vim.custom_script.product_bundle.product_bundle.get_rate",
        args: {
        price_list: "Standard Buying",
        item_code: d.item_code,
        item_group: d.item_group,
        uom:d.uom
        },
        callback: function(r)
        {
        if(r.message)
        {
        var item_price = r.message;
        frm.set_value(d.rate = item_price);
        }  
        }
        });
        if(d.item_code && d.qty && (d.default_item_in_pos || d.set_no)){
            cur_frm.trigger("total_cost_update");
            if(d.rate)
            d.amount = d.rate * d.qty;
            else{
                d.rate = 0;
                d.amount = 0;
            }
        }
        },
    qty:  function(frm, cdt, cdn)
    {
        var d = locals[cdt][cdn];
        if(d.item_code && d.qty  && (d.default_item_in_pos || d.set_no)){
            cur_frm.trigger("total_cost_update");
            if(d.rate)
            d.amount = d.rate * d.qty;
            else{
                d.rate = 0;
                d.amount = 0;
            }
        }
    },
    set_no:  function(frm, cdt, cdn)
    {
        var d = locals[cdt][cdn];
        if(d.item_code && d.qty  && (d.default_item_in_pos || d.set_no)){
            cur_frm.trigger("total_cost_update");
            if(d.rate)
            d.amount = d.rate * d.qty;
            else{
                d.rate = 0;
                d.amount = 0;
            }
        }
    },
    items_remove: function(frm) {
        cur_frm.trigger("total_cost_update");

     }
});
frappe.ui.form.on("Product Bundle", {
    total_cost_update:  function(frm)
    {   var total =0;
        var set =[];
        var set_max =[];
        for(var i=0;i<cur_frm.doc.items.length;i++)
        {
            if(cur_frm.doc.items[i].default_item_in_pos)
            total+= cur_frm.doc.items[i].rate*cur_frm.doc.items[i].qty;
            else {
                    if(set.indexOf(cur_frm.doc.items[i].set_no) !== -1){
                        if(set_max[set.indexOf(cur_frm.doc.items[i].set_no)] < cur_frm.doc.items[i].rate*cur_frm.doc.items[i].qty){
                            set_max[set.indexOf(cur_frm.doc.items[i].set_no)] = cur_frm.doc.items[i].rate*cur_frm.doc.items[i].qty;
                        }
                    }
                    else{
                        set.push(cur_frm.doc.items[i].set_no);
                        set_max.push(cur_frm.doc.items[i].rate*cur_frm.doc.items[i].qty);
                    }
            }
        }
        console.log(set,set_max);
        for(var i=0;i<set_max.length;i++)
        {
            total+= set_max[i];

        }
        cur_frm.doc.total_cost=total;
        cur_frm.refresh_fields();
    },
    update_rate:function(frm)
    {
        frm.trigger("total_cost_update")
        frm.dirty();
        // frm.trigger("item_code")
        //var d=cur_frm.doc.items
        for(var i=0;i<cur_frm.doc.items.length;i++){

            // var item  = cur_frm.doc.items[i].item_code;
            // cur_frm.doc.items[i].item_code = item;
            // cur_frm.doc.items[i].trigger("item_code")

            if(cur_frm.doc.items[i].item_code)
            frappe.call(
            {
            method: "vim.custom_script.product_bundle.product_bundle.get_rate",
            args: {
            price_list: "Standard Buying",
            item_code: cur_frm.doc.items[i].item_code,
            item_group: cur_frm.doc.items[i].item_group,
            uom:cur_frm.doc.items[i].uom
            },
            async:false,
            always: function(r)
            {
            if(r.message)
            {
            var item_price = r.message;
            cur_frm.doc.items[i].rate = item_price;
            }  
            }
            });
            if(cur_frm.doc.items[i].item_code && cur_frm.doc.items[i].qty &&
                 (cur_frm.doc.items[i].default_item_in_pos || cur_frm.doc.items[i].set_no)){
                //cur_frm.trigger("total_cost_update");
                if(cur_frm.doc.items[i].rate)
                cur_frm.doc.items[i].amount = cur_frm.doc.items[i].rate * cur_frm.doc.items[i].qty;
                else{
                    cur_frm.doc.items[i].rate = 0;
                    cur_frm.doc.items[i].amount = 0;
                }
            }
        }
        frm.refresh_fields();
    },


});
