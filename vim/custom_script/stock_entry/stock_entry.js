// frappe.ui.form.on('Stock Entry Detail', {
//     // items_on_form_rendered: function(doc, grid_row) {
//     //     vim.setup_serial_or_batch_no();
//     // },
  
// });


erpnext.stock.select_batch_and_serial_no = (frm, item) => {
	let get_warehouse_type_and_name = (item) => {
        
		let value = '';
		if(frm.fields_dict.from_warehouse.disp_status === "Write") {
			value = cstr(item.s_warehouse) || '';
			return {
				type: 'Source Warehouse',
				name: value
			};
		} else {
			value = cstr(item.t_warehouse) || '';
			return {
				type: 'Target Warehouse',
				name: value
			};
		}
	}

	if(item && !item.has_serial_no && !item.has_batch_no) return;
	if (frm.doc.purpose === 'Material Receipt') return;

	frappe.require(["assets/vim/js/utils/serial_no_batch_selector.js","assets/vim/css/serial_no_batch_selector.css"], function() {
		new erpnext.SerialNoBatchSelector({
			frm: frm,
			item: item,
			warehouse_details: get_warehouse_type_and_name(item),
		});
        
	});
    
    
}