erpnext.PointOfSale.Controller = class {
	constructor(wrapper) {
		this.wrapper = $(wrapper).find('.layout-main-section');
		this.page = wrapper.page;
		this.check_opening_entry();
        this.hide_header();

	}
	//added by shiby
    hide_header()
    {
        $('.sticky-top').css('display', 'none');
        $('.page-head').css('position', 'unset');
        $('.page-head .page-head-content').css('height', '25px');
		$('.layout-main-section-wrapper').css('margin-bottom', '10px');
      
		//this.$sticky-top = this.$component.find('.sticky-top');
        // console.log(this.wrapper.find('.sticky-top'),"this.wrapper.find",this.$component)
        // this.wrapper.find('.sticky-top').css('display', 'none');
        // this.wrapper.find('.page-head').css('position','unset')
        //this.$component.css('display', 'none');
    }
	show_header()
    {
		$('.sticky-top').css('display', 'flex');
        $('.page-head').css('position', 'sticky');
        $('.page-head .page-head-content').css('height', 'var(--page-head-height)');
		$('.layout-main-section-wrapper').css('margin-bottom', '10px');
    }
	fetch_opening_entry() {
		return frappe.call("erpnext.selling.page.point_of_sale.point_of_sale.check_opening_entry", { "user": frappe.session.user });
	}

	check_opening_entry() {
		this.fetch_opening_entry().then((r) => {
			if (r.message.length) {
				// assuming only one opening voucher is available for the current user
				this.prepare_app_defaults(r.message[0]);
			} else {
				this.create_opening_voucher();
			}
		});
	}
    create_closing_voucher(){
        const me = this;
		
		const table_fields = [
			{
				fieldname: "mode_of_payment", fieldtype: "Link",
				in_list_view: 1, label: "Mode of Payment",
				options: "Mode of Payment",				
				 filters: {
					"type":[ "=", 'Cash']
				},
				reqd: 1,
			},
			{
				fieldname: "closing_amount", fieldtype: "Currency",
				in_list_view: 1, label: "Closing Amount",
				options: "company:company_currency",
                change: function () {
					dialog.fields_dict.closing_details.df.data.some(d => {
						if (d.idx == this.doc.idx) {
							d.closing_amount = this.value;
							dialog.fields_dict.closing_details.grid.refresh();
                            dialog.fields_dict.closing_details.grid.wrapper.find('.grid-add-row').hide();
							return true;
						}
					});
				}
				
			}
		];
        const fetch_pos_close_payment_methods = () => {
			const pos_profile = cur_frm.doc.pos_profile;
			if (!pos_profile) return;
			frappe.db.get_doc("POS Profile", pos_profile).then(({ payments }) => {
				dialog.fields_dict.closing_details.df.data = [];
				payments.forEach(pay => {
						const { mode_of_payment } = pay;
						frappe.db.get_value('Mode of Payment', mode_of_payment, 'type').then(({ message }) => {
						
							if(String(message.type)=='Cash'){
						
								dialog.fields_dict.closing_details.df.data.push(
									{ mode_of_payment, closing_amount: '0' });
									dialog.fields_dict.closing_details.grid.refresh();
                                    dialog.fields_dict.closing_details.grid.wrapper.find('.grid-add-row').hide();
                                    
						}
					
				});
			});
				dialog.fields_dict.closing_details.grid.refresh();
                dialog.fields_dict.closing_details.grid.wrapper.find('.grid-add-row').hide();
			});
		}
        const dialog = new frappe.ui.Dialog({
			title: __('Create POS Closing Entry'),
			static: true,
			fields: [
				
				{
					fieldname: "closing_details",
					fieldtype: "Table",
					label: "Closing Details",
					cannot_add_rows: false,
					in_place_edit: true,
					reqd: 1,
					data: [],
					fields: table_fields
				}
			],
			primary_action: async function({ company, pos_profile, closing_details }) {
				if (!closing_details.length) {
					frappe.show_alert({
						message: __("Please add Mode of payments and closing details."),
						indicator: 'red'
					})
					return frappe.utils.play_sound("error");
				}

				// filter balance details for empty rows
				closing_details = closing_details.filter(d => d.mode_of_payment);
				
				let voucher = frappe.model.get_new_doc('POS Closing Entry');
				voucher.pos_profile = me.frm.doc.pos_profile;
				voucher.user = frappe.session.user;
				voucher.company = me.frm.doc.company;
				voucher.pos_opening_entry = me.pos_opening;
				voucher.cash_closing_amont=closing_details[0].closing_amount
				voucher.period_end_date = frappe.datetime.now_datetime();
				voucher.posting_date = frappe.datetime.now_date();
				
				frappe.set_route('Form', 'POS Closing Entry', voucher.name);

				// const method = "erpnext.selling.page.point_of_sale.point_of_sale.create_closing_voucher";
				// const res = await frappe.call({ method, args: { pos_profile, company, closing_details }, freeze:true });
				
				dialog.hide();
				
			},
			primary_action_label: __('Submit')
		});
		fetch_pos_close_payment_methods();
		dialog.show();
		this.show_header();
    }
   
	create_opening_voucher() {
		const me = this;
		const table_fields = [
			{
				fieldname: "mode_of_payment", fieldtype: "Link",
				in_list_view: 1, label: "Mode of Payment",
				options: "Mode of Payment",				
				 filters: {
					"type":[ "=", 'Cash']
				},
				reqd: 1,
			},
			{
				fieldname: "opening_amount", fieldtype: "Currency",
				in_list_view: 1, label: "Opening Amount",
				options: "company:company_currency",
				change: function () {
					dialog.fields_dict.balance_details.df.data.some(d => {
						if (d.idx == this.doc.idx) {
							d.opening_amount = this.value;
							dialog.fields_dict.balance_details.grid.refresh();
                            dialog.fields_dict.balance_details.grid.wrapper.find('.grid-add-row').hide();
							return true;
						}
					});
				}
			}
		];
		const fetch_pos_payment_methods = () => {
			const pos_profile = dialog.fields_dict.pos_profile.get_value();
			if (!pos_profile) return;
			frappe.db.get_doc("POS Profile", pos_profile).then(({ payments }) => {
				dialog.fields_dict.balance_details.df.data = [];
				payments.forEach(pay => {
						const { mode_of_payment } = pay;
						frappe.db.get_value('Mode of Payment', mode_of_payment, 'type').then(({ message }) => {
						
							if(String(message.type)=='Cash'){
						
								dialog.fields_dict.balance_details.df.data.push(
									{ mode_of_payment, opening_amount: '0' });
									dialog.fields_dict.balance_details.grid.refresh();
                                    dialog.fields_dict.balance_details.grid.wrapper.find('.grid-add-row').hide();
                                    
						}
					
				});
			});
				dialog.fields_dict.balance_details.grid.refresh();
                dialog.fields_dict.balance_details.grid.wrapper.find('.grid-add-row').hide();
			});
		}
		const dialog = new frappe.ui.Dialog({
			title: __('Create POS Opening Entry'),
			static: true,
			fields: [
				{
					fieldtype: 'Link', label: __('Company'), default: frappe.defaults.get_default('company'),
					options: 'Company', fieldname: 'company', reqd: 1
				},
				{
					fieldtype: 'Link', label: __('POS Profile'),
					options: 'POS Profile', fieldname: 'pos_profile', reqd: 1,
					get_query: () => pos_profile_query,
					onchange: () => fetch_pos_payment_methods()
				},
				{
					fieldname: "balance_details",
					fieldtype: "Table",
					label: "Opening Balance Details",
					cannot_add_rows: false,
					in_place_edit: true,
					reqd: 1,
					data: [],
					fields: table_fields
				}
			],
			primary_action: async function({ company, pos_profile, balance_details }) {
				if (!balance_details.length) {
					frappe.show_alert({
						message: __("Please add Mode of payments and opening balance details."),
						indicator: 'red'
					})
					return frappe.utils.play_sound("error");
				}

				// filter balance details for empty rows
				balance_details = balance_details.filter(d => d.mode_of_payment);

				const method = "erpnext.selling.page.point_of_sale.point_of_sale.create_opening_voucher";
				const res = await frappe.call({ method, args: { pos_profile, company, balance_details }, freeze:true });
				!res.exc && me.prepare_app_defaults(res.message);
				dialog.hide();
			},
			primary_action_label: __('Submit')
		});
		dialog.show();
		const pos_profile_query = {
			query: 'erpnext.accounts.doctype.pos_profile.pos_profile.pos_profile_query',
			filters: { company: dialog.fields_dict.company.get_value() }
		};
	}

	async prepare_app_defaults(data) {
		this.pos_opening = data.name;
		this.company = data.company;
		this.pos_profile = data.pos_profile;
		this.pos_opening_time = data.period_start_date;
		this.item_stock_map = {};
		this.settings = {};

		frappe.db.get_value('Stock Settings', undefined, 'allow_negative_stock').then(({ message }) => {
			this.allow_negative_stock = flt(message.allow_negative_stock) || false;
		});

		frappe.db.get_doc("POS Profile", this.pos_profile).then((profile) => {
			Object.assign(this.settings, profile);
			this.settings.customer_groups = profile.customer_groups.map(group => group.customer_group);
			this.make_app();
		});
	}

	set_opening_entry_status() {
		this.page.set_title_sub(
			`<span class="indicator orange">
				<a class="text-muted" href="#Form/POS%20Opening%20Entry/${this.pos_opening}">
					Opened at ${moment(this.pos_opening_time).format("Do MMMM, h:mma")}
				</a>
			</span>`);
	}

	make_app() {
		this.prepare_dom();
		this.prepare_components();
		this.prepare_menu();
		this.make_new_invoice();
        this.hide_header();
	
        
	}


	prepare_dom() {
		this.wrapper.append(
			`<div class="point-of-sale-app">
            </div>`
		);
       
		this.$components_wrapper = this.wrapper.find('.point-of-sale-app');
        $('.point-of-sale-app section').css('min-height','35rem')	
       
	}

	prepare_components() {
		this.init_item_selector();
		this.init_item_details();
		this.init_item_cart();
		this.init_payments();
		this.init_recent_order_list();
		this.init_order_summary();
        this.init_combo_item_details();
	}

	prepare_menu() {
		this.page.clear_menu();
        this.page.add_menu_item(__("Home"), this.open_home.bind(this), false, 'Ctrl+');

		this.page.add_menu_item(__("Open Form View"), this.open_form_view.bind(this), false, 'Ctrl+F');

		this.page.add_menu_item(__("Toggle Recent Orders"), this.toggle_recent_order.bind(this), false, 'Ctrl+O');

		this.page.add_menu_item(__("Save as Draft"), this.save_draft_invoice.bind(this), false, 'Ctrl+S');

		this.page.add_menu_item(__('Close the POS'), this.close_pos.bind(this), false, 'Shift+Ctrl+C');
        this.page.add_menu_item(__('Approve Discount'), this.validate_approver.bind(this), false, 'Shift+Ctrl+D');
        this.page.add_menu_item(__('Issue RFID'), this.issue_rfid.bind(this), false, 'Ctrl+R');
	
	}

    open_home(){
        frappe.set_route('Form', 'Home');
		this.show_header();
    }
	open_form_view() {
		frappe.model.sync(this.frm.doc);
		frappe.set_route("Form", this.frm.doc.doctype, this.frm.doc.name);
	}

	toggle_recent_order() {
		const show = this.recent_order_list.$component.is(':hidden');
		this.toggle_recent_order_list(show);
	}

	save_draft_invoice() {
		
		if (!this.$components_wrapper.is(":visible")) return;

		if (this.frm.doc.items.length == 0) {
			frappe.show_alert({
				message: __("You must add atleast one item to save it as draft."),
				indicator:'red'
			});
			frappe.utils.play_sound("error");
			return;
		}
      
		this.frm.save(undefined, undefined, undefined, () => {
			frappe.show_alert({
				message: __("There was an error saving the document."),
				indicator: 'red'
			});
			frappe.utils.play_sound("error");
		}).then(() => {
			frappe.run_serially([
				() => frappe.dom.freeze(),
				() => this.make_new_invoice(),				
				() => frappe.dom.unfreeze(),
			]);
			this.update_POS()
		});
	}
    issue_rfid(){
        
        let voucher = frappe.model.get_new_doc('Customer RFID');
		voucher.pos_invoice = this.frm.doc.name;	        
        frappe.set_route('Form', 'Customer RFID', voucher.name);
        this.show_header();

    }
	close_pos() {
		if (!this.$components_wrapper.is(":visible")) return;

		// let voucher = frappe.model.get_new_doc('POS Closing Entry');
		// voucher.pos_profile = this.frm.doc.pos_profile;
		// voucher.user = frappe.session.user;
		// voucher.company = this.frm.doc.company;
		// voucher.pos_opening_entry = this.pos_opening;
		// voucher.period_end_date = frappe.datetime.now_datetime();
		// voucher.posting_date = frappe.datetime.now_date();
		//frappe.set_route('Form', 'POS Closing Entry', voucher.name);
        this.create_closing_voucher()
	}
    async update_discount_approval(discount, remarks) {
        // const frm = this.events.get_frm();
        // frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'additional_discount_percentage', flt(discount));
		// frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'discount_remark',String(remarks));
        // this.discount_field.set_value(flt(cur_frm.doc.additional_discount_percentage));
		// this.disremark=cur_frm.doc.discount_remark
        cur_pos.cart.update_discount(remarks,discount)
		cur_pos.cart.hide_discount_control(discount,remarks);
        
                       
    }
    validate_approver(){
        const me = this;
		const dialog = new frappe.ui.Dialog({
            title: __('Approve Discount'),
              fields: [
                  {fieldtype: "Section Break"},
                  {fieldtype: 'Data', label: __('User'), fieldname: 'appuser',reqd:1
                    		},
                  {fieldtype: 'Password', label: __('Password'), fieldname: 'apppassword',reqd:1
                       },
                
                ],
                primary_action: async function({ appuser, apppassword}) {
                    if (!appuser) {
                        frappe.show_alert({
                            message: __("Please enter user name & password."),
                            indicator: 'red'
                        })
                        return frappe.utils.play_sound("error");
                    }
                   
                    const method = "vim.custom_script.point_of_sale.point_of_sale.validate_user_permission";
				    const res = await frappe.call({ method, args: { appuser, apppassword }, freeze:true });
					
					if(res.message==1)
					{
						me.approve_discount(appuser);
					}
					else
					{
						frappe.show_alert({
                            message: __("No Permission."),
                            indicator: 'red'
                        })
					}
				    
                    
                    dialog.hide();
                },
                primary_action_label: __('Login')
		        });
    
    dialog.show()
    dialog.$wrapper.find('.modal-dialog').css("width", "400px");
    
       
    }
    approve_discount(){
        const me = this;
		const dialog = new frappe.ui.Dialog({
            title: __('Approve Discount'),
              fields: [
                  {fieldtype: "Section Break"},
                  {fieldtype: 'Float', label: __('Discount'), default: cur_frm.doc.additional_discount_percentage,
                    			 fieldname: 'discount'
                    		},
                  {fieldtype: 'Data', label: __('Remarks'), default: cur_frm.doc.discount_remark,
                            fieldname: 'remarks'
                       },
                
                ],
                primary_action: async function({ discount, remarks }) {
                    
                    me.update_discount_approval(discount, remarks);
                    dialog.hide();
                },
                primary_action_label: __('Submit')
		        });
    
    dialog.show()
    dialog.$wrapper.find('.modal-dialog').css("width", "400px");
    dialog.$wrapper.find('.modal-dialog').css("height", "300px");
       
    }
	init_item_selector() {
		this.item_selector = new erpnext.PointOfSale.ItemSelector({
			wrapper: this.$components_wrapper,
			pos_profile: this.pos_profile,
			settings: this.settings,
			events: {
				item_selected: args => this.on_cart_update(args),
				bundle_item_selected: args => this.on_bundle_cart_update(args),

				get_frm: () => this.frm || {}
			}
		})
        // this.frm.add_custom_button(__('Get User Email Address'), function(){
        //     frappe.msgprint(frm.doc.name);
        // });
	}

	init_item_cart() {
		this.cart = new erpnext.PointOfSale.ItemCart({
			wrapper: this.$components_wrapper,
			settings: this.settings,
			events: {
				//added by shiby
                item_selected: args => this.on_cart_update(args),
                //item_selected: args => this.on_cart_update_uom(args),
				item_selected_desc: args => this.on_cart_update_desc(args),
                so_item_selected: args => this.on_cart_update_from_so(args),
                //
				get_frm: () => this.frm,

				cart_item_clicked: (item_code, batch_no, uom,rate) => {
					const search_field = batch_no ? 'batch_no' : 'item_code';
					const search_value = batch_no || item_code;
					const item_row = this.frm.doc.items.find(i => i[search_field] === search_value && i.uom === uom && i.rate ===parseFloat(rate));
					console.log(this.frm.doc.items,parseFloat(rate))
                    if(!item_row.is_free_item) {
					this.item_details.toggle_item_details_section(item_row);
                    }
                    
				},
                cart_combo_item_clicked: (item_code, batch_no, uom,rate,args) => {
					const search_field = batch_no ? 'batch_no' : 'item_code';
					const search_value = batch_no || item_code;
					const item_row = this.frm.doc.items.find(i => i[search_field] === search_value && i.uom === uom && i.rate ===parseFloat(rate));
					console.log(item_row,"AAAAAAAAAAA")
                    if(item_row && !item_row.is_free_item) {
                        cur_pos.combo_item_details.combo_items = [];
		            cur_pos.combo_item_details.combo_default_items = [];                    
                    cur_pos.combo_item_details.total_packed_qty=item_row.qty;
					cur_frm.doc.seleceted_packed_items.forEach(item => {
						var current_item={} 
                        if(item_code==item.parent_item){
                            current_item.parent_item = item.parent_item
						    current_item.item_code = item.item_code
						    current_item.packed_quantity = item.packed_quantity
						    current_item.set_no = item.set_no
						    current_item.combo_qty = item.combo_qty
						    cur_pos.combo_item_details.combo_items.push(current_item)

                        }
                		
						
					})
                  
					this.combo_item_details.toggle_combo_item_details_section(item_row);

                    }
                    else{
                        this.on_cart_update(args)
                    }
                    
				},
                
				numpad_event: (value, action) => this.update_item_field(value, action),
               
                
				checkout: () => this.payment.checkout(),

				edit_cart: () => this.payment.edit_cart(),

				customer_details_updated: (details) => {
					this.customer_details = details;
					// will add/remove LP payment method
					this.payment.render_loyalty_points_payment_mode();
				}
			}
		})
	}

	init_item_details() {
		this.item_details = new erpnext.PointOfSale.ItemDetails({
			wrapper: this.$components_wrapper,
			settings: this.settings,
			events: {
				get_frm: () => this.frm,

				toggle_item_selector: (minimize) => {
					this.item_selector.resize_selector(minimize);
					this.cart.toggle_numpad(minimize);
				},

				form_updated: async (cdt, cdn, fieldname, value) => {
					const item_row = frappe.model.get_doc(cdt, cdn);
					if (item_row && item_row[fieldname] != value) {
                        

						const { item_code, batch_no, uom } = this.item_details.current_item;
						const event = {
							field: fieldname,
							value,
							item: { item_code, batch_no, uom }
						}
						return this.on_cart_update(event)
					}
				},

				item_field_focused: (fieldname) => {
					this.cart.toggle_numpad_field_edit(fieldname);
				},
				set_value_in_current_cart_item: (selector, value) => {
					this.cart.update_selector_value_in_cart_item(selector, value, this.item_details.current_item);
				},
				clone_new_batch_item_in_frm: (batch_serial_map, current_item) => {
					// called if serial nos are 'auto_selected' and if those serial nos belongs to multiple batches
					// for each unique batch new item row is added in the form & cart
					Object.keys(batch_serial_map).forEach(batch => {
						const { item_code, batch_no } = current_item;
						const item_to_clone = this.frm.doc.items.find(i => i.item_code === item_code && i.batch_no === batch_no);
						const new_row = this.frm.add_child("items", { ...item_to_clone });
                        
						// update new serialno and batch
						new_row.batch_no = batch;
						new_row.serial_no = batch_serial_map[batch].join(`\n`);
						new_row.qty = batch_serial_map[batch].length;
						this.frm.doc.items.forEach(row => {
							if (item_code === row.item_code) {
								this.update_cart_html(row);
							}
						});
					})
				},
				remove_item_from_cart: () => this.remove_item_from_cart(),
				get_item_stock_map: () => this.item_stock_map,
				close_item_details: () => {
                    
					this.item_details.toggle_item_details_section(undefined);
					this.cart.prev_action = undefined;
					this.cart.toggle_item_highlight();
				},
				get_available_stock: (item_code, warehouse) => this.get_available_stock(item_code, warehouse)
			}
		});
	}

	init_combo_item_details() {
		this.combo_item_details = new erpnext.PointOfSale.ComboItemDetails({
			wrapper: this.$components_wrapper,
			settings: this.settings,
			events: {
				item_selected: args => this.on_cart_update(args),
				get_frm: () => this.frm,
				toggle_combo_item_selector: (minimize) => {
					this.item_selector.resize_selector(minimize);
                    this.cart.toggle_checkout_btn(false);
                    this.cart.$totals_section.find('.edit-cart-btn').css('display', 'none');
					//this.combo_item_details.toggle_combo_numpad(minimize);
                    
				},
				
				remove_item_from_cart: () => this.remove_item_from_cart(),
                combo_numpad_event: () => this.update_combo_item_field(),
                
				close_combo_item_details: () => {					
					this.combo_item_details.toggle_combo_item_details_section(undefined);
					this.cart.prev_action = undefined;
					this.cart.toggle_item_highlight();
                    this.cart.toggle_checkout_btn(true);
                   
                    
				},
				
			}
		});
	}

	init_payments() {
		this.payment = new erpnext.PointOfSale.Payment({
			wrapper: this.$components_wrapper,
			events: {
				get_frm: () => this.frm || {},
                item_selected: args => this.on_cart_update(args),
				get_customer_details: () => this.customer_details || {},

				toggle_other_sections: (show) => {
					if (show) {
						this.item_details.$component.is(':visible') ? this.item_details.$component.css('display', 'none') : '';
						this.item_selector.$component.css('display', 'none');
					} else {
						this.item_selector.$component.css('display', 'flex');
					}
				},

				submit_invoice: () => {
					try{
					this.update_Item();
                    //console.log(this.frm,"this.frm")
						this.frm.savesubmit()
						.then((r) => {
							this.toggle_components(false);
							this.order_summary.toggle_component(true);
							this.order_summary.load_summary_of(this.frm.doc, true);
                            frappe.show_alert({
                                indicator: 'green',
                                message: __('POS invoice {0} created succesfully', [r.doc.name])
                            });
							//Added by shiby
							//this.create_event_booking();
                    		this.update_POS();
							//this.update_POS_Item();
							//

						});
					// });

					} catch (error) {
						frappe.show_alert({
							indicator: 'red',
							message: __(error)
						});
		} finally {
			
			
		}
					
				}
			}
		});
	}

	init_recent_order_list() {
		this.recent_order_list = new erpnext.PointOfSale.PastOrderList({
			wrapper: this.$components_wrapper,
			events: {
				open_invoice_data: (name) => {
					frappe.db.get_doc('POS Invoice', name).then((doc) => {
						this.order_summary.load_summary_of(doc);
					});
				},
				reset_summary: () => this.order_summary.toggle_summary_placeholder(true)
                ,

				get_frm: () => this.frm || {}
			}
		})
	}

	init_order_summary() {
		this.order_summary = new erpnext.PointOfSale.PastOrderSummary({
			wrapper: this.$components_wrapper,
			events: {
				get_frm: () => this.frm,

				process_return: (name) => {
                    
					this.recent_order_list.toggle_component(false);
					frappe.db.get_doc('POS Invoice', name).then((doc) => {
						frappe.run_serially([
							() => this.make_return_invoice(doc),
							() => this.cart.load_invoice(),
							() => this.item_selector.toggle_component(true)
						]);
					});
				},
				edit_order: (name) => {
					this.recent_order_list.toggle_component(false);
					frappe.run_serially([
						() => this.frm.refresh(name),
						() => this.frm.call('reset_mode_of_payments'),
						() => this.cart.load_invoice(),
						() => this.item_selector.toggle_component(true)
					]);
				},
				delete_order: (name) => {
					frappe.model.delete_doc(this.frm.doc.doctype, name, () => {
						this.recent_order_list.refresh_list();
					});
				},
				new_order: () => {
					frappe.run_serially([
						() => frappe.dom.freeze(),
						() => this.make_new_invoice(),
						() => this.item_selector.toggle_component(true),						
						() => frappe.dom.unfreeze(),
						
					]);
				}
			}
		})
	}

	toggle_recent_order_list(show) {
		this.toggle_components(!show);
		this.recent_order_list.toggle_component(show);
		this.order_summary.toggle_component(show);
	}

	toggle_components(show) {
		this.cart.toggle_component(show);
		this.item_selector.toggle_component(show);

		// do not show item details or payment if recent order is toggled off
		!show ? (this.item_details.toggle_component(false) || this.payment.toggle_component(false)) : '';
	}

	make_new_invoice() {
		
		return frappe.run_serially([
			() => frappe.dom.freeze(),
			() => this.make_sales_invoice_frm(),
			() => this.set_pos_profile_data(),
			() => this.set_pos_profile_status(),
			() => this.cart.load_invoice(),
			() => frappe.dom.unfreeze()
		]);
	}

	make_sales_invoice_frm() {
		const doctype = 'POS Invoice';
       
		return new Promise(resolve => {
			if (this.frm) {
				this.frm = this.get_new_frm(this.frm);
                
				this.frm.doc.items = [];
				this.frm.doc.is_pos = 1
				resolve();
			} else {
				frappe.model.with_doctype(doctype, () => {
					this.frm = this.get_new_frm();
					this.frm.doc.items = [];
					this.frm.doc.is_pos = 1
					resolve();
				});
			}
		});
	}

	get_new_frm(_frm) {
		const doctype = 'POS Invoice';
		const page = $('<div>');
		const frm = _frm || new frappe.ui.form.Form(doctype, page, false);
		const name = frappe.model.make_new_doc_and_get_name(doctype, true);
		frm.refresh(name);

		return frm;
	}

	async make_return_invoice(doc) {
		frappe.dom.freeze();
		this.frm = this.get_new_frm(this.frm);
		this.frm.doc.items = [];
		const res = await frappe.call({
			method: "erpnext.accounts.doctype.pos_invoice.pos_invoice.make_sales_return",
			args: {
				'source_name': doc.name,
				'target_doc': this.frm.doc
			}
		});
		frappe.model.sync(res.message);
		await this.set_pos_profile_data();
		frappe.dom.unfreeze();
	}

	set_pos_profile_data() {
		if (this.company && !this.frm.doc.company) this.frm.doc.company = this.company;
		if (this.pos_profile && !this.frm.doc.pos_profile) this.frm.doc.pos_profile = this.pos_profile;
		if (!this.frm.doc.company) return;

		return this.frm.trigger("set_pos_data");
	}

	set_pos_profile_status() {             
		this.page.set_indicator(this.pos_profile, "blue");
	}
    async on_cart_update_from_so(args) {
       
		frappe.dom.freeze();
		let item_row = undefined;
		try {
			let { field, value, item } = args;
			
			const { item_code, batch_no, serial_no, stock_uom,rate,conversion_factor,uom } = item;
            
			item_row = this.get_item_from_frm(item_code, batch_no, uom);
			const item_selected_from_selector = field === 'qty' && value === "+1"
            
			if (item_row ) {
				
				item_selected_from_selector && (value = item_row.qty + flt(value))
				
				field === 'qty' && (value = flt(value));

				if (['qty', 'conversion_factor'].includes(field) && value > 0 && !this.allow_negative_stock) {
					const qty_needed = field === 'qty' ? value * item_row.conversion_factor : item_row.qty * value;
					await this.check_stock_availability(item_row, qty_needed, this.frm.doc.set_warehouse);
				}
				
				if (this.is_current_item_being_edited(item_row) || item_selected_from_selector) {
					
					await frappe.model.set_value(item_row.doctype, item_row.name, field, value);
					this.update_cart_html(item_row);
					
				}

			} else {
				if (!this.frm.doc.customer) {
					frappe.dom.unfreeze();
					frappe.show_alert({
						message: __('You must select a customer before adding an item.'),
						indicator: 'orange'
					});
					frappe.utils.play_sound("error");
					return;
				}
				if (!item_code) return;

				item_selected_from_selector && (value = flt(value))
				const args = { item_code, batch_no,uom,stock_uom,rate,conversion_factor, [field]: value };

				if (serial_no) {
					await this.check_serial_no_availablilty(item_code, this.frm.doc.set_warehouse, serial_no);
					args['serial_no'] = serial_no;
				}

				if (field === 'serial_no') args['qty'] = value.split(`\n`).length || 0;
               
				item_row = this.frm.add_child('items',args);   

				if (field === 'qty' && value !== 0 && !this.allow_negative_stock)
					await this.check_stock_availability(item_row, value, this.frm.doc.set_warehouse);
                await this.trigger_new_item_events_so(item_row,rate,uom);
				this.check_serial_batch_selection_needed(item_row) && this.edit_item_details_of(item_row);
				//this.update_cart_html(item_row);
              
                if(uom!=item_row.uom)
                {
					
                    var current_item={};
                    const search_field = batch_no ? 'batch_no' : 'item_code';
					const search_value = batch_no || item_code;
					const item_rowedit = this.frm.doc.items.find(i => i[search_field] === search_value && i.uom === item_row.uom);
					
                    current_item.item_code = item_code
			        current_item.batch_no = batch_no;
			        current_item.uom = uom
                    current_item.sales_order = cur_pos.cart.location_so_field.value
			       
                   	 
                        cur_pos.item_details.current_item=current_item;
                        
                        //await cur_pos.cart.events.cart_item_clicked(item_code, batch_no, item_row.uom);
                    // this.item_details.toggle_item_details_section(item_rowedit);
                    // this.update_item_field(uom,'uom')
                    // this.update_item_field(conversion_factor,'conversion_factor')
			        await frappe.model.set_value(item_row.doctype, item_row.name, 'stock_uom', uom);
                    await frappe.model.set_value(item_row.doctype, item_row.name, 'sales_order', cur_pos.cart.location_so_field.value);
                    await frappe.model.set_value(item_row.doctype, item_row.name, 'uom', uom);
                    await frappe.model.set_value(item_row.doctype, item_row.name, 'conversion_factor', (conversion_factor));
                    await frappe.model.set_value(item_row.doctype, item_row.name, 'rate', rate);
                    // console.log(item_row.item_code,frappe.model.get_value(item_row.doctype, item_row.name, 'uom'),
                    // frappe.model.get_value(item_row.doctype, item_row.name, 'rate'),"testing")
                    
                   cur_frm.refresh_field("items")
                  
                    //console.log(String(uom),"strinfguom",conversion_factor);
                    // cur_pos.item_details.set_uom_value(String(uom),conversion_factor)
                    // cur_pos.item_details.events.close_item_details();
                    // cur_pos.item_details.uom_control.set_value(uom);
                    // cur_pos.item_details.uom_control.refresh();
                    
                    // cur_pos.item_details.conversion_factor_control.set_value((conversion_factor));
                    // cur_pos.item_details.conversion_factor_control.refresh();
                    // //cur_pos.item_details.events.close_item_details();
                    var item_rownew = this.get_item_from_frm(item_code, batch_no, uom);
                    // item_rownew.uom=uom;
                    // item_rownew.conversion_factor=conversion_factor
                    
                   // console.log("lastcall",item_rownew,item_rownew.rate,item_rownew.base_rate,item_rownew)
                    
                        this.update_cart_html(item_rownew)
                    
                    
				
                }
                else{
                    this.update_cart_html(item_row);
                }
                
                
            }

		} catch (error) {
			console.log(error);
		} finally {
			frappe.dom.unfreeze();
			return item_row;
		}

    }
	async on_bundle_cart_update(args) {
		frappe.dom.freeze();
		let item_row = undefined;
		try {
			let { field, value, item } = args;
           
			const { item_code, batch_no, serial_no, uom,rate } = item;
            
			item_row = this.get_item_from_frm(item_code, batch_no, uom);
			console.log(rate,"$$$$$$$$")
			if(item_row){
               
				this.cart.events.cart_combo_item_clicked(item_code, batch_no, uom,rate,args);
			}
			else{
                
				this.on_cart_update(args)
			}
		} catch (error) {
			console.log(error);
		} finally {
			frappe.dom.unfreeze();
			return item_row;
		}
	}
	async on_cart_update(args) {
		
		frappe.dom.freeze();
		let item_row = undefined;
		try {
			let { field, value, item } = args;
			//slot_name field added by shiby
            
			const { item_code, batch_no, serial_no, uom ,rate} = item;
            
			item_row = this.get_item_from_frm(item_code, batch_no, uom);
           
			const item_selected_from_selector = field === 'qty' && value === "+1"
           

			if (item_row && item_row.rate==rate ) {
                console.log(item_row.rate,"222222222222222",rate,item_row.is_free_item)
                if(!item_row.is_free_item){
                    
				item_selected_from_selector && (value = item_row.qty + flt(value))
				field === 'qty' && (value = flt(value));
				
				if (['qty', 'conversion_factor'].includes(field) && value > 0 && !this.allow_negative_stock) {
					const qty_needed = field === 'qty' ? value * item_row.conversion_factor : item_row.qty * value;
					await this.check_stock_availability(item_row, qty_needed, this.frm.doc.set_warehouse);
				}
             
				if(cur_pos.item_selector.bundle_item && cur_pos.item_selector.bundle_item!='' && cur_pos.item_selector.bundle_item!='null' && cur_pos.item_selector.bundle_item!='undefined' && cur_pos.item_selector.bundle_item!=0)  {
					
					cur_pos.combo_item_details.total_packed_qty=value
					this.combo_item_details.current_item=item_row;
                    this.item_details.current_item=item_row;
                    cur_pos.combo_item_details.combo_items=[];
					this.edit_combo_item_details_of(item_row)
					
					
				 }
                
				if (this.is_current_item_being_edited(item_row) || item_selected_from_selector || this.is_current_combo_item_being_edited(item_row)) {
                   
					await frappe.model.set_value(item_row.doctype, item_row.name, field, value);
                       
                        this.update_cart_html(item_row);
                   
				}
            }

			} else {
				if (!this.frm.doc.customer) {
					frappe.dom.unfreeze();
					frappe.show_alert({
						message: __('You must select a customer before adding an item.'),
						indicator: 'orange'
					});
					frappe.utils.play_sound("error");
					return;
				}
				if (!item_code) return;
                item_selected_from_selector && (value = flt(value))
                

				const args = { item_code, batch_no, [field]: value };
                
				if (serial_no) {
					await this.check_serial_no_availablilty(item_code, this.frm.doc.set_warehouse, serial_no);
					args['serial_no'] = serial_no;
				}

				if (field === 'serial_no') args['qty'] = value.split(`\n`).length || 0;

				item_row = this.frm.add_child('items', args);
                
				if (field === 'qty' && value !== 0 && !this.allow_negative_stock)
					await this.check_stock_availability(item_row, value, this.frm.doc.set_warehouse);

				await this.trigger_new_item_events(item_row);

				this.check_serial_batch_selection_needed(item_row) && this.edit_item_details_of(item_row);
             if(cur_pos.item_selector.bundle_item && cur_pos.item_selector.bundle_item!='' && cur_pos.item_selector.bundle_item!='null' &&  cur_pos.item_selector.bundle_item!='undefined' && cur_pos.item_selector.bundle_item!=0)  {
				//item_row.qty=0
				this.combo_item_details.current_item=item_row;
                this.item_details.current_item=item_row;
				cur_pos.combo_item_details.total_packed_qty=item_row.qty
                cur_pos.combo_item_details.combo_items = [];
		        cur_pos.combo_item_details.combo_default_items = [];
				this.edit_combo_item_details_of(item_row)
             } 
			 
				this.update_cart_html(item_row);

			 
             
				
			}

		} catch (error) {
			console.log(error);
		} finally {
			frappe.dom.unfreeze();
			return item_row;
		}
	}
	//added by shiby
	
	async on_cart_update_desc(args) {
		
		let item_row = undefined;
		try {
			let { field, value, item } = args;
			const { item_code, batch_no, serial_no, uom,rate } = item;
			item_row = this.get_item_from_frm(item_code, batch_no, uom);
			
			const item_selected_from_selector = field === 'qty' && value === "-1"
		
			if (item_row) {
                if(!item_row.is_free_item){
				item_selected_from_selector && (value = item_row.qty + flt(value))

				field === 'qty' && (value = flt(value));

				if (['qty', 'conversion_factor'].includes(field) && value > 0 && !this.allow_negative_stock) {
					const qty_needed = field === 'qty' ? value * item_row.conversion_factor : item_row.qty * value;
					await this.check_stock_availability(item_row, qty_needed, this.frm.doc.set_warehouse);
				}

				if (this.is_current_item_being_edited(item_row) || item_selected_from_selector) {
					
					await frappe.model.set_value(item_row.doctype, item_row.name, field, value);
					this.update_cart_html(item_row);
				}
            }

			} 

		} catch (error) {
			console.log(error);
		} finally {
			frappe.dom.unfreeze();
			return item_row;
		}
	}
	async on_cart_update_uom(args) {
		
		let item_row = undefined;
		try {
			let { field, value, item } = args;
			const { item_code, batch_no, serial_no, uom } = item;
			item_row = this.get_item_from_frm(item_code, batch_no, uom);
			
			const item_selected_from_selector = field === 'qty' && value === "-1"
			
			if (item_row) {
				
				item_selected_from_selector && (value = item_row.qty + flt(value))

				field === 'uom' && (value = flt(value));

				if (['qty', 'conversion_factor'].includes(field) && value > 0 && !this.allow_negative_stock) {
					const qty_needed = field === 'qty' ? value * item_row.conversion_factor : item_row.qty * value;
					await this.check_stock_availability(item_row, qty_needed, this.frm.doc.set_warehouse);
				}

				if (this.is_current_item_being_edited(item_row) || item_selected_from_selector) {
					
					await frappe.model.set_value(item_row.doctype, item_row.name, field, value);
					this.update_cart_html(item_row);
				}

			} 

		} catch (error) {
			console.log(error);
		} finally {
			frappe.dom.unfreeze();
			return item_row;
		}
	}
	get_item_from_frm(item_code, batch_no, uom) {
		const has_batch_no = batch_no;
		return this.frm.doc.items.find(
			i => i.item_code === item_code
				&& (!has_batch_no || (has_batch_no && i.batch_no === batch_no))
				&& (i.uom === uom) && (i.is_free_item === 0)
		);
	}
	get_combo_item_from_frm(item_code, parent_item) {
		
		return this.frm.doc.seleceted_packed_items.find(
			i => i.item_code === item_code && i.parent_item===parent_item
				
		);
	}
	edit_item_details_of(item_row) {
		this.item_details.toggle_item_details_section(item_row);
	}
	edit_combo_item_details_of(item_row) {
		
		this.combo_item_details.toggle_combo_item_details_section(item_row);
	}
	is_current_item_being_edited(item_row) {
		
		const { item_code, batch_no } = this.item_details.current_item;
		
     	//console.log(this.item_details.current_item,item_row,batch_no,"batchno",item_row.batch_no,item_code,"code",item_row.item_code)
		return item_code !== item_row.item_code || batch_no != item_row.batch_no ?  false : true;
	}
	is_current_combo_item_being_edited(item_row) {
		
		const { item_code, batch_no } = this.combo_item_details.current_item;
		
     	//console.log(this.item_details.current_item,item_row,batch_no,"batchno",item_row.batch_no,item_code,"code",item_row.item_code)
		return item_code !== item_row.item_code || batch_no != item_row.batch_no ?  false : true;
	}
	update_cart_html(item_row, remove_item) {
		
		this.cart.update_item_html(item_row, remove_item);
        // this.cart.update_item_html(item_row,remove_item,function(){
        //     cur_pos.cart.check_minimum_sales_qty=false;
        //         console.log($('.cart-item-wrapper .quantity input'),"qtyobject")
        //         $('.cart-item-wrapper .quantity input').change();
        //         cur_pos.cart.check_minimum_sales_qty=true;
        // });
		this.cart.update_totals_section(this.frm);
       
	}
	update_cart_html_uom(item_row, nuom,convfactor) {
		this.cart.update_item_html(item_row, remove_item);
		this.cart.update_totals_section(this.frm);
	}
	check_serial_batch_selection_needed(item_row) {
		// right now item details is shown for every type of item.
		// if item details is not shown for every item then this fn will be needed
		const serialized = item_row.has_serial_no;
		const batched = item_row.has_batch_no;
		const no_serial_selected = !item_row.serial_no;
		const no_batch_selected = !item_row.batch_no;

		if ((serialized && no_serial_selected) || (batched && no_batch_selected) ||
			(serialized && batched && (no_batch_selected || no_serial_selected))) {
			return true;
		}
		return false;
	}

	async trigger_new_item_events(item_row) {
       
        
		await this.frm.script_manager.trigger('item_code', item_row.doctype, item_row.name);
		await this.frm.script_manager.trigger('qty', item_row.doctype, item_row.name);
		const  is_bundle = await frappe.db.get_value("Product Bundle", {"new_item_code":item_row.item_code} , "name");
		
			if(is_bundle.message.name)
             {
				
				await frappe.model.set_value(item_row.doctype, item_row.name, 'bundle_item', 1);
			 }

        // await this.frm.script_manager.trigger('uom', item_row.doctype, item_row.name);
        // await this.frm.script_manager.trigger('conversion_factor', item_row.doctype, item_row.name);
        
	}
    async trigger_new_item_events_so(item_row,rate,uom) {
       
        
		await this.frm.script_manager.trigger('item_code', item_row.doctype, item_row.name);
		await this.frm.script_manager.trigger('qty', item_row.doctype, item_row.name);        
        await frappe.model.set_value(item_row.doctype, item_row.name, 'stock_uom', uom);
        await frappe.model.set_value(item_row.doctype, item_row.name, 'uom', uom);       
        await frappe.model.set_value(item_row.doctype, item_row.name, 'rate', rate);
		const  is_bundle = await frappe.db.get_value("Product Bundle", {"new_item_code":item_row.item_code} , "name");
			if(is_bundle.message.name)
             {
				
				await frappe.model.set_value(item_row.doctype, item_row.name, 'bundle_item', 1);
			 }
		
        
	}
	async check_stock_availability(item_row, qty_needed, warehouse) {
		const available_qty = (await this.get_available_stock(item_row.item_code, warehouse)).message;

		frappe.dom.unfreeze();
		const bold_item_code = item_row.item_code.bold();
		const bold_warehouse = warehouse.bold();
		const bold_available_qty = available_qty.toString().bold()
		if (!(available_qty > 0)) {
			const  res = await frappe.db.get_value("Item",  item_row.item_code, "is_stock_item");
			if(res.message.is_stock_item==1)
             {
			frappe.model.clear_doc(item_row.doctype, item_row.name);
			frappe.throw({
				title: __("Not Available"),
				message: __('Item Code: {0} is not available under warehouse {1}.', [bold_item_code, bold_warehouse])
			})
		}
		} else if (available_qty < qty_needed) {
			frappe.show_alert({
				message: __('Stock quantity not enough for Item Code: {0} under warehouse {1}. Available quantity {2}.', [bold_item_code, bold_warehouse, bold_available_qty]),
				indicator: 'orange'
			});
			frappe.utils.play_sound("error");
		}
		frappe.dom.freeze();
	}

	async check_serial_no_availablilty(item_code, warehouse, serial_no) {
		const method = "erpnext.stock.doctype.serial_no.serial_no.get_pos_reserved_serial_nos";
		const args = {filters: { item_code, warehouse }}
		const res = await frappe.call({ method, args });

		if (res.message.includes(serial_no)) {
			frappe.throw({
				title: __("Not Available"),
				message: __('Serial No: {0} has already been transacted into another POS Invoice.', [serial_no.bold()])
			});
		}
	}

	get_available_stock(item_code, warehouse) {
		const me = this;
		return frappe.call({
			method: "erpnext.accounts.doctype.pos_invoice.pos_invoice.get_stock_availability",
			args: {
				'item_code': item_code,
				'warehouse': warehouse,
			},
			callback(res) {
				if (!me.item_stock_map[item_code])
					me.item_stock_map[item_code] = {}
				me.item_stock_map[item_code][warehouse] = res.message;
			}
		});
	}

	update_item_field(value, field_or_action) {
		if (field_or_action === 'checkout') {
			this.item_details.toggle_item_details_section(undefined);
			
		} else if (field_or_action === 'remove') {
            console.log("remove_item_from_cartELSE")
			this.remove_item_from_cart();
		} else {
			const field_control = this.item_details[`${field_or_action}_control`];
			if (!field_control) return;
			field_control.set_focus();
			value != "" && field_control.set_value(value);
		}
	}
    update_combo_item_field() {
        
		 
		 this.remove_item_from_combo_cart();
		
	}
    remove_item_from_combo_cart() {
       
		const { doctype, name, current_item } = this.combo_item_details;
        let{combodoctype,comboname,combo_current_item}=''
        frappe.model.set_value(doctype, name, 'qty', 0)
			.then(() => {
               
				frappe.model.clear_doc(doctype, name);
				this.update_cart_html(current_item, true);
				this.item_details.toggle_item_details_section(undefined);
                cur_frm.doc.seleceted_packed_items.forEach(citem => {
                    combodoctype='Selected Packed Items';
                    comboname=citem.name; 
                    if(String(citem.parent_item)==String(current_item.item_code))  
                    {
                        frappe.model.set_value(combodoctype, comboname, 'packed_quantity', 0)
                    }        
                  
                          
                   
                })
				frappe.dom.unfreeze();
			})
			.catch(e => console.log(e));
        
       
	}
	remove_item_from_cart() {
       
		frappe.dom.freeze();
        
		const { doctype, name, current_item } = this.item_details;
      
		frappe.model.set_value(doctype, name, 'qty', 0)
			.then(() => {
               
				frappe.model.clear_doc(doctype, name);
				this.update_cart_html(current_item, true);
				this.item_details.toggle_item_details_section(undefined);
				frappe.dom.unfreeze();
			})
			.catch(e => console.log(e));
	}
	create_event_booking()
    {
		
        if(!cur_pos.cart.location_so_field.value && cur_pos.cart.location_event_field.value && cur_pos.cart.location_event_slot_field.value  ) 
        {
			//cur_frm.doc.posting_date.set_value(cur_pos.cart.location_visitdate.value)
            const method = "vim.custom_script.point_of_sale.point_of_sale.create_event_booking";
            frappe.call({
                 method,  
                 freeze:true,
                 args:{pos_invoice:cur_frm.doc.name,
					event:cur_pos.cart.location_event_field.value,
					posting_date:cur_frm.doc.posting_date,
					slot:cur_pos.cart.location_event_slot_field.value,
					brand:cur_pos.cart.location_brand_field.value,
					city:cur_pos.cart.location_city_field.value,
					branch:cur_pos.cart.location_branch_field.value,
					department:cur_pos.cart.location_department_field.value
				} 
                });
                

        }    
        
    }
    update_Item()
    {
        // if(!cur_pos.cart.custom_field.value && cur_pos.cart.event_field.value ) 
        // {
        //     const method = "vim.custom_script.point_of_sale.point_of_sale.update_Item";
            
        //         frappe.call({
        //             method,  
        //              freeze:true,
        //              args:{event:cur_pos.cart.event_field.value} 
        //             });    

        // }   
		// else{console.log
			
			cur_frm.doc.items.forEach(item => {				
                
				 const method = "vim.custom_script.point_of_sale.point_of_sale.update_Item";
            
                frappe.call({
                    method,  
                     freeze:true,
                     args:{event: item.item_code} 
                    });    
			})

		// } 
    }
	update_POS_Item()
    {
        if(!cur_pos.cart.location_so_field.value && cur_pos.cart.location_event_field.value   ) 
        {
			
            const method = "vim.custom_script.point_of_sale.point_of_sale.update_POS_Item";
            
                frappe.call({
                    method,  
                     freeze:true,
                     args:{pos_invoice:cur_frm.doc.name,
						event:cur_pos.cart.location_event_field.value,
						slot:cur_pos.cart.location_event_slot_field.value} 
                    });    

        } 
		  
    }
	update_POS()
    {
        if(!cur_pos.cart.location_so_field.value )
			//&& cur_pos.cart.location_event_field.value  ) 
        {
			
            // const method = "vim.custom_script.point_of_sale.point_of_sale.update_POS";
            //     frappe.call({
            //         method,  
            //          freeze:true,
			// 		 async:false,
            //          args:{pos_invoice:cur_frm.doc.name,
			// 			brand:cur_pos.cart.location_brand_field.value,
			// 			city:cur_pos.cart.location_city_field.value,
			// 			branch:cur_pos.cart.location_branch_field.value,
            //             slot:cur_pos.cart.location_event_slot_field.value,
            //             event:cur_pos.cart.location_event_field.value,
			// 			department:cur_pos.cart.location_department_field.value} 
            //         });    

        } 
		else{
			return frappe.call({
				async:false,
				method: "vim.custom_script.point_of_sale.point_of_sale.update_accounting_dimension",
				args: {
					'sales_order': cur_pos.cart.location_so_field.value,
					'pos_invoice':cur_frm.doc.name
				}
			});

		}
		  
    }
	
};

