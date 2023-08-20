header('Content-type: application/javascript')

erpnext.SerialNoBatchSelector.prototype.get_batch_fields= function(){
    var me = this;
    var me = this;
        alert("hi")
		return [
			{fieldtype:'Section Break', label: __('Batches')},
			{fieldname: 'batches', fieldtype: 'Table', label: __('Batch Entries'),
				fields: [
					{
						'fieldtype': 'Link',
						'read_only': 0,
						'fieldname': 'batch_no',
						'options': 'Batch',
						'label': __('Select Batch'),
						'in_list_view': 1,
						get_query: function () {
							return {
								filters: {
									item_code: me.item_code,
									warehouse: me.warehouse || typeof me.warehouse_details.name == "string" ? me.warehouse_details.name : ''
								},
								query: 'erpnext.controllers.queries.get_batch_no'
							};
						},
						change: function () {
							const batch_no = this.get_value();
							if (!batch_no) {
								this.grid_row.on_grid_fields_dict
									.available_qty.set_value(0);
								return;
							}
							let selected_batches = this.grid.grid_rows.map((row) => {
								if (row === this.grid_row) {
									return "";
								}

								if (row.on_grid_fields_dict.batch_no) {
									return row.on_grid_fields_dict.batch_no.get_value();
								}
							});
							if (selected_batches.includes(batch_no)) {
								this.set_value("");
								frappe.throw(__('Batch {0} already selected.', [batch_no]));
							}

							if (me.warehouse_details.name) {
								frappe.call({
									method: 'erpnext.stock.doctype.batch.batch.get_batch_qty',
									args: {
										batch_no,
										warehouse: me.warehouse_details.name,
										item_code: me.item_code
									},
									callback: (r) => {
										this.grid_row.on_grid_fields_dict
											.available_qty.set_value(r.message || 0);
									}
								});

							} else {
								this.set_value("");
								frappe.throw(__('Please select a warehouse to get available quantities'));
							}
							// e.stopImmediatePropagation();
						}
					},
					{
						'fieldtype': 'Date',
						'fieldname': 'expiry_date',
						'label': __('Expiry Date'),
						'in_list_view': 1,
						// change: function () {
						// 	this.grid_row.on_grid_fields_dict.selected_qty.set_value('0');
						// }
					},
					{
						'fieldtype': 'Float',
						'read_only': 1,
						'fieldname': 'available_qty',
						'label': __('Available'),
						'in_list_view': 1,
						'default': 0,
						change: function () {
							this.grid_row.on_grid_fields_dict.selected_qty.set_value('0');
						}
					},
					{
						'fieldtype': 'Float',
						'read_only': 0,
						'fieldname': 'selected_qty',
						'label': __('Qty'),
						'in_list_view': 1,
						'default': 0,
						change: function () {
							var batch_no = this.grid_row.on_grid_fields_dict.batch_no.get_value();
							var available_qty = this.grid_row.on_grid_fields_dict.available_qty.get_value();
							var selected_qty = this.grid_row.on_grid_fields_dict.selected_qty.get_value();

							if (batch_no.length === 0 && parseInt(selected_qty) !== 0) {
								frappe.throw(__("Please select a batch"));
							}
							if (me.warehouse_details.type === 'Source Warehouse' &&
								parseFloat(available_qty) < parseFloat(selected_qty)) {

								this.set_value('0');
								frappe.throw(__('For transfer from source, selected quantity cannot be greater than available quantity'));
							} else {
								this.grid.refresh();
							}

							me.update_total_qty();
							me.update_pending_qtys();
						}
					},
				],
				in_place_edit: true,
				data: this.data,
				get_data: function () {
					return this.data;
				},
			}
		];
    }
  