import onScan from 'onscan.js';

erpnext.PointOfSale.ItemSelector = class {
	// eslint-disable-next-line no-unused-vars
	constructor({ frm, wrapper, events, pos_profile, settings }) {
		this.wrapper = wrapper;
		this.events = events;
		this.pos_profile = pos_profile;
		this.hide_images = settings.hide_images;
		this.auto_add_item = settings.auto_add_item_to_cart;
        this.minimum_sales_quantity=0;
        this.maximum_sales_quantity=0;
        this.bundle_item=undefined;
		this.inti_component();
	}

	inti_component() {
		this.prepare_dom();
		this.make_search_bar();
		this.load_items_data();
		this.bind_events();
		this.attach_shortcuts();
        this.get_item_group();     

		
	}

	prepare_dom() {
		this.wrapper.append(
			`  <section class="items-selector">
            <div class="pos-item-category search-item-group" style="background:grey;height:100%;width:10%;position:absolute;">
							<ul class="pos-item-cat dropdown-menu" style=" display: block;
                            position: unset;
                            min-width: unset;
                            min-height: 100%;
                            width: 100%;
                            background-color: #485663;
                            color: #e6e6e6;
                            overflow: hidden;
                            margin: 0px;"></ul>
							<ul class="pos-item-sub-cat dropdown-sub-menu" style=" 
							display: none;
                            position: unset;
                            min-width: unset;
                            min-height: 100%;
                            width: 50%;
                            background-color:#rgb(99 128 155);
                            color: #e6e6e6;
                            overflow: hidden;
                            margin: 0px;"></ul>
						</div>
						
            
                 <div class="filter-section" style="width:80%;align-self:flex-end;">
                     <div class="label" style="display:none;">All Items</div>
					 <div class="item-group-field"></div>
                     <div class="search-field"></div>
					 <div class="pagination"></div>
                     
                 </div>
				
                 <div class="items-container" style="width:80%;align-self:flex-end;"></div>
               
             </section>`
		);
		this.$component = this.wrapper.find('.items-selector');
		this.$items_container = this.$component.find('.items-container');
		this.$component.find('.filter-section').css({'padding':'','padding-left':'35px','padding-bottom':''})
		this.$component.find('.pagination').css({
			
			'padding': '10px 0px 0px 0px',
			'margin': '0px 0px 10px 0px',
			'width': '80%',
    		'align-self': 'flex-end'
		})
		this.$component.css('height','90vh')
		this.search_item_group = this.wrapper.find('.search-item-group');
		this.search_item_group.find('.dropdown-sub-menu').css({
			
			'padding': '4px',
    'font-size': 'var(--text-md)',
    'max-height': '500px'

		})
	}
	
	async load_items_data() {
		if (!this.item_group) {
			const res = await frappe.db.get_value("Item Group", {lft: 1, is_group: 1}, "name");
			this.parent_item_group = res.message.name;
		}
        
		if (!this.price_list) {
			const res = await frappe.db.get_value("POS Profile", this.pos_profile, "selling_price_list");
			this.price_list = res.message.selling_price_list;
		}

		this.get_items({}).then(({message}) => {
			this.render_item_list(message.items);
			this.pagination();
		});
	}

	get_items({start = 0, page_length = 40, search_value=''}) {
		const doc = this.events.get_frm().doc;
		const price_list = (doc && doc.selling_price_list) || this.price_list;
		let { item_group, pos_profile } = this;
       
		!item_group && (item_group = this.parent_item_group);
        if(price_list)
        {
            return frappe.call({
                method: "vim.custom_script.point_of_sale.point_of_sale.get_pos_items",
                freeze: true,
                args: { start, page_length, price_list, item_group, search_value, pos_profile },
            });
        }
		
	}


	render_item_list(items) {
		this.$items_container.html('');
        
		
		items.forEach(item => {
			const item_html = this.get_item_html(item);
			this.$items_container.append(item_html);
		});
	}

	get_item_html(item) {
		const me = this;
		// eslint-disable-next-line no-unused-vars
		const { item_image, serial_no, batch_no, barcode, actual_qty, stock_uom,warehouse_reorder_level } = item;
		if(warehouse_reorder_level){
            var indicator_color_=actual_qty > warehouse_reorder_level ? "green" : actual_qty <= (warehouse_reorder_level *50/100) ? "orange" : "orange";
        }
        else{

        var  indicator_color_ = actual_qty > 10 ? "green" : actual_qty <= 0 ? "red" : "orange";
        
            
           
        }
        const indicator_color =indicator_color_
		let qty_to_display = actual_qty;

		if (Math.round(qty_to_display) > 999) {
			qty_to_display = Math.round(qty_to_display)/1000;
			qty_to_display = qty_to_display.toFixed(1) + 'K';
		}
        // if (Math.round(qty_to_display) < 0) {
		// 	qty_to_display = '';
			
		// }

		function get_item_image_html() {
			if (!me.hide_images && item_image) {
				return `<div class="item-qty-pill">
							<span class="indicator-pill whitespace-nowrap ${indicator_color}">${qty_to_display}</span>
						</div>
						<div class="flex items-center justify-center h-32 border-b-grey text-6xl text-grey-100">
							<img class="h-full" src="${item_image}" alt="${frappe.get_abbr(item.item_name)}" style="object-fit: cover;height:135px;">
						</div>`;
			} else {
				return `<div class="item-qty-pill">
							<span class="indicator-pill whitespace-nowrap ${indicator_color}">${qty_to_display}</span>
						</div>
						<div class="item-display abbr">${frappe.get_abbr(item.item_name)}</div>`;
			}
		}
		this.$component.find('.item-rate').css({
			'background-color': '#0799a3bd'
		})
		return (
			`<div class="item-wrapper"
				data-item-code="${escape(item.item_code)}" data-serial-no="${escape(serial_no)}"
				data-batch-no="${escape(batch_no)}" data-uom="${escape(stock_uom)}" data-item-rate="${escape(item.price_list_rate)}"
				title="${item.item_name}"
                data-minimum-sales-qty="${escape(item.minimum_sales_quantity)}"
                data-maximum-sales-qty="${escape(item.maximum_sales_quantity)}"
                data-bundle-item="${escape(item.bundle_item)}">

				${get_item_image_html()}

				<div class="item-detail">
					<div class="item-name">
						${frappe.ellipsis(item.item_name, 18)}
					</div>
					<div class="item-rate">${format_currency(item.price_list_rate, item.currency,2) || 0}</div>
				</div>
			</div>`
		);
		
		
	}

	make_search_bar() {
		const me = this;
		const doc = me.events.get_frm().doc;
		this.$component.find('.search-field').html('');
		this.$component.find('.item-group-field').html('');
		this.$component.find('.search-field').css({
			'grid-column': 'span 5/span 5',
			'width':'200px'

		})
		
		this.search_field = frappe.ui.form.make_control({
			df: {
				label: __('Search'),
				fieldtype: 'Data',
				placeholder: __('Search by item code, serial number or barcode')
			},
			parent: this.$component.find('.search-field'),
			render_input: true,
		});
		this.item_group_field = frappe.ui.form.make_control({
			df: {
				label: __('Item Group'),
				fieldtype: 'Link',
				options: 'Item Group',
				placeholder: __('Select item group'),
				onchange: function() {
					me.item_group = this.value;
					!me.item_group && (me.item_group = me.parent_item_group);
					me.filter_items();
				},
				get_query: function () {
					return {
						query: 'erpnext.selling.page.point_of_sale.point_of_sale.item_group_query',
						filters: {
							pos_profile: doc ? doc.pos_profile : ''
						}
					};
				},
			},
			parent: this.$component.find('.item-group-field'),
			render_input: true,
		});
		// this.search_field.toggle_label(false);
		// this.item_group_field.toggle_label(false);
	}

	set_search_value(value) {
		$(this.search_field.$input[0]).val(value).trigger("input");
	}

	bind_events() {
		const me = this;
		window.onScan = onScan;

		onScan.decodeKeyEvent = function (oEvent) {
			var iCode = this._getNormalizedKeyNum(oEvent);
			switch (true) {
				case iCode >= 48 && iCode <= 90: // numbers and letters
				case iCode >= 106 && iCode <= 111: // operations on numeric keypad (+, -, etc.)
				case (iCode >= 160 && iCode <= 164) || iCode == 170: // ^ ! # $ *
				case iCode >= 186 && iCode <= 194: // (; = , - . / `)
				case iCode >= 219 && iCode <= 222: // ([ \ ] ')
				case iCode == 32: // spacebar
					if (oEvent.key !== undefined && oEvent.key !== '') {
						return oEvent.key;
					}

					var sDecoded = String.fromCharCode(iCode);
					switch (oEvent.shiftKey) {
						case false: sDecoded = sDecoded.toLowerCase(); break;
						case true: sDecoded = sDecoded.toUpperCase(); break;
					}
					return sDecoded;
				case iCode >= 96 && iCode <= 105: // numbers on numeric keypad
					return 0 + (iCode - 96);
			}
			return '';
		};

		onScan.attachTo(document, {
			onScan: (sScancode) => {
				if (this.search_field && this.$component.is(':visible')) {
					this.search_field.set_focus();
					this.set_search_value(sScancode);
					this.barcode_scanned = true;
				}
			}
		});

		this.$component.on('click', '.item-wrapper', function() {
			
			const $item = $(this);
           
			const item_code = unescape($item.attr('data-item-code'));
			let batch_no = unescape($item.attr('data-batch-no'));
			let serial_no = unescape($item.attr('data-serial-no'));
			let uom = unescape($item.attr('data-uom'));
            let rate=unescape($item.attr('data-item-rate'));
            const minimum_sales_quantity=unescape($item.attr('data-minimum-sales-qty'));
            const maximum_sales_quantity=unescape($item.attr('data-maximum-sales-qty'));
			var bundle_item=unescape($item.attr('data-bundle-item'));
			cur_pos.item_selector.minimum_sales_quantity=minimum_sales_quantity;
             cur_pos.item_selector.maximum_sales_quantity=maximum_sales_quantity;
			 cur_pos.item_selector.bundle_item=bundle_item;
            // console.log(this.minimum_sales_quantity,this.maximum_sales_quantity,"this.maximum_sales_quantity")
            console.log(unescape($item.attr('data-item-rate')),"ITM")
			// escape(undefined) returns "undefined" then unescape returns "undefined"
			batch_no = batch_no === "undefined" ? undefined : batch_no;
			serial_no = serial_no === "undefined" ? undefined : serial_no;
			uom = uom === "undefined" ? undefined : uom;
			// if(minimum_sales_quantity && minimum_sales_quantity>0)
            //     {
                 
            //         const maximum_sales_quantity=unescape($item.attr('data-minimum-sales-qty'));
            //         me.events.item_selected({ field: 'qty',value: minimum_sales_quantity, item: { item_code, batch_no, serial_no, uom }});
            //     }
            //     else{
					
            //         me.events.item_selected({ field: 'qty', value: "+1", item: { item_code, batch_no, serial_no, uom }});
            //     }
           
				if(minimum_sales_quantity && minimum_sales_quantity>0)
                {
                 
                    const maximum_sales_quantity=unescape($item.attr('data-minimum-sales-qty'));
					//frappe.db.get_value("Product Bundle", {"new_item_code":item_code} ,"name", (r)=> {
                
                    if(cur_pos.item_selector.bundle_item && cur_pos.item_selector.bundle_item!='' && cur_pos.item_selector.bundle_item!='null' && cur_pos.item_selector.bundle_item!='undefined' && cur_pos.item_selector.bundle_item!=0)  {
					
							bundle_item=1
							
							me.events.bundle_item_selected({ field: 'qty',value: minimum_sales_quantity, item: { item_code, batch_no, serial_no, uom,rate }}).then(() => {
                                const event = {
                                    field: "qty",
									value:minimum_sales_quantity,
                                    item: { item_code, batch_no, uom }
                                }
                                 
                                 setTimeout(() => {
                                 
                                 cur_frm.doc.items.forEach(item => {

                                    cur_pos.cart.update_item_html(item);
                                });
                                 
                                }, 800);
                                
                        })
			
						}
						else{
							bundle_item=0
							
							me.events.item_selected({ field: 'qty',value: minimum_sales_quantity, item: { item_code, batch_no, serial_no, uom,rate }}).then(() => {
                                const event = {
                                    field: "qty",
									value:minimum_sales_quantity,
                                    item: { item_code, batch_no, uom }
                                }
                                 
                                 setTimeout(() => {
                                 
                                 cur_frm.doc.items.forEach(item => {

                                    cur_pos.cart.update_item_html(item);
                                });
                                 
                                }, 800);
                                
                        })
                                
                           
						}
		
					//})
					
					
                }
                else{
					//frappe.db.get_value("Product Bundle", {"new_item_code":item_code} ,"name", (r)=> {
                
                    if(cur_pos.item_selector.bundle_item && cur_pos.item_selector.bundle_item!='' && cur_pos.item_selector.bundle_item!='null' && cur_pos.item_selector.bundle_item!='undefined' && cur_pos.item_selector.bundle_item!=0)  {
					
							bundle_item=1
							
							me.events.bundle_item_selected({ field: 'qty', value: "+1", item: { item_code, batch_no, serial_no, uom,rate }})
							.then(() => {
                                const event = {
                                    field: "qty",
                                    value:"+1",
                                    item: { item_code, batch_no, uom }
                                }
                                 
                                 setTimeout(() => {
                                 
                                 cur_frm.doc.items.forEach(item => {

                                    cur_pos.cart.update_item_html(item);
                                });
                                 
                                }, 800);
                                
                        })
						}
						else{
							bundle_item=0
							
							me.events.item_selected({ field: 'qty', value: "+1", item: { item_code, batch_no, serial_no, uom ,rate}})
                            .then(() => {
                                const event = {
                                    field: "qty",
                                    value:"+1",
                                    item: { item_code, batch_no, uom }
                                }
                                 
                                 setTimeout(() => {
                                
                                 cur_frm.doc.items.forEach(item => {

                                    cur_pos.cart.update_item_html(item);
                                });
                                 
                                }, 800);
                                
                        })
						}
		
					//})
                    
                }
               
            me.set_search_value('');
           
			})

		
		//});
       
		this.search_field.$input.on('input', (e) => {
			clearTimeout(this.last_search);
			this.last_search = setTimeout(() => {
				const search_term = e.target.value;
				this.filter_items({ search_term });
			}, 300);
		});
	}
	
	attach_shortcuts() {
		const ctrl_label = frappe.utils.is_mac() ? '⌘' : 'Ctrl';
		this.search_field.parent.attr("title", `${ctrl_label}+I`);
		frappe.ui.keys.add_shortcut({
			shortcut: "ctrl+i",
			action: () => this.search_field.set_focus(),
			condition: () => this.$component.is(':visible'),
			description: __("Focus on search input"),
			ignore_inputs: true,
			page: cur_page.page.page
		});
		this.item_group_field.parent.attr("title", `${ctrl_label}+G`);
		frappe.ui.keys.add_shortcut({
			shortcut: "ctrl+g",
			action: () => this.item_group_field.set_focus(),
			condition: () => this.$component.is(':visible'),
			description: __("Focus on Item Group filter"),
			ignore_inputs: true,
			page: cur_page.page.page
		});

		// for selecting the last filtered item on search
		frappe.ui.keys.on("enter", () => {
			const selector_is_visible = this.$component.is(':visible');
			if (!selector_is_visible || this.search_field.get_value() === "") return;

			if (this.items.length == 1) {
				this.$items_container.find(".item-wrapper").click();
				frappe.utils.play_sound("submit");
				$(this.search_field.$input[0]).val("").trigger("input");
			} else if (this.items.length == 0 && this.barcode_scanned) {
				// only show alert of barcode is scanned and enter is pressed
				frappe.show_alert({
					message: __("No items found. Scan barcode again."),
					indicator: 'orange'
				});
				frappe.utils.play_sound("error");
				this.barcode_scanned = false;
				$(this.search_field.$input[0]).val("").trigger("input");
			}
		});
	}

	filter_items({ search_term='' }={}) {
       
		
			search_term = search_term.toLowerCase();

			// memoize
			this.search_index = this.search_index || {};
			if (this.search_index[search_term]) {
				const items = this.search_index[search_term];
				this.items = items;
				this.render_item_list(items);
				this.pagination();
               
				this.auto_add_item && this.items.length == 1 && this.add_filtered_item_to_cart();
				return;
			}
		
        
		this.get_items({ search_value: search_term })
			.then(({ message }) => {
				// eslint-disable-next-line no-unused-vars
				const { items, serial_no, batch_no, barcode } = message;
				if (search_term && !barcode) {
					this.search_index[search_term] = items;
				}
				this.items = items;
				this.render_item_list(items);
				this.pagination();
               
                if(this.items.length == 1 && search_term){
				    this.auto_add_item && this.items.length == 1 && this.add_filtered_item_to_cart();
                }

			});
        
	}

	add_filtered_item_to_cart() {
		this.$items_container.find(".item-wrapper").click();
	}

	resize_selector(minimize) {
		minimize ?
			this.$component.find('.filter-section').css('grid-template-columns', 'repeat(1, minmax(0, 1fr))') :
			this.$component.find('.filter-section').css('grid-template-columns', 'repeat(12, minmax(0, 1fr))');
			
		
		minimize ?
			this.$component.find('.search-field').css('margin', 'var(--margin-sm) 0px') :
			this.$component.find('.search-field').css('margin', '0px var(--margin-sm)');

		minimize ?
			this.$component.css('grid-column', 'span 2 / span 2') :
			this.$component.css('grid-column', 'span 6 / span 6');

		minimize ?
			this.$items_container.css('grid-template-columns', 'repeat(1, minmax(0, 1fr))') :
			this.$items_container.css('grid-template-columns', 'repeat(4, minmax(0, 1fr))');
		minimize ?
			this.$component.find('.search-item-group').css('width','5%'):            
			this.$component.find('.search-item-group').css('width','10%');	
        if(this.item_sub_groups.length>0)
            {
               
				if(this.$component.find('.filter-section').is(":visible")){
					this.$component.find('.search-item-group').css('width','5%');
					
				}
				else{
					
					this.$component.find('.search-item-group').css('width','20%');	
				}
                
            }
		
	}

	toggle_component(show) {
		show ? this.$component.css('display', 'flex') : this.$component.css('display', 'none');
	}
    //added by shiby
    show_sub_group(show){
		
		if(show){
           
			this.$component.find('.pos-item-sub-cat').css({
				'display': 'block',
                'width': '80%'
			})
            this.$component.find('.filter-section').css({
				'display': 'none'
               
			})
            this.$component.find('.items-container').css({
				'display': 'none'
               
			})
			this.$component.find('.pos-item-cat').css({
				'width': '20%'
			})
            this.$component.find('.search-item-group').css({
				'width': '50%'
			})
        
			
		}
		else{
			this.$component.find('.pos-item-sub-cat').css({
				'display': 'none'
			})
			this.$component.find('.pos-item-cat').css({
				'width': '100%'
			})
            this.$component.find('.items-container').css({
				'display': 'grid'
               
			})
			
            this.$component.find('.filter-section').css({
				'display': 'grid'
               
			})
            this.$component.find('.search-item-group').css({
				'width': '10%'
			})

		}
		if(this.$component.find('.filter-section').is(":visible")){
			this.$component.find('.search-item-group').css('width','10%');
			
			
		}
		else{
			
			this.$component.find('.search-item-group').css('width','20%');	
		}
	}
	get_item_group() {
        
		var me = this;
		frappe.call({
			method: "vim.custom_script.point_of_sale.point_of_sale.get_item_group",
			freeze: true,
			args: {
				pos_profile: me.pos_profile ? me.pos_profile : ''
			}
		}).then(r => {
			me.item_groups = r.message['item_group_dict'];
			// me.item_sub_groups=r.message['item_sub_group_dict'];
            
			me.search_item_group = me.wrapper.find('.search-item-group');
			// var dropdown_html = me.get_sorted_item_groups().map(function(item_group) {
			// 	var itmgrm=item_group
				
			// 	return `<li style='margin: 0 5px;border-bottom: 1px solid #cccac6;font-size: 11px;padding: 15px 1px;'><a class='option' style="padding: 0;" data-value='`+item_group+`'>`+item_group+`</a>
			// 	${me.get_sorted_item_sub_groups(item_group).map(function(item_sgroup) {
					
			// 		return `<li class="subgroup`+itmgrm+` "style='margin: 0 5px;display:none;overflow: hidden;background-color: silver;border-bottom: 1px solid #cccac6;font-size: 11px;padding: 15px 1px;'><a class='option' data-value='`+item_sgroup+`'>`+item_sgroup+`</a>
					
			// 		</li>`
			// 	 })}
			// 	</li>`;
			//  }
			//  ).join("");
			var dropdown_html = me.get_sorted_item_groups().map(function(item_group) {
				var itmgrm=item_group
				
				return `<li style='margin: 0 5px;border-bottom: 1px solid #cccac6;font-size: 11px;padding: 15px 1px;'><a class='option' style="padding: 0;" data-value='`+item_group+`'>`+item_group+`</a>
				
				</li>`;
			 }
			 ).join("");
			
			me.search_item_group.find('.dropdown-menu').html(dropdown_html);
			
			me.search_item_group.on('click', '.dropdown-menu a', function() {
			
				if(cur_pos.combo_item_details.wrapper.find('.combo-item-details-container').is(":visible")){
					frappe.throw("Please close Item Bundle popup")

				}
				me.item_group_field.set_value($(this).attr('data-value'));
				
                if(cur_pos.item_details.wrapper.find('.item-details-container').is(":visible")){
                    cur_pos.item_details.events.close_item_details()
                 }
                me.show_sub_group(false);
				me.get_item_sub_group($(this).attr('data-value'))
				
				
			});
            me.search_item_group.find('.dropdown-menu').find("a:first").trigger("click");
           
		});
	}
	
	get_item_sub_group(item_group){
		var me=this;
        //me.show_sub_group(false);
		var sub_html ='<div class="row" style="width: 100%; ">';
				frappe.call({
					method: "vim.custom_script.point_of_sale.point_of_sale.get_item_sub_group",
					freeze: true,
					args: {
						pos_profile: me.pos_profile ? me.pos_profile : '',
						item_group:item_group?item_group:''
					}
				}).then(r => {
			me.item_sub_groups=r.message['item_sub_group_dict'];
           	me.search_item_group = me.wrapper.find('.search-item-group');
               
			   if(me.item_sub_groups.length>0)
			   {
				me.show_sub_group(true);
			   }
               
			var dropdown_html = me.get_sorted_item_sub_groups().map(function(item_group) {
				var itmgrm=item_group
				
				return `<div class="col-md-4"><li style='margin: 0 5px;border-bottom: 1px solid #cccac6;font-size: 11px;padding: 15px 1px;'><a class='option' style="padding: 0;" data-value='`+item_group+`'>`+item_group+`</a>
				
				</li></div>`;
			 }
			 ).join("");
             dropdown_html=sub_html+dropdown_html+'</div>'
			me.search_item_group.find('.dropdown-sub-menu').html(dropdown_html);
			
			me.search_item_group.on('click', '.dropdown-sub-menu a', function() {
			
				me.item_group_field.set_value($(this).attr('data-value'));
				var classname="subgroup"+$(this).attr('data-value');
				me.$subgroup = me.search_item_group.find("."+classname+"");	
				if	(me.$subgroup)	{
					me.$subgroup.css('display', 'block');

				}
				
				me.show_sub_group(false);
						
					this.$component.find('.search-item-group').css('width','5%');	
				
			});
				// 	this.item_sub_groups=r.message;
					
				// 	return this.get_sorted_item_sub_groups().map(function(item_group) {

				// 	 var html= "<li style='margin: 0 5px;border-bottom: 1px solid #cccac6;font-size: 11px;padding: 15px 1px;'><a class='option' data-value='"+item_group+"'>"+item_group+"</a></li>";
					 
					 
				// 	})						
						
					
			})			
					
	}
	
	
	get_sorted_item_sub_groups(item_group) {
       // console.log("get_sorted_item_sub_groups")
		var list = {}
		var filtered =  this.item_sub_groups.filter(function(hero) {
			return hero.parent_item_group == item_group;
		});
			
		
	var	item_sub_group_dict={};
		$.each(filtered, function(i, data) {		
			item_sub_group_dict[data.name] = [data.lft, data.rgt]
		})
		
		$.each(item_sub_group_dict, function(i, data) {
			list[i] = data[0]
		})

		return Object.keys(list).sort(function(a,b){return list[a]-list[b]})
	}
	get_sorted_item_groups() {
		var list = {}
		$.each(this.item_groups, function(i, data) {
			
			list[i] = data[0]
		})
			
		return Object.keys(list).sort(function(a,b){return list[a]-list[b]})
	}
	
	pagination() {
		var me = this;
		const pageSize = 2;
        const showpage=3;
        var diffpage=0;
		me.wrapper.find('.pagination').empty().hide();
		var pageCount = Math.ceil((me.wrapper.find(".item-wrapper").size() || 1)/4)
		
		pageCount = pageCount / pageSize;
		if (pageCount <= 1)
			return;
		
		var container_list = me.wrapper.find('.items-selector');		
		container_list.find(".pagination").append(`<a class="previous disabled">&laquo;</a>`)
		for(var i = 0; i<pageCount; i++) {
            if(i<showpage)
            {
                container_list.find(".pagination").append(`<a class="page-link">`+(i+1)+`</a>`).show();
            }
            else{
                container_list.find(".pagination").append(`<a class="page-link hide">`+(i+1)+`</a>`).show();
               
            }
            
		}
		container_list.find(".pagination").append(`<a class="next">&raquo;</a>`)
		container_list.find(".pagination a.page-link").first().addClass("active");
		
		const showPage = function() {
		
			var current_page = container_list.find(".pagination a.active");
			var page_n = current_page.text();
         
			var row_idx = (page_n - 1) * pageSize;
			// console.log(page_n+"   "+row_idx)

			var _row = me.wrapper.find(".item-wrapper").eq(row_idx);
			

			var _idx = _row.index();
			var row_height = _row.height();
			var container_height = _row.parent().height();
            

			// var scroll_to = container_height - (_idx * row_height);
			var scroll_to = (_idx * row_height);
			var scroll_to = scroll_to == container_height ? 0 : scroll_to;
			// console.log(container_height+"   "+_idx+"   "+row_height+"   "+scroll_to);
			container_list.find('.items-container').animate({scrollTop: scroll_to}, "fast");
		}
		 
		showPage();
	 
		container_list.find(".pagination a").click(function() {
			var page_idx = $(".pagination a.active").index();
           
			$(".pagination a.page-link").removeClass("active");
			$(".pagination a").removeClass("disabled");
			
			if($(this).hasClass("page-link")) {
				$(this).addClass("active");
                
			}
			
			var pre_idx = (page_idx - 1) >= 1 ? (page_idx - 1) : 1;
			// console.log("prev idx "+ pre_idx);
			if ($(this).hasClass("previous"))
            {
                $(".pagination a").eq(pre_idx).addClass("active");
                if(pre_idx>=showpage)
                {
                    $(".pagination a").eq(pre_idx+1).addClass("hide");
                    $(".pagination a").eq(pre_idx+1-showpage).removeClass("hide")
                    $(".pagination a").eq(pre_idx+1-showpage).css('display','unset')
                }
            }
				
                
			
			if ($(".pagination a.active").index() == 1)
				$(".pagination a.previous").addClass("disabled");
			
			var page_link_len = $(".pagination a").size() - 2;
			var next_idx = (page_idx + 1) <= page_link_len ? (page_idx + 1) : page_link_len;
			var page_link_len = $(".pagination a").size() - 2;
		
			if ($(this).hasClass("next"))
            {
                $(".pagination a").eq(next_idx).addClass("active");
                if(next_idx<page_link_len)
                {
                    $(".pagination a").eq(next_idx+1).removeClass("hide");
                    $(".pagination a").eq(next_idx+1).css('display','unset')
                    
                }
               if(next_idx-showpage>=0)
               {
                if(next_idx-showpage+1<showpage)
                {
                    $(".pagination a").eq(next_idx-showpage+1).addClass("hide");
                }
                
               }

            }
				

			if ($(".pagination a.active").index() == page_link_len)
				$(".pagination a.next").addClass("disabled");

			showPage();
          
            $('.pagination a').css({
			
                'padding': '8px 16px',
                'text-decoration': 'none',
                'margin': '0 1px',
                'background-color': 'white',
                'border': '1px solid #ddd'
                
            })
            
            $('.pagination a:not(.disabled)').css({
                'color': 'black',
                'transition': 'background-color .3s'
            })
            
            $('.pagination a.page-link.active').css({
                'background-color': '#4CAF50',
                'color': 'white',
                'border': '1px solid #4CAF50'
            })
            $('.pagination a.page-link.hide').css({
                'display':'none'
            })
            $('.pagination a.page-link:hover:not(.active)').css({
                'background-color': '#ddd'})
            
                $('.pagination a:first-child').css( {
                'border-top-left-radius': '5px',
                'border-bottom-left-radius': '5px'
            })
            
            $('.pagination a:last-child').css({
                'border-top-right-radius': '5px',
                'border-bottom-right-radius': '5px'
            })
		});
		
        $('.pagination a').css({
			
			'padding': '8px 16px',
			'text-decoration': 'none',
			'margin': '0 1px',
			'background-color': 'white',
			'border': '1px solid #ddd'
			
		})
		
		$('.pagination a:not(.disabled)').css({
			'color': 'black',
			'transition': 'background-color .3s'
		})
		
		$('.pagination a.page-link.active').css({
			'background-color': '#4CAF50',
			'color': 'white',
			'border': '1px solid #4CAF50'
		})
		
		$('.pagination a.page-link:hover:not(.active)').css({
			'background-color': '#ddd'})
		
			$('.pagination a:first-child').css( {
			'border-top-left-radius': '5px',
			'border-bottom-left-radius': '5px'
		})
		
		$('.pagination a:last-child').css({
			'border-top-right-radius': '5px',
			'border-bottom-right-radius': '5px'
		})
	
	}
    
};


