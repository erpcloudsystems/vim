
var in_apply_price_list=true
frappe.ui.form.on("POS Invoice",{
    
    setup:function(frm) {
        console.log("pos_profile")
		frm.add_fetch('pos_profile', 'dimension_brand', 'brand');
        frm.add_fetch('pos_profile', 'dimension_department',  'department');
        frm.add_fetch('pos_profile', 'dimension_city',  'city');
        frm.add_fetch('pos_profile', 'dimension_branch',  'branch');
        
    },
    // pos_profile:function(frm)
    // {
    //     frm.add_fetch('pos_profile',  'brand', 'dimension_brand');
    //     frm.add_fetch('pos_profile',  'department', 'dimension_department');
    //     frm.add_fetch('pos_profile',  'city', 'dimension_city');
    //     frm.add_fetch('pos_profile',  'branch', 'dimension_branch');
       
    // },
    actual_entry_time:function(frm){
      
        frappe.call({
            method: "vim.custom_script.pos_invoice.pos_invoice.get_item",
            args: {
                doc: cur_frm.doc,
                
            },
            callback: function (r) {
                if (r && r.message) {
                    console.log(r.message)
                    cur_frm.doc.expected_finish_time=r.message
                    console.log(cur_frm.doc.expected_finish_time)
                }
                cur_frm.refresh_fields()
            }
        });
        // $.each(cur_frm.doc.items,function(i,v){

        // })
        // frappe.model.get_value('Item', {'name': cur_frm.doc.items[0].item_code},
        // function(d) { 
        //     console.log(d)
            
        // }) 
    },
    apply_coupon_code:function(frm){
        frm.events.apply_coupon(this)
        //frm.set_value("coupon_code",cur_frm.doc.couponcode)

    },
    apply_coupon: function(btn) {
        console.log(cur_frm.doc.set_warehouse)
		return frappe.call({
			type: "POST",
			method: "vim.custom_script.point_of_sale.point_of_sale.apply_coupon_code",
            async:false,
			btn: btn,
			args : {
                doc:cur_frm.doc,
				applied_code : cur_frm.doc.couponcode,
				applied_referral_sales_partner: '',
                warehouse:cur_frm.doc.set_warehouse
                
			},
			callback: function(r) {
				if (r && r.message){
                    
                    var me = this;
                    frappe.run_serially([
                        () => cur_frm.doc.ignore_pricing_rule=1,
                        //() => cur_frm.ignore_pricing_rule(),
                        () => cur_frm.doc.ignore_pricing_rule=0,
                        () => cur_frm.events.apply_pricing_rule(cur_frm.doc.items)
                    ]);
					
				}
			}
		});
	
   
    
},
 apply_pricing_rule: function(item) {
       // console.log("applypricing")
		var me = this;
		var args = _get_args(item);
		
		return frappe.call({
			method: "vim.custom_script.point_of_sale.point_of_sale.apply_pricing_rule",
			args: {	args: args, doc: cur_frm.doc },
            async:false,
			callback: function(r) {
                
				if (!r.exc && r.message) {
                    cur_frm.set_value("applied_coupen",cur_frm.doc.couponcode)
                   
					_set_values_for_item_list(r.message);
					if(item) set_gross_profit(item);
					// if(cur_frm.doc.apply_discount_on) cur_frm.trigger("apply_discount_on")
				}
			}
		});
	},
    trigger_price_list_rate: function() {
		var me  = this;

		cur_frm.doc.items.forEach(child_row => {
			cur_frm.script_manager.trigger("price_list_rate",
				child_row.doctype, child_row.name);
		})
	},

})

