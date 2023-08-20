frappe.ui.form.on('Work Order', {
    setup : function(frm){
        frm.fields_dict['reusable_items'].grid.get_field('asset_name').get_query = function(frm, cdt, cdn) {
			var child = locals[cdt][cdn];
			return{
                query: "vim.custom_script.work_order.work_order.get_asset_list",
				filters: {
					'item_code': child.item_code
                    // ,
					// 'maximum_usage_count': [">", "used_count"]
				}
			}
		}
        frm.fields_dict['reusable_items'].grid.get_field('item_code').get_query = function(frm, cdt, cdn) {
			var child = locals[cdt][cdn];
			return{
				filters: {
					'reusable_item': 1
				}
			}
		}
    },
    //  refresh:function(frm){
    //     if (frm.doc.fg_warehouse == frm.doc.source_warehouse){
    //         var set_source = false;
    //         if(frm.doc.required_items)
    //         for(var i = 0; i<frm.doc.required_items.length;i++)
    //         {
    //             if( frm.doc.required_items[i].source_warehouse){
    //                 set_source = true;
    //                 break; 
    //             }
                
    //         }
    //         else 
    //         set_source = true;        
    //         if(!set_source){
    //             frm.set_value('source_warehouse', "");
    //             frm.set_value('source_warehouse', frm.doc.fg_warehouse);
    //         }
    //     }
    // },
    sales_order:function(frm){
    if(frm.doc.sales_order){
    frappe.db.get_value('Sales Order', frm.doc.sales_order, 'set_warehouse' ,function(r) {
        frm.set_value('fg_warehouse', r.set_warehouse);
        frm.set_value('source_warehouse', r.set_warehouse);
        frm.set_value('wip_warehouse', r.set_warehouse);

        frm.refresh_fields();
      });

    }
    },
    bom_no:function(frm){
        frm.set_value('reusable_items', []);
        frm.refresh_fields();

        if(frm.doc.bom_no){
            console.log(frm.doc.bom_no,"bom")
            frappe.call({
                "method": "vim.custom_script.work_order.work_order.get_item_list",
                args:{bom:frm.doc.bom_no},
                async: true,
                callback: function (r) {
            console.log(r,"reusable")

                    for(var i =0 ; i<r.message.length;i++)
                    {var childTable = cur_frm.add_child("reusable_items");
                    childTable.item_code=r.message[i];
                    cur_frm.refresh_fields("reusable_items");}
                }})
        frm.refresh_fields();
        }
        },
    before_save:function(frm){
        if(frm.doc.reusable_items)
        for(var i = 0; i<frm.doc.reusable_items.length;i++)
        {
            console.log(i,"i");
            if(frm.doc.reusable_items[i].balance_count <= 0){
                frappe.validated = false;
                frappe.throw("Item with no balance at row  "+frm.doc.reusable_items[i].idx)
            }
            if(!frm.doc.reusable_items[i].asset_name)
            frappe.call({
            "method": "vim.custom_script.work_order.work_order.check_asset_name",
            args:{item_code:frm.doc.reusable_items[i].item_code},
            async: false,
            callback: function (r) {
                // if (r.message["error"]){
                    if(r.message["asset"]){
                       
                        // {
                            frappe.validated = false;
                            frappe.throw("Asset Name is mandatory for row "+frm.doc.reusable_items[i].idx)}
                    // }
                    //":"Asset Name is mandatory for row {}".format(item.idx)
                   // :"Item with no balance at row {}".format(item.idx)
                // }
            }})}
    }
 });

 frappe.ui.form.on('Reusable Items', {
    asset_name:function(frm , cdt ,cdn){
	var child = locals[cdt][cdn];
    // console.log(child.asset_name,"child.asset_name")
    if(child.asset_name){
         frappe.db.get_value('Asset', child.asset_name, ['maximum_usage_count','used_count'],
        function(r) {
            // console.log(r)
            var asset_value =r
            var maximum_usage_count = asset_value["maximum_usage_count"];
            var used_count = asset_value["used_count"];
            // console.log(asset_value,asset_value.message,maximum_usage_count,used_count)
            child.maximum_usage_count = maximum_usage_count;
            child.used_count = used_count;
            child.balance_count = maximum_usage_count-used_count;
            frm.refresh_fields();
          });
       
    }
    },
    item_code:function(frm , cdt ,cdn){
        var child = locals[cdt][cdn];
        // console.log(child.asset_name,"child.asset_name")
        if(child.item_code){
             frappe.db.get_value('Item', child.item_code, ['maximum_usage_count','used_count'],
            function(r) {
                // console.log(r)
                var asset_value =r
                var maximum_usage_count = asset_value["maximum_usage_count"];
                var used_count = asset_value["used_count"];
                // console.log(asset_value,asset_value.message,maximum_usage_count,used_count)
                child.maximum_usage_count = maximum_usage_count;
                child.used_count = used_count;
                child.balance_count = maximum_usage_count-used_count;
                frm.refresh_fields();
              });
           
        }
        }
 });


//  frappe.ui.form.on("Work Order", "validate", function(frm, cdt, cdn) { 
// 	$.each(frm.doc.reusable_items || [], function(i, d) {
//         var Asset  = frappe.get_doc("Asset",{"item_code":d.item_code})
//         console.log(Asset&&!d.asset_name);
//         (Asset && !d.asset_name)
// 	    {
// 			frappe.throw("Asset Name is mandatory for row "+d.idx);
// 		}
// 	})
// });