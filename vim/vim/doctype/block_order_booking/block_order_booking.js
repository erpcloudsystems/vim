// Copyright (c) 2021, aavu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Block Order Booking', {
	// refresh: function(frm) {

	// }
	setup: function(frm) {

	frm.set_query("block_branch","block_branch", function(frm,cdt,cdn) {
		var branch_list = [];
		for (var i = 0;i<cur_frm.doc.block_branch.length;i++){
			branch_list.push(cur_frm.doc.block_branch[i].block_branch)
		}
		if (branch_list.length>0)
		return {
			"filters": {
				"name":["not in",branch_list]
			}
		};
		else return {}
	});
	frm.set_query("block_item","block_item", function(frm,cdt,cdn) {
		var item_list = [];
		for (var i = 0;i<cur_frm.doc.block_item.length;i++){
			branch_item.push(cur_frm.doc.block_item[i].block_item)
		}
		if (branch_item.length>0)
		return {
			"filters": {
				"name":["not in",branch_item]
			}
		};
		else return {}
	});
	},
});

frappe.ui.form.on('Block Item', {
	item:function(frm,cdt,cdn){
        var child = locals[cdt][cdn];
		if(child.item){
			frappe.db.get_value('Item', child.item, ['item_name'],
            function(r) {
                // console.log(r)
                child.item_name =r['item_name']
             
                frm.refresh_fields();
              });
		}
		else{
			child.item_name =''
             
			frm.refresh_fields();
		}
	}
});