frappe.ui.form.on("POS Invoice Item",{
    item_code:function(frm,cdt,cdn)
    {
        frm.refresh();
        //console.log("trigger")
       
            var child = locals[cdt][cdn];
          
            if(!child.group_no){
                frappe.model.set_value(child.doctype, child.name, "parent_item_row", child.idx)
            cur_frm.refresh_field('items')
            }
            
       
    },
    before_items_remove: function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
        console.log(frm.doc.items.length,"before_items_remove")
        if(!row.is_free_item){
            for (var i = frm.doc.items.length - 1; i >= 0; i--) {
            
                if(row && row.idx!=frm.doc.items[i].idx){
                    if (frm.doc.items[i].parent_item_row == row.parent_item_row ) {
                        console.log("before_items_remove")
                        cur_frm.get_field("items").grid.grid_rows[i].remove();
                        
                    }
                }
           
                cur_frm.refresh_field('items')
        }
        }
		
	},
    items_remove: function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
        console.log(frm.doc.items.length,"before_items_remove")
        
            for (var i = frm.doc.items.length - 1; i >= 0; i--) {
            
                if(row && row.idx!=frm.doc.items[i].idx){
                    if (frm.doc.items[i].parent_item_row == row.parent_item_row ) {
                        console.log("before_items_remove")
                        cur_frm.get_field("items").grid.grid_rows[i].remove();
                        
                    }
                }
           
                cur_frm.refresh_field('items')
        }
       
		
	},
    qty: function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
        if(row.qty==0) {
            for (var i = frm.doc.items.length - 1; i >= 0; i--) {
                console.log(frm.doc.items[i].parent_item_row,row.parent_item_row,frm.doc.items[i].item_code,"before_items_remove")
                if(row.idx!=frm.doc.items[i].idx){
                    if (frm.doc.items[i].parent_item_row == row.parent_item_row ) {
                        console.log("RMV",frm.doc.items[i].item_code)
                        cur_frm.get_field("items").grid.grid_rows[i].remove();
                        cur_frm.refresh_field('items')
                    }
                }
                
                
            }
        }
		
        
        
		

	},
    uom:function(frm,cdt,cdn)
    {
        //cur_frm.refresh_fields(uom);
       // cur_frm.refresh_fields(uom)
        //console.log("trigger")
        
    },
    conversion_factor:function(frm,cdt,cdn)
    {
        //cur_frm.refresh_fields(conversion_factor);
       // cur_frm.refresh_fields(uom)
        //console.log("trigger")
        
    },
    items_add:function(frm,cdt,cdn){
        console.log("addnew")
    }

})
function _get_args(item) {
    
    return {
        "items": _get_item_list(item),
        "customer": cur_frm.doc.customer || cur_frm.doc.party_name,
        "quotation_to": '',
        "customer_group": '',
        "territory": '',
        "supplier": '',
        "supplier_group": '',
        "currency": cur_frm.doc.currency,
        "conversion_rate": cur_frm.doc.conversion_rate,
        "price_list": cur_frm.doc.selling_price_list ,
        "price_list_currency": cur_frm.doc.price_list_currency,
        "plc_conversion_rate": cur_frm.doc.plc_conversion_rate,
        "company": cur_frm.doc.company,
        "transaction_date": cur_frm.doc.posting_date,
        "campaign": '',
        "sales_partner": '',
        "ignore_pricing_rule": 0,
        "doctype": cur_frm.doc.doctype,
        "name": cur_frm.doc.name,
        "is_return": cint(cur_frm.doc.is_return),
        "update_stock":  0,
        "conversion_factor": 1,
        "pos_profile":   '',
        "coupon_code": cur_frm.doc.couponcode
    };
}
function _get_item_list(item) {
    var item_list = [];
   
    var append_item = function(d) {
        if (d.item_code) {
            item_list.push({
                "doctype": d.doctype,
                "name": d.name,
                "child_docname": d.name,
                "item_code": d.item_code,
                "item_group": d.item_group,
                "brand": d.brand,
                "qty": d.qty,
                "stock_qty": d.stock_qty,
                "uom": d.uom,
                "stock_uom": d.stock_uom,
                "parenttype": d.parenttype,
                "parent": d.parent,
                "pricing_rules": d.pricing_rules,
                "warehouse": d.warehouse,
                "serial_no": d.serial_no,
                "batch_no": d.batch_no,
                "price_list_rate": d.price_list_rate,
                "conversion_factor": d.conversion_factor || 1.0
            });

            
        }
    };
    
  
        $.each(cur_frm.doc["items"] || [], function(i, d) {
            append_item(d);
        });
   
        
    return item_list;
}
function _set_values_for_item_list(children) {
    var me = this;
    var price_list_rate_changed = false;
    var items_rule_dict = {};

    for(var i=0, l=children.length; i<l; i++) {
        var d = children[i];
        var existing_pricing_rule = d.pricing_rules;
       
        for(var k in d) {
            var v = d[k];
            
            if (["doctype", "name"].indexOf(k)===-1) {
                if(k=="price_list_rate") {
                    console.log(k,"k====",d.price_list_rate)
                    if(flt(v) != flt(d.price_list_rate)) price_list_rate_changed = true;
                }

                if (k !== 'free_item_data') {
                    frappe.model.set_value(d.doctype, d.name, k, v);
                }
            }
        }
        console.log(children,d.pricing_rules,"existing_pricing_rule")
        // if pricing rule set as blank from an existing value, apply price_list
       
        if(existing_pricing_rule &&!cur_frm.doc.ignore_pricing_rule && !d.pricing_rules) {
            console.log(existing_pricing_rule ,cur_frm.doc.ignore_pricing_rule ,d.pricing_rules,"eeeeeeeeeeeeeeeeeeeeeeeee")
            apply_price_list(frappe.get_doc(d.doctype, d.name));
        } else if(!d.pricing_rules) {
            console.log(existing_pricing_rule ,cur_frm.doc.ignore_pricing_rule ,d.pricing_rules,"eeeeeeeeeeeeeeeeeeeeeeeee")
            remove_pricing_rule(frappe.get_doc(d.doctype, d.name));
        }
       

        if (d.free_item_data && d.free_item_data.length>0) {
            apply_product_discount(d);
        }

        if (d.apply_rule_on_other_items) {
            items_rule_dict[d.name] = d;
        }
    }

    apply_rule_on_other_items(items_rule_dict);

    //if(!price_list_rate_changed) calculate_taxes_and_totals();
}
function apply_price_list(item, reset_plc_conversion) {
    console.log("apply_price_listapply_price_list")
    if (!reset_plc_conversion) {
        cur_frm.set_value("plc_conversion_rate", "");
    }

    var me = this;
    var args = _get_args(item);
    if (!((args.items && args.items.length) || args.price_list)) {
        return;
    }
    console.log(in_apply_price_list,"me.in_apply_price_list")
    if (in_apply_price_list == true) return;

    in_apply_price_list = true;
    return frappe.call({
        method: "erpnext.stock.get_item_details.apply_price_list",
        args: {	args: args },
        callback: function(r) {
            if (!r.exc) {
                frappe.run_serially([
                    () => cur_frm.set_value("price_list_currency", r.message.parent.price_list_currency),
                    () => cur_frm.set_value("plc_conversion_rate", r.message.parent.plc_conversion_rate),
                    () => {
                        if(args.items.length) {
                            _set_values_for_item_list(r.message.children);
                        }
                    },
                    () => { in_apply_price_list = false; }
                ]);

            } else {
                in_apply_price_list = false;
            }
        }
    }).always(() => {
        in_apply_price_list = false;
    });
}
function remove_pricing_rule(item) {
    let me = this;
    const fields = ["discount_percentage",
        "discount_amount", "margin_rate_or_amount", "rate_with_margin"];

    if(item.remove_free_item) {
        var items = [];

        cur_frm.doc.items.forEach(d => {
            if(d.item_code != item.remove_free_item || !d.is_free_item) {
                items.push(d);
            }
        });

        cur_frm.doc.items = items;
        refresh_field('items');
    } else if(item.applied_on_items && item.apply_on) {
        const applied_on_items = item.applied_on_items.split(',');
        cur_frm.doc.items.forEach(row => {
            if(applied_on_items.includes(row[item.apply_on])) {
                fields.forEach(f => {
                    row[f] = 0;
                });

                ["pricing_rules", "margin_type"].forEach(field => {
                    if (row[field]) {
                        row[field] = '';
                    }
                })
            }
        });

        me.trigger_price_list_rate();
    }
}
function apply_product_discount(args) {
    console.log("apply_product_discount")
    const items = cur_frm.doc.items.filter(d => (d.is_free_item)) || [];

    const exist_items = items.map(row => (row.item_code, row.pricing_rules));

    args.free_item_data.forEach(pr_row => {
        let row_to_modify = {};
        if (!items || !in_list(exist_items, (pr_row.item_code, pr_row.pricing_rules))) {

            row_to_modify = frappe.model.add_child(cur_frm.doc,
                cur_frm.doc.doctype + ' Item', 'items');

        } else if(items) {
            row_to_modify = items.filter(d => (d.item_code === pr_row.item_code
                && d.pricing_rules === pr_row.pricing_rules))[0];
        }

        for (let key in pr_row) {
            row_to_modify[key] = pr_row[key];
        }
    });

    // free_item_data is a temporary variable
    args.free_item_data = '';
    refresh_field('items');
}
function apply_rule_on_other_items(args) {
    const me = this;
    const fields = ["discount_percentage", "pricing_rules", "discount_amount", "rate"];

    for(var k in args) {
        let data = args[k];

        if (data && data.apply_rule_on_other_items) {
            cur_frm.doc.items.forEach(d => {
                if (in_list(data.apply_rule_on_other_items, d[data.apply_rule_on])) {
                    for(var k in data) {
                        if (in_list(fields, k) && data[k] && (data.price_or_product_discount === 'price' || k === 'pricing_rules')) {
                            frappe.model.set_value(d.doctype, d.name, k, data[k]);
                        }
                    }
                }
            });
        }
    }
}
function set_gross_profit(item) {
    if (["Sales Order", "Quotation"].includes(cur_frm.doc.doctype) && item.valuation_rate) {
        var rate = flt(item.rate) * flt(cur_frm.doc.conversion_rate || 1);
        item.gross_profit = flt(((rate - item.valuation_rate) * item.stock_qty), precision("amount", item));
    }
}