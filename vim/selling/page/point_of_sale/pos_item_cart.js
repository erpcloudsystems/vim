erpnext.PointOfSale.ItemCart = class {
	constructor({ wrapper, events, settings,pos_profile }) {
		this.wrapper = wrapper;
		this.events = events;
		this.customer_info = undefined;
		this.location_info = undefined;
		this.so_info=undefined;
		this.non_sharable_slot=0;
		
		this.hide_images = settings.hide_images;
		this.pos_profile = pos_profile;
		this.allowed_customer_groups = settings.customer_groups;
		this.allow_rate_change = settings.allow_rate_change;
		this.allow_discount_change = settings.allow_discount_change;
		this.disremark='';
		this.init_component();
		this.check_minimum_sales_qty=true;
		this.custom_change_call=false;
		this.old_val_set = 0;
	}

	init_component() {
		this.prepare_dom();
		this.init_child_components();
		this.bind_events();
		this.attach_shortcuts();
		this.set_css();
	}
	make_search_bar() {
		const me = this;
		
		this.$component.find('.sosearch-field').html('');
		
		this.sosearch_field = frappe.ui.form.make_control({
			df: {
				label: __('Search'),
				fieldtype: 'Data',
				placeholder: __('Scan Order Booking No/RFID')
				
			},
			parent: this.$component.find('.sosearch-field'),
			render_input: true,
		});
		
		this.sosearch_field.toggle_label(false);
		
	}

	set_css()
	{
		$('.cart-container').css('padding-left', '3px');
		
		$('.abs-cart-container').css({'padding':'',
		'padding-bottom':''});

	}
	prepare_dom() {
		this.wrapper.append(
			`<section class="customer-cart-container"></section>`
		)
		
		this.$component = this.wrapper.find('.customer-cart-container');
        $('.point-of-sale-app section').css('height','90vh')	
		
	}

	init_child_components() {
		this.init_customer_selector();
		this.init_cart_components();
		this.init_sosearch();
	}
	init_sosearch()
	{
	//this.$component.append(`<div class="sosearch-field"></div>`)
		this.make_search_bar()
	}
	init_customer_selector() {
		this.$component.append(
			`<div class="sosearch-field"></div>
			<div class="customer-section"></div>`
		)
		this.$component.append(
            
			`<div class="location-fields-container">
            <div class="visitdate-field"></div>
			<div class="so-field"></div>
            </div>			
			`
		)
		this.$customer_section = this.$component.find('.customer-section');
		this.$location_fields_container = this.$component.find('.location-fields-container');
        $('.location-fields-container').css({
            				'background-color': '#0799a3bd',
            				'display': 'grid',
            				'grid-template-columns': 'repeat(2,minmax(0,1fr))',
            				'margin-top': 'var(--margin-md)',
            				'-moz-column-gap': 'var(--padding-sm)',
            				'column-gap': 'var(--padding-sm)',
            				'row-gap': 'var(--padding-xs)',
            				'padding-right': '3px',
            				'padding-left': '3px'
                    });
        this.make_customer_selector();
        //added by shiby
		//this.render_location_fields();
        //
	}

	reset_customer_selector() {
		const frm = this.events.get_frm();
		
        
        if(frm.doc.items.length==0){
		frm.set_value('customer', '');
		
		this.make_customer_selector();
		this.customer_field.set_focus();
		}
	}
//<div class="cart-label">Item Cart</div>
	init_cart_components() {
		this.$component.append(
			`<div class="cart-container">
				<div class="abs-cart-container">
					
					<div class="cart-header">
                        
						<div class="name-header">Item</div>
						<div class="qty-header">Qty</div>
						<div class="rate-amount-header">Amount</div>
					</div>
					<div class="cart-items-section"></div>
					<div class="cart-totals-section"></div>
					<div class="numpad-section"></div>
                    
				</div>
			</div>`
		);
		this.$cart_container = this.$component.find('.cart-container');
      
		this.make_cart_totals_section();
		this.make_cart_items_section();
		this.make_cart_numpad();
       
	}
  
	make_cart_items_section() {
		this.$cart_header = this.$component.find('.cart-header');
		this.$cart_items_wrapper = this.$component.find('.cart-items-section');
        this.$abs_cart_container = this.$component.find('.abs-cart-container');
        this.$abs_cart_container = this.$component.find('.abs-cart-container');
        this.$net_total_container = this.$component.find('.net-total-container');
        this.$grand_total_container = this.$component.find('.grand-total-container');
		this.$cart_totals_section=this.$component.find('.cart-totals-section');
		this.make_no_items_placeholder();
	}

	make_no_items_placeholder() {
		
		this.$cart_header.css('display', 'none');
        this.$cart_header.css({'padding-left': '3px;',
        'background-color': '#eceef0'});
        this.$abs_cart_container.css('padding','')
        this.$net_total_container.css({'padding-left': '10px',
		'color': '#fff'})
        this.$grand_total_container.css({'padding-left': '10px',
		'color': '#fff'})
		this.$cart_totals_section.css('background-color','rgba(7, 153, 163, 0.74)')
		this.$component.find('.name-header').css('padding-left', '10px')
		this.$component.find('.abs-cart-container').css('padding', 'unset')
		this.$component.find('.qty-header').css('padding-right', '60px')
		this.$component.find('.taxes-container').css({'padding-left': '10px',
		'color': '#fff'})
		this.$component.find('.add-discount-wrapper').css({'color': '#fff'})
		this.$cart_items_wrapper.html(
			`<div class="no-item-wrapper">No items in cart</div>`
		);
	}

	get_discount_icon() {
		return (
			`<svg class="discount-icon" width="24" height="24" viewBox="0 0 24 24" stroke="currentColor" fill="none" xmlns="http://www.w3.org/2000/svg">
				<path d="M19 15.6213C19 15.2235 19.158 14.842 19.4393 14.5607L20.9393 13.0607C21.5251 12.4749 21.5251 11.5251 20.9393 10.9393L19.4393 9.43934C19.158 9.15804 19 8.7765 19 8.37868V6.5C19 5.67157 18.3284 5 17.5 5H15.6213C15.2235 5 14.842 4.84196 14.5607 4.56066L13.0607 3.06066C12.4749 2.47487 11.5251 2.47487 10.9393 3.06066L9.43934 4.56066C9.15804 4.84196 8.7765 5 8.37868 5H6.5C5.67157 5 5 5.67157 5 6.5V8.37868C5 8.7765 4.84196 9.15804 4.56066 9.43934L3.06066 10.9393C2.47487 11.5251 2.47487 12.4749 3.06066 13.0607L4.56066 14.5607C4.84196 14.842 5 15.2235 5 15.6213V17.5C5 18.3284 5.67157 19 6.5 19H8.37868C8.7765 19 9.15804 19.158 9.43934 19.4393L10.9393 20.9393C11.5251 21.5251 12.4749 21.5251 13.0607 20.9393L14.5607 19.4393C14.842 19.158 15.2235 19 15.6213 19H17.5C18.3284 19 19 18.3284 19 17.5V15.6213Z" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"/>
				<path d="M15 9L9 15" stroke-miterlimit="10" stroke-linecap="round" stroke-linejoin="round"/>
				<path d="M10.5 9.5C10.5 10.0523 10.0523 10.5 9.5 10.5C8.94772 10.5 8.5 10.0523 8.5 9.5C8.5 8.94772 8.94772 8.5 9.5 8.5C10.0523 8.5 10.5 8.94772 10.5 9.5Z" fill="white" stroke-linecap="round" stroke-linejoin="round"/>
				<path d="M15.5 14.5C15.5 15.0523 15.0523 15.5 14.5 15.5C13.9477 15.5 13.5 15.0523 13.5 14.5C13.5 13.9477 13.9477 13.5 14.5 13.5C15.0523 13.5 15.5 13.9477 15.5 14.5Z" fill="white" stroke-linecap="round" stroke-linejoin="round"/>
			</svg>`
		);
	}

	make_cart_totals_section() {
		this.$totals_section = this.$component.find('.cart-totals-section');
       
		// this.$totals_section.append(
		// 	`<div class="add-discount-wrapper">
		// 		${this.get_discount_icon()} Add Discount
		// 	</div>
		// 	<div class="net-total-container">
		// 		<div class="net-total-label">Net Total</div>
		// 		<div class="net-total-value">0.00</div>
		// 	</div>
		// 	<div class="taxes-container"></div>
		// 	<div class="grand-total-container">
		// 		<div>Grand Total</div>
		// 		<div>0.00</div>
		// 	</div>
		// 	<div class="checkout-btn">Checkout</div>
		// 	<div class="edit-cart-btn">Edit Cart</div>`
		// )
		//Commented and added by shiby
		this.$totals_section.append(
			`<div class="add-discount-wrapper">
				<div>${this.get_discount_icon()}Discount</div>
				<div class="discount-value">0.00</div>
			</div>
			<div class="net-total-container">
				<div class="net-total-label">Net Total</div>
				<div class="net-total-value">0.00</div>
			</div>
			<div class="taxes-container"></div>
			<div class="grand-total-container">
				<div>Grand Total</div>
				<div>0.00</div>
			</div>
			<div class="checkout-btn">Checkout</div>
			<div class="btn save-as-draft-btn"  style="display:none;">Approve Discount</div>
			<div class="edit-cart-btn">Edit Cart</div>`
		)

		this.$add_discount_elem = this.$component.find(".add-discount-wrapper");
		this.$add_discount_elem.css({'justify-content': 'space-between'})
		const me = this;
      
		this.$totals_section.on('click', '.save-as-draft-btn', function () {
		//me.save_as_draft();
        me.validate_approver();
            
			
	});
    
	}

	make_cart_numpad() {
		this.$numpad_section = this.$component.find('.numpad-section');

		this.number_pad = new erpnext.PointOfSale.NumberPad({
			wrapper: this.$numpad_section,
			events: {
				numpad_event: this.on_numpad_event.bind(this)
			},
			cols: 5,
			keys: [
				[ 1, 2, 3, 'Quantity' ],
				[ 4, 5, 6, 'Discount' ],
				[ 7, 8, 9, 'Rate' ],
				[ '.', 0, 'Delete', 'Remove' ]
			],
			css_classes: [
				[ '', '', '', 'col-span-2' ],
				[ '', '', '', 'col-span-2' ],
				[ '', '', '', 'col-span-2' ],
				[ '', '', '', 'col-span-2 remove-btn' ]
			],
			fieldnames_map: { 'Quantity': 'qty', 'Discount': 'discount_percentage' }
		})

		this.$numpad_section.prepend(
			`<div class="numpad-totals">
				<span class="numpad-net-total"></span>
				<span class="numpad-grand-total"></span>
			</div>`
		)

		this.$numpad_section.append(
			`<div class="numpad-btn checkout-btn" data-button-value="checkout">Checkout</div>`
		)
	}

	bind_events() {
		const me = this;
		this.$customer_section.on('click', '.reset-customer-btn', function () {
			me.reset_customer_selector();
		});

		
		this.$customer_section.on('click', '.close-details-btn', function () {
			
			me.toggle_customer_info(false);
		});

		this.$customer_section.on('click', '.customer-display', function(e) {
			if ($(e.target).closest('.reset-customer-btn').length) return;

			const show = me.$cart_container.is(':visible');
           
			me.toggle_customer_info(show);
		});
		this.$cart_items_wrapper.on('click', '.list-item', function() {
			me.toggle_item_highlight(this);
			this.item_is_selected=true;
		});
		this.$cart_items_wrapper.on('dblclick', '.cart-item-wrapper', function() {
			const $cart_item = $(this);

			me.toggle_item_highlight(this);
			
			const payment_section_hidden = !me.$totals_section.find('.edit-cart-btn').is(':visible');
			if (!payment_section_hidden) {
				// payment section is visible
				// edit cart first and then open item details section
				me.$totals_section.find(".edit-cart-btn").click();
			}

			const item_code = unescape($cart_item.attr('data-item-code'));
			const batch_no = unescape($cart_item.attr('data-batch-no'));
			const uom = unescape($cart_item.attr('data-uom'));
            var bundle_item=unescape($cart_item.attr('data-bundle-item'));
			const rate=unescape($cart_item.attr('data-item-rate'));
            const free_item=unescape($cart_item.attr('data-item-free'));
            
			var current_item={};
			current_item.item_code = item_code;
			current_item.batch_no = batch_no;
			current_item.uom = uom
			cur_pos.item_details.current_item=current_item;	
			const $btn = $(this);
			current_item.qty = flt($btn.closest(".cart-item-wrapper").find(".quantity input").val())
			cur_pos.combo_item_details.current_item=current_item;
            
            if(cur_frm.doc.is_return)
           {
            frappe.db.get_value("Product Bundle", {"new_item_code":item_code} ,"name", (r)=> {
                
                if(r.name ){
                    bundle_item=1
                    me.events.cart_combo_item_clicked(item_code, batch_no, uom,rate);
                   //const item_row_name = unescape($cart_item.attr('data-row-name'));
                  // me.events.cart_combo_item_clicked({ name: item_row_name });
    
                }
                else{
                    bundle_item=0
                    me.events.cart_item_clicked(item_code, batch_no, uom,rate);
                   //const item_row_name = unescape($cart_item.attr('data-row-name'));
			       // me.events.cart_item_clicked({ name: item_row_name });
                }

            })
           }
           
           else{
            if(free_item==0){
            frappe.db.get_value("Product Bundle", {"new_item_code":item_code} ,"name", (r)=> {
               
                if(r.name ){
                    bundle_item=1

                    if(bundle_item && bundle_item!='' && bundle_item!='null' && bundle_item!="undefined" ){
                        //const item_row_name = unescape($cart_item.attr('data-row-name'));
                       // me.events.cart_combo_item_clicked({ name: item_row_name });
                        me.events.cart_combo_item_clicked(item_code, batch_no, uom,rate);

                     }
                    else{
                        //const item_row_name = unescape($cart_item.attr('data-row-name'));
                       // me.events.cart_item_clicked({ name: item_row_name });
			            me.events.cart_item_clicked(item_code, batch_no, uom,rate);
                    }
                }
                else{
                    bundle_item=0
                    me.events.cart_item_clicked(item_code, batch_no, uom,rate);
                    //const item_row_name = unescape($cart_item.attr('data-row-name'));
			        //me.events.cart_item_clicked({ name: item_row_name });
                }})
            }
            else{
                console.log("free")
                $('.quantity input').attr('readonly', true);
            }
           }
            
			this.numpad_value = '';
		});

		this.$cart_items_wrapper.on('change', '.quantity input', function() {
			const $input = $(this);
           
			const $item = $input.closest('.cart-item-wrapper[data-item-code]');
           
			me.toggle_item_highlight( $item);
			const item_code = unescape($item.attr('data-item-code'));
			var current_item={};
			let batch_no = unescape($item.attr('data-batch-no'));
          
			const serial_no = unescape($item.attr('data-serial-no'));
			const uom = unescape($item.attr('data-uom'));
            const free_item=unescape($item.attr('data-item-free'));
            
			batch_no = batch_no === "undefined" ? undefined : batch_no;
			batch_no = batch_no === "" ? undefined : batch_no;
            const maximum_sales_quantity=unescape($item.attr('data-maximum-sales-qty'));
            const minimum_sales_quantity=unescape($item.attr('data-minimum-sales-qty')) && unescape($item.attr('data-minimum-sales-qty'))!=0?unescape($item.attr('data-minimum-sales-qty')):1
			var bundle_item=unescape($item.attr('data-bundle-item'));
			var rate=unescape($item.attr('data-item-rate'));
			cur_pos.item_selector.bundle_item=bundle_item;
			current_item.item_code = unescape($item.attr('data-item-code'));
			current_item.batch_no = batch_no;
			current_item.uom = unescape($item.attr('data-uom'));
			cur_pos.item_details.current_item=current_item;	
			current_item.qty=flt($('.quantity input').val())
			cur_pos.combo_item_details.current_item=current_item;		
			
           
           if(free_item==0){
                frappe.db.get_value("Product Bundle", {"new_item_code":item_code} ,"name", (r)=> {
               
                if(r.name ){
                    bundle_item =1
                    cur_pos.item_selector.bundle_item=bundle_item;
                    current_item.qty
                    me.events.item_selected({ field: 'qty', value:current_item.qty , item: { item_code, batch_no, serial_no, uom ,rate}}).then(() => {
						const event = {
							field: "qty",
							value:current_item.qty,
							item: { item_code, batch_no, uom }
						}
						 
						 setTimeout(() => {
							me.$cart_items_wrapper.html('');
							me.make_no_items_placeholder();
						 cur_frm.doc.items.forEach(item => {

							cur_pos.cart.update_item_html(item);
						});
						 
						}, 800);
						
				})
                    $('.quantity input').attr('readonly', true);
                }
                else{
                    $('.quantity input').attr('readonly', false);
				if(!cur_frm.doc.is_return && minimum_sales_quantity  && flt($('.quantity input').val())<= minimum_sales_quantity )
				{
					 frappe.show_alert({
					 indicator: 'red',
					 message: "Minimum Sales Quantity is :"+minimum_sales_quantity
				 });
			
			
             	me.events.item_selected({ field: 'qty', value:flt(minimum_sales_quantity) , item: { item_code, batch_no, serial_no, uom ,rate}}).then(() => {
					const event = {
						field: "qty",
						value:flt(minimum_sales_quantity) ,
						item: { item_code, batch_no, uom }
					}
					 
					 setTimeout(() => {
                       
						me.$cart_items_wrapper.html('');
						me.make_no_items_placeholder();
					 cur_frm.doc.items.forEach(item => {

						cur_pos.cart.update_item_html(item);
					});
					 
					}, 800);
					
			})
			
				 return;

			}
			else if(!cur_frm.doc.is_return && maximum_sales_quantity && maximum_sales_quantity!=0 && flt($('.quantity input').val())> maximum_sales_quantity )
			{
				
				 frappe.show_alert({
				 indicator: 'red',
				 message: "Maximum Sales Quantity is :"+maximum_sales_quantity
			 });
			 me.events.item_selected({ field: 'qty', value:flt(maximum_sales_quantity) , item: { item_code, batch_no, serial_no, uom,rate }}).then(() => {
				const event = {
					field: "qty",
					value:flt(maximum_sales_quantity) ,
					item: { item_code, batch_no, uom }
				}
				 
				 setTimeout(() => {
					me.$cart_items_wrapper.html('');
					me.make_no_items_placeholder();
				 cur_frm.doc.items.forEach(item => {

					cur_pos.cart.update_item_html(item);
				});
				 
				}, 800);
				
		})
			
				 return;
			}
			else{
				me.events.item_selected({ field: 'qty', value:flt($input.val()) , item: { item_code, batch_no, serial_no, uom,rate }}).then(() => {
					const event = {
						field: "qty",
						value:flt($input.val()) ,
						item: { item_code, batch_no, uom }
					}
					 
					 setTimeout(() => {
						me.$cart_items_wrapper.html('');
						me.make_no_items_placeholder();
					 cur_frm.doc.items.forEach(item => {

						cur_pos.cart.update_item_html(item);
					});
					 
					}, 800);
					
			})
			
			}
			
                }
            })
        }
        else{
            console.log("free")
            $('.quantity input').attr('readonly', true);
        }
           
        //     if(bundle_item=='' || bundle_item=='null' || bundle_item=="undefined"  ){
		// 		$('.quantity input').attr('readonly', false);
		// 		if(!cur_frm.doc.is_return && minimum_sales_quantity && minimum_sales_quantity!=0 && flt($('.quantity input').val())<= minimum_sales_quantity )
		// 		{
		// 			 frappe.show_alert({
		// 			 indicator: 'red',
		// 			 message: "Minimum Sales Quantity is :"+minimum_sales_quantity
		// 		 });
			
			
        //      	me.events.item_selected({ field: 'qty', value:flt(minimum_sales_quantity) , item: { item_code, batch_no, serial_no, uom }});
			
		// 		 return;

		// 	}
		// 	else if(!cur_frm.doc.is_return && maximum_sales_quantity && maximum_sales_quantity!=0 && flt($('.quantity input').val())> maximum_sales_quantity )
		// 	{
				
		// 		 frappe.show_alert({
		// 		 indicator: 'red',
		// 		 message: "Maximum Sales Quantity is :"+maximum_sales_quantity
		// 	 });
		// 	 me.events.item_selected({ field: 'qty', value:flt(maximum_sales_quantity) , item: { item_code, batch_no, serial_no, uom }});
			
		// 		 return;
		// 	}
		// 	else{
		// 		me.events.item_selected({ field: 'qty', value:flt($input.val()) , item: { item_code, batch_no, serial_no, uom }});
			
		// 	}
			
				
		// }
		// else{
		// 	$('.quantity input').attr('readonly', true);
		// }
										
		});
		
		this.$cart_items_wrapper.on('click',
			'[data-action="increment"], [data-action="decrement"]', function() {
							
				const $btn = $(this);
				const $item = $btn.closest('.cart-item-wrapper[data-item-code]');
				
				const item_code = unescape($item.attr('data-item-code'));
				const action = $btn.attr('data-action');
				
			let batch_no = unescape($item.attr('data-batch-no'));
			let serial_no = unescape($item.attr('data-serial-no'));
			let uom = unescape($item.attr('data-uom'));
			let rate= unescape($item.attr('data-item-rate'));
			const free_item=unescape($item.attr('data-item-free'));
			
            
            const maximum_sales_quantity=unescape($item.attr('data-maximum-sales-qty'));
            const minimum_sales_quantity=unescape($item.attr('data-minimum-sales-qty')) && unescape($item.attr('data-minimum-sales-qty'))!=0?unescape($item.attr('data-minimum-sales-qty')):1
            
            //const bundle_item=unescape($item.attr('data-bundle-item'));
			var bundle_item=0
			batch_no = batch_no === "undefined" ? undefined : batch_no;
			serial_no = serial_no === "undefined" ? undefined : serial_no;
			uom = uom === "undefined" ? undefined : uom;
			var qtyvalue="+1";
            console.log(free_item,"free_item")
			if(free_item==0){
			frappe.db.get_value("Product Bundle", {"new_item_code":item_code} ,"name", (r)=> {
              
                if(r.name ){
                    bundle_item =1
                    cur_pos.item_selector.bundle_item=bundle_item;
                    if(bundle_item=='' || bundle_item=='null' || bundle_item=="undefined"  ||bundle_item==null  ){
				        if(action === 'increment') {
					//events.on_field_change(item_code, 'qty', '+1');
						
						if(!cur_frm.doc.is_return && maximum_sales_quantity && maximum_sales_quantity!=0 && flt($btn.closest(".cart-item-wrapper").find(".quantity input").val())>= maximum_sales_quantity )
						{
                            me.events.item_selected({ field: 'qty', value: maximum_sales_quantity, item: { item_code, batch_no, serial_no, uom ,rate}});
							 frappe.show_alert({
							 indicator: 'red',
							 message: "Maximum Sales Quantity is :"+maximum_sales_quantity
						 });
							 return;
	 
						}
						else{
						
							qtyvalue="+1";
							me.events.item_selected({ field: 'qty', value: qtyvalue, item: { item_code, batch_no, serial_no, uom,rate}}).then(() => {
                                const event = {
                                    field: "qty",
                                    value:qtyvalue,
                                    item: { item_code, batch_no, uom,rate }
                                }
                                 
                                 setTimeout(() => {
									me.$cart_items_wrapper.html('');
									me.make_no_items_placeholder();
                                 cur_frm.doc.items.forEach(item => {

                                    cur_pos.cart.update_item_html(item);
                                });
                                 
                                }, 800);
                                
                        })
						
						}		
				        } else if(action === 'decrement') {
					
					
					if(minimum_sales_quantity && minimum_sales_quantity!=0 && flt($btn.closest(".cart-item-wrapper").find(".quantity input").val())<= minimum_sales_quantity)
					{
						 frappe.show_alert({
						 indicator: 'red',
						 message: "Minimum Sales Quantity is :"+minimum_sales_quantity
					 });
						 return;
 
					}
					else{
						
						qtyvalue="-1";
						me.events.item_selected_desc({ field: 'qty', value: qtyvalue, item: { item_code, batch_no, serial_no, uom,rate }}).then(() => {
							const event = {
								field: "qty",
								value:qtyvalue,
								item: { item_code, batch_no, uom ,rate}
							}
							 
							 setTimeout(() => {
								me.$cart_items_wrapper.html('');
								me.make_no_items_placeholder();
							 cur_frm.doc.items.forEach(item => {

								cur_pos.cart.update_item_html(item);
							});
							 
							}, 800);
							
					})	

					}
				
					
				}
				
			        }
			        else{
				        $btn.closest(".cart-item-wrapper").find(".quantity input").attr('readonly', true);
			            }
            }else{
                bundle_item=0
                cur_pos.item_selector.bundle_item=bundle_item;
                if(bundle_item=='' || bundle_item=='null' || bundle_item=="undefined"  ||bundle_item==null  ){
                    if(action === 'increment') {
                //events.on_field_change(item_code, 'qty', '+1');
                    
                    if(!cur_frm.doc.is_return && maximum_sales_quantity && maximum_sales_quantity!=0 && flt($btn.closest(".cart-item-wrapper").find(".quantity input").val())>= maximum_sales_quantity )
                    {
                        me.events.item_selected({ field: 'qty', value: maximum_sales_quantity, item: { item_code, batch_no, serial_no, uom,rate }});
                         frappe.show_alert({
                         indicator: 'red',
                         message: "Maximum Sales Quantity is :"+maximum_sales_quantity
                     });
                         return;
 
                    }
                    else{
                    
                        qtyvalue="+1";
                        me.events.item_selected({ field: 'qty', value: qtyvalue, item: { item_code, batch_no, serial_no, uom,rate }}).then(() => {
							const event = {
								field: "qty",
								value:qtyvalue,
								item: { item_code, batch_no, uom }
							}
							 
							 setTimeout(() => {
								me.$cart_items_wrapper.html('');
								me.make_no_items_placeholder();
							 cur_frm.doc.items.forEach(item => {

								cur_pos.cart.update_item_html(item);
							});
							 
							}, 800);
							
					})
                    
                    }		
                    } else if(action === 'decrement') {
                
                        console.log(minimum_sales_quantity,"FFFFFFFFFF")
                if(!cur_frm.doc.is_return && minimum_sales_quantity  && flt($btn.closest(".cart-item-wrapper").find(".quantity input").val())<= minimum_sales_quantity )
                {
                     frappe.show_alert({
                     indicator: 'red',
                     message: "Minimum Sales Quantity is :"+minimum_sales_quantity
                 });
                     return;

                }
                else{
                
                    qtyvalue="-1";
                    me.events.item_selected_desc({ field: 'qty', value: qtyvalue, item: { item_code, batch_no, serial_no, uom ,rate}}).then(() => {
						const event = {
							field: "qty",
							value:qtyvalue,
							item: { item_code, batch_no, uom ,rate}
						}
						
						 setTimeout(() => {
						 me.$cart_items_wrapper.html('');
						 me.make_no_items_placeholder();
						 cur_frm.doc.items.forEach(item => {
							cur_pos.cart.update_item_html(item);
						});
						}, 800);
				})	

                }
            
                
            }
            
                }
                else{
                    $btn.closest(".cart-item-wrapper").find(".quantity input").attr('readonly', true);
                    }

             }})
            }
            else{
                console.log("free")
                $('.quantity input').attr('readonly', true);
            }	
			});


		this.$component.on('click', '.checkout-btn', function() {
		
			if ($(this).attr('style').indexOf('--blue-500') == -1) return;
           //shiby
		 //
		//  frappe.db.get_value('POS Profile',  cur_frm.doc.pos_profile, ["is_event"]).then(({ message }) => {
		// 	this.is_event=message.is_event
		
		
		//   if(message.is_event==1)
		//   {
		// 	if(!cur_pos.cart.location_visitdate_field || cur_pos.cart.location_visitdate_field.value=='')
		// 	{
		// 	 frappe.show_alert({
		// 		 indicator: 'red',
		// 		 message: "Visit date is mandatory"
		// 	 });
		// 	 return;
 
		// 	}
			
		// 	if(this.non_sharable_slot==1)
		// 	{
			 
		// 		if(!cur_pos.cart.location_city_field || !cur_pos.cart.location_branch_field || !cur_pos.cart.location_brand_field && ! cur_pos.cart.location_department_field)
		// 		{
		// 		 frappe.show_alert({
		// 			 indicator: 'red',
		// 			 message: "Enter Location Details"
		// 		 });
		// 		 return;
 
		// 		}
			
			
			 
		// 	}
				 
		// 	if(cur_pos.cart.location_so_field.value=='')
		// 	{
			   
		// 		if(cur_pos.cart.location_event_field || cur_pos.cart.location_event_field.value=='')
		// 		{
		// 			frappe.show_alert({
		// 				indicator: 'red',
		// 				message: "Please select Event or Sales Order to Continue"
		// 			});
		// 			return;
		// 		}

		// 	}
			
		// }

		
			// me.events.checkout();
			// me.toggle_checkout_btn(false);
			// me.allow_discount_change && me.$add_discount_elem.removeClass("d-none");
		
	
           
		// });
		const frm = me.events.get_frm();
        
        if(frm.doc.items.length){
			frm.doc.items.forEach(item => {
				const $item = me.get_cart_item(item);	
                var current_item={}
                current_item.qty = item.qty
                if(item.qty==0)
                {
                    frappe.throw({
				        title: __("Check Quantity"),
				         message: __('Item Code: {0} Quantity is Zero.', [item.item_code])
			        })
                }
                
            })}
			
			me.events.checkout();
			me.toggle_checkout_btn(false);
			me.allow_discount_change && me.$add_discount_elem.removeClass("d-none");
		
	
	
        
	}); 
			//end
			

		this.$totals_section.on('click', '.edit-cart-btn', () => {
			this.events.edit_cart();
			this.toggle_checkout_btn(true);
		});

		this.$component.on('click', '.add-discount-wrapper', () => {
			const can_edit_discount = this.$add_discount_elem.find('.edit-discount-btn').length;

			if(!this.discount_field || can_edit_discount) this.show_discount_control();
		});
		this.sosearch_field.$input.on('input', (e) => {
           
			clearTimeout(this.last_search);
			this.last_search = setTimeout(() => {
				const search_term = e.target.value;
                
				this.get_so_detail(search_term);
			}, 300);
		});
		frappe.ui.form.on("POS Invoice", "paid_amount", frm => {
			// called when discount is applied
			this.update_totals_section(frm);
		});
        
	}
	//added by shiby
	 
	async get_so_detail() {
        var me=this;
		//frappe.dom.freeze();
		const frm = this.events.get_frm();
		const search_term = this.sosearch_field.get_value();	
       
		const  res = await frappe.db.get_value("Sales Order",{'name': search_term,'pos_status':'Open'}  , "customer");
        
        if(res.message.customer){
            
            const  res1 = await frappe.db.get_value("Sales Order",{'name': search_term,'pos_status':'Open'}  , "delivery_date");
			
			if(String(res1.message.delivery_date)==String(frappe.datetime.nowdate()))
			{
               
				frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'customer', res.message.customer);					
				this.location_info = {};		
				this.load_invoice();
				frappe.db.get_value('Sales Order', {'name': search_term,'pos_status':'Open'}, ["delivery_date", "customer","brand","city","branch","department"]).then(({ message }) => {
							
								this.location_info = { ...message };
								this.location_info["visitdate"] = message.delivery_date;
								this.location_info["so"] = search_term;
								
								this.location_info["brand"] = message.brand;
								this.location_info["city"] = message.city;
								this.location_info["branch"] = message.branch;
								this.location_info["department"] = message.department;
								if(cur_pos.cart.location_so_field)
								{
								
									cur_pos.cart.location_so_field.set_value(search_term)
									cur_pos.cart.location_visitdate_field.set_value(message.delivery_date)
								}
								
								
							
						});
				this.render_location_fields();
		
			}
			else{
				frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'customer', '');	
				
				this.get_positems('')				
				this.location_info = {};		
				this.load_invoice();	
				cur_pos.cart.location_so_field.set_value('')
				cur_pos.cart.location_visitdate_field.set_value('')	

				// frappe.show_alert({
				// 	indicator: 'red',
				// 	message: __('Visit date not matched')
				// });
	
			}

        }
        else{
           
           var  pos_details=[];
            frappe.call({
                method: 'vim.custom_script.point_of_sale.point_of_sale.get_pos_from_rfid',
                args: {
                    rfid: search_term?search_term:''
                },
                async: false,
                callback: function(r) {
                    
                    if (r && r.message){                        
                        pos_details = r.message;
                        var sales_order="",pos_invoice="",customer="";var creation=""; 
                        pos_details.forEach(function (c, index) {
                            sales_order=c.sales_order
                            pos_invoice=c.pos_invoice
                            customer=c.customer
                            creation=c.creation
                        })
                        
                                             
                        var postime=new Date(creation)                     
                        postime.setHours(postime.getHours() + 24) 
                        
                    //    if(new Date(postime).toLocaleString()>=new Date().toLocaleString()){
                      
                        if(new Date(postime).getTime() >= new Date().getTime()){
                            frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'customer', customer);  
                            me.location_info = {};		
                            me.load_invoice();
                            frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'customer_pos', pos_invoice);  
                            frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'customer_so', sales_order);  
                       }
                       else{
                        frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'customer', '');  
                        me.location_info = {};		
                        me.load_invoice();
                        frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'customer_pos', undefined);  
                        frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'customer_so', undefined);  
                        // frappe.show_alert({
                        //     indicator: 'red',
                        //     message: "RFID not found..........."
                        // });

                       }

                       
                    }
                }
            });
            
            
            
        }
       
			
		
		
		
	}
	set_selected_item($item) {
		this.selected_item = $item;
		this.$cart_items_wrapper.find('.list-item').removeClass('current-item qty disc rate');
		this.selected_item.addClass('current-item');
		
	}
	attach_shortcuts() {
		for (let row of this.number_pad.keys) {
			for (let btn of row) {
				if (typeof btn !== 'string') continue; // do not make shortcuts for numbers

				let shortcut_key = `ctrl+${frappe.scrub(String(btn))[0]}`;
				if (btn === 'Delete') shortcut_key = 'ctrl+backspace';
				if (btn === 'Remove') shortcut_key = 'shift+ctrl+backspace'
				if (btn === '.') shortcut_key = 'ctrl+>';

				// to account for fieldname map
				const fieldname = this.number_pad.fieldnames[btn] ? this.number_pad.fieldnames[btn] :
					typeof btn === 'string' ? frappe.scrub(btn) : btn;

				let shortcut_label = shortcut_key.split('+').map(frappe.utils.to_title_case).join('+');
				shortcut_label = frappe.utils.is_mac() ? shortcut_label.replace('Ctrl', '⌘') : shortcut_label;
				this.$numpad_section.find(`.numpad-btn[data-button-value="${fieldname}"]`).attr("title", shortcut_label);

				frappe.ui.keys.on(`${shortcut_key}`, () => {
					const cart_is_visible = this.$component.is(":visible");
					if (cart_is_visible && this.item_is_selected && this.$numpad_section.is(":visible")) {
						this.$numpad_section.find(`.numpad-btn[data-button-value="${fieldname}"]`).click();
					}
				})
			}
		}
		const ctrl_label = frappe.utils.is_mac() ? '⌘' : 'Ctrl';
		this.$component.find(".checkout-btn").attr("title", `${ctrl_label}+Enter`);
		frappe.ui.keys.add_shortcut({
			shortcut: "ctrl+enter",
			action: () => this.$component.find(".checkout-btn").click(),
			condition: () => this.$component.is(":visible") && !this.$totals_section.find('.edit-cart-btn').is(':visible'),
			description: __("Checkout Order / Submit Order / New Order"),
			ignore_inputs: true,
			page: cur_page.page.page
		});
		this.$component.find(".edit-cart-btn").attr("title", `${ctrl_label}+E`);
		frappe.ui.keys.on("ctrl+e", () => {
			const item_cart_visible = this.$component.is(":visible");
			const checkout_btn_invisible = !this.$totals_section.find('.checkout-btn').is('visible');
			if (item_cart_visible && checkout_btn_invisible) {
				this.$component.find(".edit-cart-btn").click();
			}
		});
		this.$component.find(".add-discount-wrapper").attr("title", `${ctrl_label}+D`);
		frappe.ui.keys.add_shortcut({
			shortcut: "ctrl+d",
			action: () => this.$component.find(".add-discount-wrapper").click(),
			condition: () => this.$add_discount_elem.is(":visible"),
			description: __("Add Order Discount"),
			ignore_inputs: true,
			page: cur_page.page.page
		});
		frappe.ui.keys.on("escape", () => {
			const item_cart_visible = this.$component.is(":visible");
			if (item_cart_visible && this.discount_field && this.discount_field.parent.is(":visible")) {
				this.discount_field.set_value(0);
			}
		});
	}

	toggle_item_highlight(item) {
		const $cart_item = $(item);
		const item_is_highlighted = $cart_item.attr("style") == "background-color:var(--gray-50);";

		if (!item || item_is_highlighted) {
			this.item_is_selected = false;
			this.$cart_container.find('.cart-item-wrapper').css("background-color", "");
		} else {
			$cart_item.css("background-color", "var(--gray-50)");
			this.item_is_selected = true;
			this.$cart_container.find('.cart-item-wrapper').not(item).css("background-color", "");
		}
	}

	make_customer_selector() {
		this.$customer_section.html(`
			<div class="customer-field"></div>
		`);
		const me = this;
		// const query = { query: 'erpnext.controllers.queries.customer_query' }; 
		const query = { query: 'vim.custom_script.customer.customer.customer_query' }; 
		const allowed_customer_group = this.allowed_customer_groups || [];
		if (allowed_customer_group.length) {
			query.filters = {
				customer_group: ['in', allowed_customer_group]
			}
		}
		this.customer_field = frappe.ui.form.make_control({
			df: {
				label: __('Customer'),
				fieldtype: 'Link',
				options: 'Customer',
				placeholder: __('Search by customer name, phone, email.'),
				get_query: () => query,
				onchange: function() {
					if (this.value) {
						
						//uncomment ,if SO Select
						cur_frm.set_value('customer_pos', undefined);  
                        cur_frm.set_value('customer_so', undefined);  
						me.get_positems('');
						const frm = me.events.get_frm();
						frappe.dom.freeze();
						frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'customer', this.value);
						frm.script_manager.trigger('customer', frm.doc.doctype, frm.doc.name).then(() => {
							frappe.run_serially([
								() => me.fetch_customer_details(this.value),
								() => me.events.customer_details_updated(me.customer_info),
								() => me.update_customer_section(),
								() => me.update_totals_section(),
								() => frappe.dom.unfreeze(),
                                //uncomment ,if SO Select
                                () => me.render_location_fields(),
                                () => me.fetch_location_details(),
								
							]);
                            $('.search-item-group').find('.dropdown-menu').find("a:first").trigger("click");
						})
						
								   
					}
                    //Added by Shiby
                    	var customer=this.value
                        
                        // cur_pos.cart.custom_field.set_value('');
						// cur_pos.cart.event_field.set_value('');
						// cur_pos.cart.slot_field.set_value('');
						// cur_pos.cart.visit_date.set_value('');
								
                                // cur_pos.cart.location_so_field.get_query= function() {
								// 	return {
								// 	 filters: [
								// 	  ["Sales Order","customer", "=", customer?customer:''],
								// 	  ["Sales Order","docstatus", "=", 1],
								// 	  ["Sales Order","status", "!=", 'Closed']
								// 	 ]
								 
								// 	}
								 
								//    }
                                   //end
				},
			},
			parent: this.$customer_section.find('.customer-field'),
			render_input: true,
		});
		this.customer_field.toggle_label(false);
	}
//start Added by Shiby

	update_customer_branch(customer){
		frappe.call({
			async:false,
			method: "vim.custom_script.point_of_sale.point_of_sale.update_customer_branch",
			args: {
				'customer': customer,
				'pos_profile':cur_frm.doc.pos_profile
			}
		});

	}
	getslotDetails(select_event,delivery_date){
        var resultlist=[];var slotlist=[];
		frappe.call({
				"method": "vim.custom_script.point_of_sale.point_of_sale.get_slot_list",
				async: true,
				args:{item_name:select_event?select_event:'',is_new:0,delivery_date:delivery_date?delivery_date:''},
				callback: function (r) {
									
					
					resultlist = (r.message['result_list'] || []);
					
					Object.entries(resultlist).forEach(([key, value]) => {
						var item = "";
						item=(value["slot_name"]);
						slotlist.push(item);
					});
                    
					//$(`.slot-field`).set_df_property()
					return slotlist;
				}})
	}
	// getbranchDetails(brand){
    //     var resultlist=[];var slotlist=[];
	// 	frappe.call({
	// 		"method": "vim.custom_script.point_of_sale.point_of_sale.get_branch_list",
	// 		async: true,
	// 		args:{brand:brand?brand:''},
	// 		callback: function (r) {
				
	// 			resultlist = (r.message['branch_list'] || []);
	// 			return resultlist;
	// 		}
	// 	})
	// }
	//end
	fetch_customer_details(customer) {
		if (customer) {
			return new Promise((resolve) => {
				frappe.db.get_value('Customer', customer, ["email_id", "mobile_no", "image", "loyalty_program"]).then(({ message }) => {
					const { loyalty_program } = message;
					// if loyalty program then fetch loyalty points too
					if (loyalty_program) {
						frappe.call({
							method: "erpnext.accounts.doctype.loyalty_program.loyalty_program.get_loyalty_program_details_with_points",
							args: { customer, loyalty_program, "silent": true },
							callback: (r) => {
								const { loyalty_points, conversion_factor } = r.message;
								if (!r.exc) {
									this.customer_info = { ...message, customer, loyalty_points, conversion_factor };
									resolve();
								}
							}
						});
					} else {
						this.customer_info = { ...message, customer };
						resolve();
					}
				});
			});
		} else {
			return new Promise((resolve) => {
				this.customer_info = {}
				resolve();
			});
		}
	}
	fetch_location_details(pos_invoice) {
		var item_list_data=[];
        if(cur_pos.cart.location_info && cur_pos.cart.location_info["so"]!=undefined)
        {
            
            this.get_positems('')
			
				if(cur_pos.cart.location_info["so"])
				{
					frappe.call({
						method: "vim.custom_script.point_of_sale.point_of_sale.get_payment_entry",
						args: {
							sorder: cur_pos.cart.location_info["so"]
						},
						async: false,
						callback: function(r) {
							item_list_data = (r.message['result_list'] || []); 
							
							var allocated_amount = 0;
							Object.entries(item_list_data).forEach(([key, value]) => {
								
								allocated_amount=flt(value["allocated_amount"])
							});
							var child = cur_frm.add_child("advances");
							frappe.model.set_value(child.doctype, child.name, "allocated_amount", allocated_amount)
							cur_frm.refresh_field("advances")
						}
					});
				}
			
        }
       
		if (pos_invoice) {
			return new Promise((resolve) => {
				frappe.db.get_value('POS Invoice', pos_invoice, ["visit_date", "sales_order","event", "slot","brand","city","branch","department"]).then(({ message }) => {
					
						this.location_info = { ...message };
						this.location_info["visitdate"] = message.visit_date;
						this.location_info["so"] = message.sales_order;
						this.location_info["event"] = message.event;
						this.location_info["event_slot"] = message.slot;
						this.location_info["brand"] = message.brand;
						this.location_info["city"] = message.city;
						this.location_info["branch"] = message.branch;
						this.location_info["department"] = message.department;
						if(cur_pos.cart.location_so_field)
						{
						
							cur_pos.cart.location_so_field.set_value(message.sales_order)
							cur_pos.cart.location_visitdate_field.set_value(message.visit_date)
						}
						
						resolve();
					
				});
			});
			
		
		} else {
			return new Promise((resolve) => {
				this.location_info = {}
				resolve();
			});
		}
		
	}
	show_discount_control() {
		this.$add_discount_elem.css({ 'padding': '0px', 'border': 'none' });
		this.$add_discount_elem.html(
			`<div style="display:flex">
			<div class="add-discount-remark-field">
			<input type="text" id="discremark" name="disremark" placeholder="Add Discount Remarks" style="border: none;
			border-radius: var(--border-radius);
			font-size: var(--text-md);
			height: 26px;"><br><br></div>
			<div class="add-discount-field"></div>
           </div>`
		);

		const me = this;
			this.$component.on('change', '#discremark', function () {
			
				me.disremark=$('#discremark').val();
			
		});
		this.discount_field = frappe.ui.form.make_control({
			df: {
				label: __('Discount'),
				fieldtype: 'Data',
				placeholder: __('Enter discount percentage.'),
				input_class: 'input-xs',
				onchange: function() {
				
					const frm = me.events.get_frm();
					if(frm.doc.is_approved==0) 
					{
						if (flt(this.value) != 0 ) {
							frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'additional_discount_percentage', flt(this.value));
							frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'discount_remark',String(me.disremark));
						   
							 me.hide_discount_control(this.value,me.disremark);  
						} else {
							
							frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'additional_discount_percentage', 0);
							frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'discount_remark', '');
							me.$add_discount_elem.css({
								'border': '1px dashed var(--gray-500)',
								'padding': 'var(--padding-sm) var(--padding-md)'
							});
							me.$add_discount_elem.html(`${me.get_discount_icon()} Add Discount`);
							me.discount_field = undefined;
						}
					}
					else{
						me.hide_discount_control(frm.doc.additional_discount_percentage,me.disremark); 
						
					}
					
				},
			},
			parent: this.$add_discount_elem.find('.add-discount-field'),
			render_input: true,
		});
        
		this.discount_field.toggle_label(false);
		this.discount_field.set_focus();
		
	}
    update_discount(remarks,discount)
    {
        
		if(discount>0)
		{
			const frm = this.events.get_frm();
			frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'discount_remark',remarks);
			frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'additional_discount_percentage',discount);
            
			frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'is_approved',1);
			this.disremark=remarks
			this.discount_field=flt(discount);       
			this.update_totals_section();
			this.$cart_container.find('.checkout-btn').css({
				'display': 'flex'})
				this.$cart_container.find('.checkout-btn').css({
					'background-color': 'var(--blue-500)'
				});
			this.$cart_container.find('.save-as-draft-btn').css({
				'display': 'none'})
		}
        
                       
    }
    update_discount_so(disc_perc,discount)
    {
        
		if(disc_perc>0)
		{
			const frm = this.events.get_frm();
			frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'additional_discount_percentage',disc_perc);
			frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'is_approved',1);
			this.discount_field=flt(discount);       
			this.update_totals_section();
			this.$cart_container.find('.checkout-btn').css({
				'display': 'flex'})
				this.$cart_container.find('.checkout-btn').css({
					'background-color': 'var(--blue-500)'
				});
			this.$cart_container.find('.save-as-draft-btn').css({
				'display': 'none'})
		}
        else if (discount>0){
            const frm = this.events.get_frm();
			frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'additional_discount_percentage',0);
            frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'discount_amount',discount);
			frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'is_approved',1);
			this.discount_field=flt(discount);       
			
            const currency = this.events.get_frm().doc.currency;
            this.$add_discount_elem.html(
                `<div class="edit-discount-btn" display: flex; style="color:white !important" >
                    ${this.get_discount_icon()}Discount&nbsp;${String(0).bold()}&nbsp;% &nbsp; ${String('')}
                </div>
                <div class="discount-amount"> 
                ${format_currency(String(discount), currency,2)}
                </div>`
            );
            this.update_totals_section();
			this.$cart_container.find('.checkout-btn').css({
				'display': 'flex'})
				this.$cart_container.find('.checkout-btn').css({
					'background-color': 'var(--blue-500)'
				});
			this.$cart_container.find('.save-as-draft-btn').css({
				'display': 'none'})
        }
       
        
                       
    }
//add and commented by shiby
	hide_discount_control(discount,remark) {
	if (!discount) {
        
			this.$add_discount_elem.css({ 'padding': '0px', 'border': 'none' });
			this.$add_discount_elem.html(
				`<div class="add-discount-field"></div>`
			);
         this.toggle_checkout_btn(true);
         this.$cart_container.find('.save-as-draft-btn').css({
         'display': 'none'})
        
	} else {
	
		this.$add_discount_elem.css({
			'border': '1px dashed var(--white)',
            'color':'white'
            
		});
		const frm = this.events.get_frm();
		const currency = this.events.get_frm().doc.currency;
		var remarks=''
		
		this.$add_discount_elem.html(
			`<div class="edit-discount-btn" style="color:white !important" >
				${this.get_discount_icon()}Discount&nbsp;${String(discount).bold()}&nbsp;% &nbsp; ${String(this.disremark)}
			</div>
			<div class="discount-amount"> 
			${format_currency(String(frm.doc.base_total*discount/100), currency,2)}
			</div>`
		);
		if(discount>0)
        {
            
            frappe.db.get_value('POS Profile',  cur_frm.doc.pos_profile, ["discount_approval_required"]).then(({ message }) => {
                this.discount_approval_required=message.discount_approval_required;
                
                if(message.discount_approval_required && message.discount_approval_required==1 && cur_frm.doc.is_approved==0)
                {
                    frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'discount_approval_required', 1);
                  
                        this.$cart_container.find('.checkout-btn').css({
                            'background-color': 'var(--blue-200)',
                            'display':'none'
                        });
                        this.$cart_container.find('.save-as-draft-btn').css({'background-color': 'var(--blue-500)',
                            'display': 'flex',
                            'color': '#fff',
                            'align-items': 'center',
                            'justify-content': 'center',
                            'padding': 'var(--padding-sm)',
                            'margin-top': 'var(--margin-sm)',
                            'border-radius': 'var(--border-radius-md)',
                            'font-size': 'var(--text-lg)',
                            'font-weight': '700',
                        
                            'cursor': 'pointer'})
                           // this.create_discount_popup();
                    
                }
    
            });
        }
        
        frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'discount_approval_required', 0);
       
      
	}
   

	}
   
	// hide_discount_control(discount) {
	// 	if (!discount) {
	// 		this.$add_discount_elem.css({ 'padding': '0px', 'border': 'none' });
	// 		this.$add_discount_elem.html(
	// 			`<div class="add-discount-field"></div>`
	// 		);
	// 	} else {
	// 		this.$add_discount_elem.css({
	// 			'border': '1px dashed var(--dark-green-500)',
	// 			'padding': 'var(--padding-sm) var(--padding-md)'
	// 		});
	// 		this.$add_discount_elem.html(
	// 			`<div class="edit-discount-btn">
	// 				${this.get_discount_icon()} Additional&nbsp;${String(discount).bold()}% discount applied
	// 			</div>`
	// 		);
	// 	}
	// }

	update_customer_section() {
		const me = this;
		const { customer, email_id='', mobile_no='', image } = this.customer_info || {}; 

		if (customer) {
			this.$customer_section.html(
				`<div class="customer-details">
					<div class="customer-display">
						${this.get_customer_image()}
						<div class="customer-name-desc">
							<div class="customer-name">${customer}</div>
							${get_customer_description()}
						</div>
						<div class="reset-customer-btn" data-customer="${escape(customer)}">
							<svg width="32" height="32" viewBox="0 0 14 14" fill="none">
								<path d="M4.93764 4.93759L7.00003 6.99998M9.06243 9.06238L7.00003 6.99998M7.00003 6.99998L4.93764 9.06238L9.06243 4.93759" stroke="#8D99A6"/>
							</svg>
						</div>
					</div>
				</div>`
			);
			
		} else {
			// reset customer selector
			this.reset_customer_selector();
		}

		function get_customer_description() {
			if (!email_id && !mobile_no) {
				return `<div class="customer-desc">Click to add email / phone</div>`;
			} else if (email_id && !mobile_no) {
				return `<div class="customer-desc">${email_id}</div>`;
			} else if (mobile_no && !email_id) {
				
				return `<div class="customer-desc">${mobile_no}</div>`;
			} else {
				return `<div class="customer-desc">${email_id} - ${mobile_no}</div>`;
			}
		}

	}
	
	get_customer_image() {
		const { customer, image } = this.customer_info || {};
		if (image) {
			return `<div class="customer-image"><img src="${image}" alt="${image}""></div>`;
		} else {
			return `<div class="customer-image customer-abbr">${frappe.get_abbr(customer)}</div>`;
		}
	}

	update_totals_section(frm) {
		
	
		if (!frm) frm = this.events.get_frm();
       
		this.render_discount()
		this.render_net_total(frm.doc.net_total);
		const grand_total = cint(frappe.sys_defaults.disable_rounded_total) ? frm.doc.grand_total : frm.doc.rounded_total;
		
		this.render_grand_total(grand_total);

		const taxes = frm.doc.taxes.map(t => {
			return {
				description: t.description, rate: t.rate
			};
		});
		this.render_taxes(frm.doc.total_taxes_and_charges, taxes);
       
		
	}
    
	update_totals_section_after_approval(frm) {
		
		
		if (!frm) frm = this.events.get_frm();
		
		this.render_net_total(frm.doc.net_total);
		const grand_total = cint(frappe.sys_defaults.disable_rounded_total) ? frm.doc.grand_total : frm.doc.rounded_total;
		
		this.render_grand_total(grand_total);

		const taxes = frm.doc.taxes.map(t => {
			return {
				description: t.description, rate: t.rate
			};
		});
		this.render_taxes(frm.doc.total_taxes_and_charges, taxes);
		
	}
	render_net_total(value) {

		const currency = this.events.get_frm().doc.currency;
		this.$totals_section.find('.net-total-container').html(
			`<div>Net Total</div><div>${format_currency(value, currency,2)}</div>`
		)

		this.$numpad_section.find('.numpad-net-total').html(
			`<div>Net Total: <span>${format_currency(value, currency,2)}</span></div>`
		);
	}

	render_grand_total(value) {
		const currency = this.events.get_frm().doc.currency;
		this.$totals_section.find('.grand-total-container').html(
			`<div>Grand Total</div><div>${format_currency(value, currency,2)}</div>`
		)

		this.$numpad_section.find('.numpad-grand-total').html(
			`<div>Grand Total: <span>${format_currency(value, currency,2)}</span></div>`
		);
	}
	render_discount(){
	
		if(this.discount_field)
		{
			//this.discount_field.set_value(flt(cur_frm.doc.additional_discount_percentage));
			this.disremark=cur_frm.doc.discount_remark
			this.hide_discount_control(cur_frm.doc.additional_discount_percentage,cur_frm.doc.discount_remark);
            
		
		}
		else{
			this.show_discount_control()
			this.discount_field.set_value(flt(cur_frm.doc.additional_discount_percentage));
			this.disremark=cur_frm.doc.discount_remark
			this.hide_discount_control(cur_frm.doc.additional_discount_percentage,cur_frm.doc.discount_remark);
		
		}
		
		// if(cur_pos.cart.discount_field)
		// { 
		// 	console.log(cur_pos.cart.discount_field,"1")			       
        //     this.discount_field=cur_frm.doc.additional_discount_percentage;        
		// 	this.hide_discount_control(this.discount_field,'');
		// }
		// else
		// {
		// 	this.hide_discount_control(0,'');  
			
		// }
		
		// frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'additional_discount_percentage', flt(10));
		// console.log("renderdisc")
		// const frm = this.events.get_frm();
		// const currency=this.events.get_frm().doc.currency;
		// this.$totals_section.find('.add-discount-field').html(
		// 	`<div class="edit-discount-btn" >
		// 		${this.get_discount_icon()}Discount&nbsp;${String(5).bold()}&nbsp;%
		// 	</div>
		// 	<div class="discount-amount"> 
		// 	${format_currency(String(frm.doc.grand_total*10/100), currency)}
		// 	</div>`
		
		//);

	}
	render_taxes(value, taxes) {
		if (taxes.length) {
			const currency = this.events.get_frm().doc.currency;
			const taxes_html = taxes.map(t => {
				const description = /[0-9]+/.test(t.description) ? t.description : `${t.description} @ ${t.rate}%`;
				return `<div class="tax-row">
					<div class="tax-label">${description}</div>
					<div class="tax-value">${format_currency(value, currency,2)}</div>
				</div>`;
			}).join('');
			this.$totals_section.find('.taxes-container').css('display', 'flex').html(taxes_html);
		} else {
			this.$totals_section.find('.taxes-container').css('display', 'none').html('');
		}
	}

	get_cart_item({ name }) {
		// const batch_attr = `[data-batch-no="${escape(batch_no)}"]`;
		// const item_code_attr = `[data-item-code="${escape(item_code)}"]`;
		// const uom_attr = `[data-uom="${escape(uom)}"]`;
        
		// const item_selector = batch_no ?
		// 	`.cart-item-wrapper${batch_attr}${uom_attr}` : `.cart-item-wrapper${item_code_attr}${uom_attr}`;

		// return this.$cart_items_wrapper.find(item_selector);
        const item_selector = `.cart-item-wrapper[data-row-name="${escape(name)}"]`;
        console.log(item_selector,"item_selector")
		return this.$cart_items_wrapper.find(item_selector);
	}
    get_free_item(item) {
        console.log(item,"FFFFFFFFFFFF")
        const doc = this.events.get_frm().doc;
        
        var item_row=doc.items.find(i => i.name == item.name && i.uom == item.uom && i.rate == item.rate);
        console.log(item_row,"FFFFFFFFFFFF")
		return doc.items.find(i => i.parent_item_row == item_row.parent_item_row && i.is_free_item == 1);
	}
    get_item_from_frm(item) {
		const doc = this.events.get_frm().doc;
        
		return doc.items.find(i => i.name == item.name && i.uom == item.uom && i.rate == item.rate);
	}
	update_item_html(item, remove_item) {
       
		const $item = this.get_cart_item(item);	
		if (remove_item) {
            $item && $item.next().remove() && $item.remove(); 
            const no_items = this.$cart_items_wrapper.find('.cart-item-wrapper').length;
            setTimeout(() => {
                this.$cart_items_wrapper.html('');
                this.make_no_items_placeholder();
             cur_frm.doc.items.forEach(item => {

                cur_pos.cart.update_item_html(item);
            });
             
            }, 800);
            console.log(no_items,"no_items")
            // const frm = this.events.get_frm();
            // this.update_totals_section(frm);
		} else {
            const item_row = this.get_item_from_frm(item);
           
            this.render_cart_item(item_row, $item);
			// const { item_code, batch_no, uom } = item;
			// const search_field = batch_no ? 'batch_no' : 'item_code';
			// const search_value = batch_no || item_code;
			// const item_rowp = this.events.get_frm().doc.items.find(i => i[search_field] === search_value && i.uom === uom );
			
			// this.render_cart_item(item_rowp, $item)
		}

		const no_of_cart_items = this.$cart_items_wrapper.find('.cart-item-wrapper').length;
		this.highlight_checkout_btn(no_of_cart_items > 0);
        console.log(no_of_cart_items,"no_of_cart_items",remove_item)
		this.update_empty_cart_section(no_of_cart_items);
        
		
	}
   
	update_item_html_uom(item, removnuom,convfactore_item) {
		
		const $item = this.get_cart_item(item);	
		
			const { item_code, batch_no, uom,slot_name } = item;
			const search_field = batch_no ? 'batch_no' : 'item_code';
			const search_value = batch_no || item_code;
			const item_rowp = this.events.get_frm().doc.items.find(i => i[search_field] === search_value && i.uom === uom);
			
			this.render_cart_item(item_rowp, $item);
			
		

		const no_of_cart_items = this.$cart_items_wrapper.find('.cart-item-wrapper').length;
		this.highlight_checkout_btn(no_of_cart_items > 0);

		this.update_empty_cart_section(no_of_cart_items);
	}
	render_cart_item(item_data, $item_to_update) {
       
		
		const currency = this.events.get_frm().doc.currency;
		const me = this;
        
		if (!$item_to_update.length) {
           
			this.$cart_items_wrapper.append(
				`<div class="cart-item-wrapper"
                        data-row-name="${escape(item_data.name)}"
						data-item-code="${escape(item_data.item_code)}" data-uom="${escape(item_data.uom)}"
						data-batch-no="${escape(item_data.batch_no || '')}"
                        data-minimum-sales-qty="${escape(cur_pos.item_selector.minimum_sales_quantity)}"
                        data-maximum-sales-qty="${escape(cur_pos.item_selector.maximum_sales_quantity)}"
                        data-bundle-item="${escape(cur_pos.item_selector.bundle_item)}"
						data-item-rate="${escape(item_data.rate)}"
                        data-item-free="${escape(item_data.is_free_item)}">
				</div>
				<div class="seperator"></div>`
			)
            // this.$cart_items_wrapper.append(
			// 	`<div class="cart-item-wrapper" data-row-name="${escape(item_data.name)}"></div>
			// 	<div class="seperator"></div>`
			// )
			$item_to_update = this.get_cart_item(item_data);
		}
        
        if(cur_pos.cart.location_so_field.value){
            //console.log(cur_pos.cart.location_so_field.value,"console.log(cur_pos.cart.location_so_field)")
            //setTimeout(() => {
                $item_to_update.html(
                    `${get_item_image_html()}
                    <div class="item-name-desc">
                        <div class="item-name">
                            ${item_data.item_name}
                        </div>
                        ${get_description_html()}
                    </div>
                    ${get_rate_discount_html()}`
                )
                $('.btn-xs').css('line-height','1.8')
                $('.item-qty').css('width','110px')
            // }, 800);

        }
        else{
            
            setTimeout(() => {
                $item_to_update.html(
                    `${get_item_image_html()}
                    <div class="item-name-desc">
                        <div class="item-name">
                            ${item_data.item_name}
                        </div>
                        ${get_description_html()}
                    </div>
                    ${get_rate_discount_html()}`
                )
                $('.btn-xs').css('line-height','1.8')
                $('.item-qty').css('width','110px')
             }, 500);
        }
		
		
		//added by tushar
            // this.check_minimum_sales_qty=false;
			// if(!this.custom_change_call)
            //  { 
			// 	 var s = $('.cart-item-wrapper .item-amount').text();
			// 	var k = s.split(" ")
				
			// 	console.log(item_data,frappe.model.get_value(item_data.doctype, item_data.name,'rate'),"get_value")
			// 	if (k.length>1 && flt(k[k.length-1] )==flt(item_data.rate) )
			// 	{	
			// 		if(	this.old_val_set<10){
			// 			this.old_val_set += 1;
			// 		}
			// 		else
			// 		this.custom_change_call = true; 
			// 		}
            //     $('.cart-item-wrapper .quantity input').change();
			// }
            //     this.check_minimum_sales_qty=true;
        ///////////////////////////////
		
		
		set_dynamic_rate_header_width();
		this.scroll_to_item($item_to_update);

		function set_dynamic_rate_header_width() {
			const rate_cols = Array.from(me.$cart_items_wrapper.find(".item-rate-amount"));
			me.$cart_header.find(".rate-amount-header").css("width", "");
			me.$cart_items_wrapper.find(".item-rate-amount").css("width", "");
			let max_width = rate_cols.reduce((max_width, elm) => {
				if ($(elm).width() > max_width)
					max_width = $(elm).width();
				return max_width;
			}, 0);

			max_width += 1;
			if (max_width == 1) max_width = "";

			me.$cart_header.find(".rate-amount-header").css("width", max_width);
			me.$cart_items_wrapper.find(".item-rate-amount").css("width", max_width);
		}
					
		// function get_rate_discount_html() {
		// 	if (item_data.rate && item_data.amount && item_data.rate !== item_data.amount) {
		// 		return `
		// 			<div class="item-qty-rate">
		// 				<div class="item-qty"><span>${item_data.qty || 0}</span></div>
		// 				<div class="item-rate-amount">
		// 					<div class="item-rate">${format_currency(item_data.amount, currency)}</div>
		// 					<div class="item-amount">${format_currency(item_data.rate, currency)}</div>
		// 				</div>
		// 			</div>`
		// 	} else {
		// 		return `
		// 			<div class="item-qty-rate">
		// 				<div class="item-qty"><span>${item_data.qty || 0}</span></div>
		// 				<div class="item-rate-amount">
		// 					<div class="item-rate">${format_currency(item_data.rate, currency)}</div>
		// 				</div>
		// 			</div>`
		// 	}
		// }
		//Comment and updated by shiby 
		function get_rate_discount_html() {
            let _item = Object.assign({}, item_data)
			
			if (item_data.rate && item_data.amount && item_data.rate !== item_data.amount) {
				
				return `
					<div class="item-qty-rate">
						<div class="item-qty">
						<div class="quantity list-item__content text-right">
						<div class="input-group input-group-xs">
					<span class="input-group-btn">
						<button class="btn-default btn-xs" data-action="increment">+</button>
					</span>

					<input class="form-control" type="number" value="${item_data.qty || 0}" style="padding: unset;text-align:right">

					<span class="input-group-btn">
						<button class="btn-default btn-xs" data-action="decrement">-</button>
					</span>
				</div>
						</div>
						</div>
						<div class="item-rate-amount">
							<div class="item-rate">${format_currency(item_data.amount, currency,2)}</div>
							<div class="item-amount">${format_currency(item_data.rate, currency,2)}</div>
						</div>
					</div>`
			} else {
				return `
					<div class="item-qty-rate">
						<div class="item-qty">
						<div class="quantity list-item__content text-right">
						<div class="input-group input-group-xs">
					<span class="input-group-btn">
						<button class="btn-default btn-xs" data-action="increment">+</button>
					</span>

					<input class="form-control" type="number" value="${item_data.qty || 0}" style="text-align:right;padding: unset;">

					<span class="input-group-btn">
						<button class="btn-default btn-xs" data-action="decrement">-</button>
					</span>
				</div>
						</div>
						</div>
						<div class="item-rate-amount">
							<div class="item-rate">${format_currency(item_data.rate, currency,2)}</div>
						</div>
					</div>`
			}

		}

		function get_description_html() {
			if (item_data.description) {
				if (item_data.description.indexOf('<div>') != -1) {
					try {
						item_data.description = $(item_data.description).text();
					} catch (error) {
						item_data.description = item_data.description.replace(/<div>/g, ' ').replace(/<\/div>/g, ' ').replace(/ +/g, ' ');
					}
				}
				item_data.description = frappe.ellipsis(item_data.description, 45);
				return `<div class="item-desc">${item_data.description}</div>`;
			}
			return ``;
		}

		function get_item_image_html() {
			const { image, item_name } = item_data;
			if (image) {
				return `<div class="item-image"><img src="${image}" alt="${image}""></div>`;
			} else {
				return `<div class="item-image item-abbr">${frappe.get_abbr(item_name)}</div>`;
			}
		}
		
	
	}

	scroll_to_item($item) {
		if ($item.length === 0) return;
		const scrollTop = $item.offset().top - this.$cart_items_wrapper.offset().top + this.$cart_items_wrapper.scrollTop();
		this.$cart_items_wrapper.animate({ scrollTop });
	}

	update_selector_value_in_cart_item(selector, value, item) {
		const $item_to_update = this.get_cart_item(item);
		$item_to_update.attr(`data-${selector}`, escape(value));
	}

	toggle_checkout_btn(show_checkout) {
		if (show_checkout) {
			this.$totals_section.find('.checkout-btn').css('display', 'flex');
			this.$totals_section.find('.edit-cart-btn').css('display', 'none');
		} else {
			this.$totals_section.find('.checkout-btn').css('display', 'none');
			this.$totals_section.find('.edit-cart-btn').css('display', 'flex');
		}
	}

	highlight_checkout_btn(toggle) {
		if (toggle) {
			this.$add_discount_elem.css('display', 'flex');
			this.$cart_container.find('.checkout-btn').css({
				'background-color': 'var(--blue-500)'
			});
		} else {
			this.$add_discount_elem.css('display', 'none');
			this.$cart_container.find('.checkout-btn').css({
				'background-color': 'var(--blue-200)'
			});
		}
	}

	update_empty_cart_section(no_of_cart_items) {
		const $no_item_element = this.$cart_items_wrapper.find('.no-item-wrapper');

		// if cart has items and no item is present
		no_of_cart_items > 0 && $no_item_element && $no_item_element.remove() && this.$cart_header.css('display', 'flex');

		no_of_cart_items === 0 && !$no_item_element.length && this.make_no_items_placeholder();
	}

	on_numpad_event($btn) {
		const current_action = $btn.attr('data-button-value');
		const action_is_field_edit = ['qty', 'discount_percentage', 'rate'].includes(current_action);
		const action_is_allowed = action_is_field_edit ? (
			(current_action == 'rate' && this.allow_rate_change) ||
			(current_action == 'discount_percentage' && this.allow_discount_change) ||
			(current_action == 'qty')) : true;

		const action_is_pressed_twice = this.prev_action === current_action;
		const first_click_event = !this.prev_action;
		const field_to_edit_changed = this.prev_action && this.prev_action != current_action;

		if (action_is_field_edit) {
			if (!action_is_allowed) {
				const label = current_action == 'rate' ? 'Rate'.bold() : 'Discount'.bold();
				const message = __('Editing {0} is not allowed as per POS Profile settings', [label]);
				frappe.show_alert({
					indicator: 'red',
					message: message
				});
				frappe.utils.play_sound("error");
				return;
			}

			if (first_click_event || field_to_edit_changed) {
				this.prev_action = current_action;
			} else if (action_is_pressed_twice) {
				this.prev_action = undefined;
			}
			this.numpad_value = '';

		} else if (current_action === 'checkout') {
			this.prev_action = undefined;
			this.toggle_item_highlight();
			this.events.numpad_event(undefined, current_action);
			return;
		} else if (current_action === 'remove') {
			this.prev_action = undefined;
			this.toggle_item_highlight();
            
			this.events.numpad_event(undefined, current_action);
			return;
		} else {
			this.numpad_value = current_action === 'delete' ? this.numpad_value.slice(0, -1) : this.numpad_value + current_action;
			this.numpad_value = this.numpad_value || 0;
		}

		const first_click_event_is_not_field_edit = !action_is_field_edit && first_click_event;

		if (first_click_event_is_not_field_edit) {
			frappe.show_alert({
				indicator: 'red',
				message: __('Please select a field to edit from numpad')
			});
			frappe.utils.play_sound("error");
			return;
		}

		if (flt(this.numpad_value) > 100 && this.prev_action === 'discount_percentage') {
			frappe.show_alert({
				message: __('Discount cannot be greater than 100%'),
				indicator: 'orange'
			});
			frappe.utils.play_sound("error");
			this.numpad_value = current_action;
		}

		this.highlight_numpad_btn($btn, current_action);
		this.events.numpad_event(this.numpad_value, this.prev_action);
	}
    
    
	highlight_numpad_btn($btn, curr_action) {
		const curr_action_is_highlighted = $btn.hasClass('highlighted-numpad-btn');
		const curr_action_is_action = ['qty', 'discount_percentage', 'rate', 'done'].includes(curr_action);

		if (!curr_action_is_highlighted) {
			$btn.addClass('highlighted-numpad-btn');
		}
		if (this.prev_action === curr_action && curr_action_is_highlighted) {
			// if Qty is pressed twice
			$btn.removeClass('highlighted-numpad-btn');
		}
		if (this.prev_action && this.prev_action !== curr_action && curr_action_is_action) {
			// Order: Qty -> Rate then remove Qty highlight
			const prev_btn = $(`[data-button-value='${this.prev_action}']`);
			prev_btn.removeClass('highlighted-numpad-btn');
		}
		if (!curr_action_is_action || curr_action === 'done') {
			// if numbers are clicked
			setTimeout(() => {
				$btn.removeClass('highlighted-numpad-btn');
			}, 200);
		}
	}

	toggle_numpad(show) {
		if (show) {
			this.$totals_section.css('display', 'none');
			this.$numpad_section.css('display', 'flex');
		} else {
			this.$totals_section.css('display', 'flex');
			this.$numpad_section.css('display', 'none');
		}
		this.reset_numpad();
	}
  
	reset_numpad() {
		this.numpad_value = '';
		this.prev_action = undefined;
		this.$numpad_section.find('.highlighted-numpad-btn').removeClass('highlighted-numpad-btn');
	}

	toggle_numpad_field_edit(fieldname) {
		if (['qty', 'discount_percentage', 'rate'].includes(fieldname)) {
			this.$numpad_section.find(`[data-button-value="${fieldname}"]`).click();
		}
	}

	// toggle_customer_info(show) {
	// 	if (show) {
	// 		const { customer } = this.customer_info || {};
           
	// 		this.$cart_container.css('display', 'none');
	// 		this.$customer_section.css({
	// 			'height': '100%',
	// 			'padding-top': '0px'
	// 		});
	// 		this.$customer_section.find('.customer-details').html(
	// 			`<div class="header">
	// 				<div class="label">Contact Details</div>
	// 				<div class="close-details-btn">
	// 					<svg width="32" height="32" viewBox="0 0 14 14" fill="none">
	// 						<path d="M4.93764 4.93759L7.00003 6.99998M9.06243 9.06238L7.00003 6.99998M7.00003 6.99998L4.93764 9.06238L9.06243 4.93759" stroke="#8D99A6"/>
	// 					</svg>
	// 				</div>
	// 			</div>
	// 			<div class="customer-display">
	// 				${this.get_customer_image()}
	// 				<div class="customer-name-desc">
	// 					<div class="customer-name">${customer}</div>
	// 					<div class="customer-desc"></div>
	// 				</div>
	// 			</div>
	// 			<div class="customer-fields-container">
	// 				<div class="email_id-field"></div>
	// 				<div class="mobile_no-field"></div>
	// 				<div class="loyalty_program-field"></div>
	// 				<div class="loyalty_points-field"></div>
	// 			</div>
				
	// 			<div class="location-fields-container">
	// 			<div class="visitdate-field"></div>
	// 			<div class="so-field"></div>
	// 			<div class="event-field"></div>
	// 			<div class="event_slot-field"></div>
				
	// 				<div class="brand-field"></div>
	// 				<div class="city-field"></div>
	// 				<div class="branch-field"></div>
	// 				<div class="department-field"></div>
	// 			</div>
	// 			<div class="transactions-label">Recent Transactions</div>`
	// 		);
	// 		//added by shiby

    //         $('.location-fields-container').css({
	// 				'background-color': '#0799a3bd',
	// 				'display': 'grid',
	// 				'grid-template-columns': 'repeat(2,minmax(0,1fr))',
	// 				'margin-top': 'var(--margin-md)',
	// 				'-moz-column-gap': 'var(--padding-sm)',
	// 				'column-gap': 'var(--padding-sm)',
	// 				'row-gap': 'var(--padding-xs)',
	// 				'padding-right': '3px',
	// 				'padding-left': '3px'
    //         });
	// 		this.$customer_section.append(`<div class="location-details"></div>`);
	// 		//
	// 		// transactions need to be in diff div from sticky elem for scrolling
	// 		this.$customer_section.append(`<div class="customer-transactions"></div>`);
            

	// 		this.render_customer_fields();
	// 		//added by shiby
	// 		this.render_location_fields();
	// 		//
		  
	// 		this.fetch_customer_transactions();

	// 	} else {
			
	// 		if(this.non_sharable_slot==1 )
	// 			{
	// 				if(!cur_pos.cart.location_visitdate_field.value)
	// 				{
	// 					frappe.show_alert({
	// 						message: __("Please select Visit Date."),
	// 						indicator: 'red'
	// 					})
	// 					return frappe.utils.play_sound("error");

	// 				}
	// 				if(!cur_pos.cart.location_event_slot_field.value)
	// 				{
	// 					frappe.show_alert({
	// 						message: __("Please select slot."),
	// 						indicator: 'red'
	// 					})
	// 					return frappe.utils.play_sound("error");

	// 				}
	// 				if(!cur_pos.cart.location_brand_field.value)
	// 				{
	// 					frappe.show_alert({
	// 						message: __("Please select brand."),
	// 						indicator: 'red'
	// 					})
	// 					return frappe.utils.play_sound("error");

	// 				}
	// 				if(!cur_pos.cart.location_city_field.value)
	// 				{
	// 					frappe.show_alert({
	// 						message: __("Please select city."),
	// 						indicator: 'red'
	// 					})
	// 					return frappe.utils.play_sound("error");

	// 				}
	// 				if(!cur_pos.cart.location_branch_field.value)
	// 				{
	// 					frappe.show_alert({
	// 						message: __("Please select branch."),
	// 						indicator: 'red'
	// 					})
	// 					return frappe.utils.play_sound("error");

	// 				}
					
					
				
	// 			}
	// 			this.$cart_container.css('display', 'flex');
	// 		this.$customer_section.css({
	// 			'height': '',
	// 			'padding-top': ''
	// 		});

	// 		this.update_customer_section();
           
				
	// }
			
	// }
	toggle_customer_info(show) {
		if (show) {
			const { customer } = this.customer_info || {};
           
			this.$cart_container.css('display', 'none');
			this.$customer_section.css({
				'height': '100%',
				'padding-top': '0px'
			});
			this.$customer_section.find('.customer-details').html(
				`<div class="header">
					<div class="label">Contact Details</div>
					<div class="close-details-btn">
						<svg width="32" height="32" viewBox="0 0 14 14" fill="none">
							<path d="M4.93764 4.93759L7.00003 6.99998M9.06243 9.06238L7.00003 6.99998M7.00003 6.99998L4.93764 9.06238L9.06243 4.93759" stroke="#8D99A6"/>
						</svg>
					</div>
				</div>
				<div class="customer-display">
					${this.get_customer_image()}
					<div class="customer-name-desc">
						<div class="customer-name">${customer}</div>
						<div class="customer-desc"></div>
					</div>
				</div>
				<div class="customer-fields-container">
					<div class="email_id-field"></div>
					<div class="mobile_no-field"></div>
					<div class="loyalty_program-field"></div>
					<div class="loyalty_points-field"></div>
                   
				</div>
				
				 
                 <div class="btn edit-customer-btn"  style="background-color: rgba(7, 153, 163, 0.74);font-weight: bold">Edit Customer</div>
				<div class="transactions-label">Recent Transactions</div>`
			);
			//added by shiby

           
			this.$customer_section.append(`<div class="location-details"></div>`);
			//
			// transactions need to be in diff div from sticky elem for scrolling
			this.$customer_section.append(`<div class="customer-transactions"></div>`);
            const me = this;
            this.$customer_section.on('click', '.edit-customer-btn', function () {
               
                window.open('#Form/Customer/'+me.customer_info.customer, '_blank')
                    
                    
            });
			this.render_customer_fields();
			//added by shiby
			//this.render_location_fields();
			//
		  
			this.fetch_customer_transactions();

		} else {
	
				this.$cart_container.css('display', 'flex');
			this.$customer_section.css({
				'height': '',
				'padding-top': ''
			});

			this.update_customer_section();
           
				
	}
			
	}
	render_customer_fields() {
		const $customer_form = this.$customer_section.find('.customer-fields-container');

		const dfs = [{
			fieldname: 'email_id',
			label: __('Email'),
			fieldtype: 'Data',
			options: 'email',
			placeholder: __("Enter customer's email")
		},{
			fieldname: 'mobile_no',
			label: __('Phone Number'),
			fieldtype: 'Data',
			placeholder: __("Enter customer's phone number")
		},{
			fieldname: 'loyalty_program',
			label: __('Loyalty Program'),
			fieldtype: 'Link',
			options: 'Loyalty Program',
			placeholder: __("Select Loyalty Program")
		},{
			fieldname: 'loyalty_points',
			label: __('Loyalty Points'),
			fieldtype: 'Data',
			read_only: 1
		}];

		const me = this;
		dfs.forEach(df => {
            
                this[`customer_${df.fieldname}_field`] = frappe.ui.form.make_control({
               
                    df: { ...df,
                        onchange: handle_customer_field_change,
                    },
                    parent: $customer_form.find(`.${df.fieldname}-field`),
                    render_input: true,
                });

            
			
            //console.log(this[`customer_edit_customer_field`],"customer_edit_customer_field")
			this[`customer_${df.fieldname}_field`].set_value(this.customer_info[df.fieldname]);
			const frm=this.events.get_frm();
			if(frm.doc.items.length==0)
			{
				
				if(cur_pos.cart.customer_mobile_no_field){cur_pos.cart.customer_mobile_no_field.input.readOnly=false}
				}
			else{
				
				if(cur_pos.cart.customer_mobile_no_field){cur_pos.cart.customer_mobile_no_field.input.readOnly=true}
				
				//this[`customer_mobile_no_field`].attr('readonly', false);
			}
            
           
		})
        
		function handle_customer_field_change() {
			const current_value = me.customer_info[this.df.fieldname];
			const current_customer = me.customer_info.customer;
			


			if (this.value && current_value != this.value && this.df.fieldname != 'loyalty_points') {
				

				frappe.call({
					method: 'erpnext.selling.page.point_of_sale.point_of_sale.set_customer_info',
					args: {
						fieldname: this.df.fieldname,
						customer: current_customer,
						value: this.value
					},
					callback: (r) => {
						if(!r.exc) {
							me.customer_info[this.df.fieldname] = this.value;
							frappe.show_alert({
								message: __("Customer contact updated successfully."),
								indicator: 'green'
							});
							frappe.utils.play_sound("submit");
						}
					}
				});
			}
		}
	}
//Added by Shiby
	// render_location_fields() {
       
	// 	var slotoptions= this.getslotDetails('','');
	// 	var opbranch=this.getbranchDetails('');
	// 	const $customer_form = this.$customer_section.find('.location-fields-container');
    //     const query = { query: 'vim.custom_script.point_of_sale.point_of_sale.event_query' };
    //     const soquery = { soquery: 'vim.custom_script.point_of_sale.point_of_sale.so_query' };
	// 	const dfs = [{
	// 		fieldname: 'visitdate',
	// 		label: __('Visit Date'),
	// 		fieldtype: 'Date'
			
	// 	}
    //     ,{
	// 		fieldname: 'so',
	// 		label: __('Sales Order'),
	// 		fieldtype: 'Link',
	// 		options:'Sales Order', 
    //         get_query: () => soquery,
    //         filters: {  
    //             "customer":[ "=", this.customer_info.customer?this.customer_info.customer:'' ]  ,           
    //            "pos_status":[ "=", 'Open']
    //         },
    //         placeholder: __("Select SO")
           	
			
	// 	},{
	// 		fieldname: 'event',
	// 		label: __('Event'),
	// 		fieldtype: 'Link',
	// 		options: 'Item',				
	// 			get_query: () => query,
	// 			placeholder: __("Event"),
				
	// 	},
    //     ,{
            
    //         fieldname: 'event_slot',
	// 		label: __('Slot'),
	// 		fieldtype: 'Select',
	// 		options:slotoptions,
    //         placeholder: __("Slot"),
               
	// 	},{
	// 		fieldname: 'brand',
	// 		label: __('Brand'),
	// 		fieldtype: 'Link',
	// 		options: 'Dimension Brand',
	// 		placeholder: __("Enter customer's email")
	// 	},{
	// 		fieldname: 'city',
	// 		label: __('City'),
	// 		fieldtype: 'Link',
	// 		options:'Dimension City',
	// 		placeholder: __("Enter customer's phone number")
	// 	},{
	// 		fieldname: 'branch',
	// 		label: __('Branch'),
	// 		fieldtype: 'Select',
	// 		options: opbranch,
	// 		placeholder: __("Select Branch")
	// 	},{
	// 		fieldname: 'department',
	// 		label: __('Department'),
	// 		fieldtype: 'Link',
	// 		options:'Dimension Department'
			
	// 	}
    // ];

	// 	const me = this;
	
	// 	dfs.forEach(df => {
	// 		this[`location_${df.fieldname}_field`] = frappe.ui.form.make_control({
	// 			df: { ...df,
	// 				onchange: handle_location_field_change,
					
	// 			},
	// 			parent: $customer_form.find(`.${df.fieldname}-field`),
	// 			render_input: true,
	// 		});
          
    //         me.slot_field=this.location_info.event_slot;
    //         me.branch_field=this.location_info.branch;
		
	// 		if(me.branch_field && cur_pos.cart.location_branch_field )
	// 		{
	// 			cur_pos.cart.location_branch_field.set_value(me.branch_field)
	// 			cur_pos.cart.location_branch_field.refresh();
	// 		}
	// 		this[`location_${df.fieldname}_field`].set_value(me.location_info[df.fieldname]);
	// 	})
	// 	function handle_location_field_change() {
	// 		const current_value = me.location_info[this.df.fieldname];
	// 		const current_customer = me.customer_info.customer;
	// 		const visitdate_value=this.value
	// 		if(this.value)
	// 		{
	// 			if(this.df.fieldname == 'so')
	// 			{
	// 			cur_pos.cart.location_event_field.value='';
	// 			cur_pos.cart.location_event_slot_field.value='';
	// 			me.non_sharable_slot=0;
	// 			me.location_info.event='';
	// 			me.location_info.event_slot='';
	// 			cur_pos.cart.location_event_field.refresh();
	// 			cur_pos.cart.location_event_slot_field.refresh();	
	// 			cur_pos.cart.location_so_field.read_only=false;
	// 			cur_pos.cart.location_event_field.read_only=true;
	// 			cur_pos.cart.location_event_slot_field.read_only=true;
				
	// 			}
	// 			if(this.df.fieldname == 'event')
	// 			{
				
	// 			cur_pos.cart.location_event_slot_field.value='';
	// 			cur_pos.cart.location_so_field.value='';
	// 			me.location_info.so='';
	// 			//me.location_info.event_slot='';
	// 			me.non_sharable_slot=0;
	// 			cur_pos.cart.location_event_slot_field.refresh();
	// 			cur_pos.cart.location_so_field.refresh();	
	// 			cur_pos.cart.location_so_field.read_only=true;
	// 			cur_pos.cart.location_event_field.read_only=false;
	// 			cur_pos.cart.location_event_slot_field.read_only=false;
				
	// 			}
	// 			if(this.df.fieldname=='visitdate')
	// 			{
	// 			cur_pos.cart.location_so_field.value='';
	// 			cur_pos.cart.location_event_field.value='';
	// 			cur_pos.cart.location_event_slot_field.value='';
	// 			me.location_info.so='';
				
	// 			me.location_info.event='';
    //             me.location_info.event_slot='';
	// 			cur_pos.cart.location_so_field.refresh();
	// 			cur_pos.cart.location_event_field.refresh();
	// 			cur_pos.cart.location_event_slot_field.refresh();
	// 			me.non_sharable_slot=0;
	// 			}

	// 		}
	// 		else{
	// 			cur_pos.cart.location_event_field.value='';
	// 			cur_pos.cart.location_event_slot_field.value='';
	// 			cur_pos.cart.location_so_field.value='';
	// 			me.location_info.so='';
				
	// 			me.location_info.event='';
    //             me.location_info.event_slot='';
	// 			me.non_sharable_slot=0;
	// 			cur_pos.cart.location_event_field.refresh();
	// 			cur_pos.cart.location_event_slot_field.refresh();
	// 			cur_pos.cart.location_so_field.refresh();	
	// 			cur_pos.cart.location_so_field.read_only=false;
	// 			cur_pos.cart.location_event_field.read_only=false;
	// 			cur_pos.cart.location_event_slot_field.read_only=false;
				

	// 		}
		
	// 		me.location_info[this.df.fieldname]=this.value;
	// 		const frm = me.events.get_frm();
	// 		if (this.value && current_value != this.value && this.df.fieldname == 'visitdate') {
				
	// 			//me.location_info.visitdate =this.value;
				
	// 			frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'visit_date', this.value);
				
	// 			cur_pos.cart.location_so_field.get_query= function() {					
	// 								return {
	// 								 filters: [
	// 								  ["Sales Order","customer", "=", current_customer?current_customer:''],
	// 								  ["Sales Order","docstatus", "=", 1],
	// 								  ["Sales Order","pos_status", "=", 'Open'],
	// 								  ["Sales Order","delivery_date", "=", me.location_info.visitdate]
	// 								 ]
								 
	// 								}
								 
	// 					}

	// 		}
	// 		if (this.value && current_value != this.value && this.df.fieldname == 'so') {
	// 				var sorder=this.value;
	// 				var item_list_data=[];
	// 				frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'sales_order', this.value);					
	// 				me.get_items(sorder);
	// 				if(this.value)
	// 				{
	// 					frappe.call({
	// 						method: "vim.custom_script.point_of_sale.point_of_sale.get_payment_entry",
	// 						args: {
	// 							sorder: sorder
	// 						},
	// 						async: false,
	// 						callback: function(r) {
	// 							item_list_data = (r.message['result_list'] || []); 
	// 							console.log(item_list_data,"item_list_data")
	// 							var allocated_amount = 0;
	// 							Object.entries(item_list_data).forEach(([key, value]) => {
									
	// 								allocated_amount=flt(value["allocated_amount"])
	// 							});
	// 							var child = cur_frm.add_child("advances");
	// 							frappe.model.set_value(child.doctype, child.name, "allocated_amount", allocated_amount)
	// 							cur_frm.refresh_field("advances")
	// 						}
	// 					});
	// 				}
	// 		}
			
	// 		if (this.value && current_value != this.value && this.df.fieldname == 'event') {
	// 			frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'event', this.value);
	// 			var event=this.value
    //             if(me.slot_field==undefined )
    //             {
                    
    //                 me.clear_cart();
    //             }
    //             else if(me.slot_field=='')
    //             {
                   
    //                 me.clear_cart();
    //             }
                
    //             me.get_items_event(event);
    //             if(me.slot_field && me.slot_field!='')
    //                {
                   
    //                 	me.slot_change=false;
    //                    cur_pos.cart.location_event_slot_field.set_value(me.slot_field)
    //                    cur_pos.cart.location_event_slot_field.refresh();
                      
    //                 }
               
                       
	// 		}
	// 		if (this.value && current_value != this.value && this.df.fieldname == 'event_slot') {
	// 			//me.location_info.event_slot =this.value;
	// 			frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'slot', this.value);
	// 			var slot=this.value
               
    //             if(me.slot_change==undefined )
    //             {
                    
    //                 me.make_item_slot(slot,cur_pos.cart.location_event_field.value)
    //             }
    //             else if(me.slot_change==true)
    //             {
                   
    //                 me.make_item_slot(slot,cur_pos.cart.location_event_field.value)
    //             }
	// 		}
    //         if (this.value && current_value != this.value && this.df.fieldname == 'brand') {
	// 			frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'brand', this.value);
	// 			var brand=this.value
    //             me.get_branch_list(this.value);
              
    //             if(me.branch_field && me.branch_field!='')
    //                {
						
                    
	// 				   cur_pos.cart.location_branch_field.set_value(me.branch_field)
    //                    cur_pos.cart.location_branch_field.refresh();
    //                 }
               
	// 		}
	// 		if (this.value && current_value != this.value && this.df.fieldname == 'city') {
	// 			frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'city', this.value);
				
	// 		}
	// 		if (this.value && current_value != this.value && this.df.fieldname == 'branch') {
	// 			frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'branch', this.value);
				
	// 		}
	// 		if (this.value && current_value != this.value && this.df.fieldname == 'department') {
	// 			frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'department', this.value);
				
	// 		}
			
	// 		//me.location_info[this.df.fieldname]=this.value;
	// 	}
		
	// }
    //
    render_location_fields() {
		const $customer_form = this.$location_fields_container;
        const soquery = { soquery: 'vim.custom_script.point_of_sale.point_of_sale.so_query' };
		const dfs = [{
			fieldname: 'visitdate',
			label: __('Visit Date'),
			fieldtype: 'Date',
			default:frappe.datetime.nowdate()
		}
        ,{
			fieldname: 'so',
			label: __('Sales Order'),
			fieldtype: 'Link',
			options:'Sales Order', 
            get_query: () => soquery,
            filters: {  
                "customer":[ "=", this.customer_info.customer?this.customer_info.customer:'' ]  ,           
               "pos_status":[ "=", 'Open'],
			   "delivery_date":["=",frappe.datetime.nowdate()]
            },
            placeholder: __("Select SO")
		}
       
    ];
		const me = this;
        if(!cur_pos.cart.location_visitdate_field)
        {
            dfs.forEach(df => {
                this[`location_${df.fieldname}_field`] = frappe.ui.form.make_control({
                    df: { ...df,
                        onchange: handle_location_field_change,
                        
                    },
                    parent: $customer_form.find(`.${df.fieldname}-field`),
                    render_input: true,
                });
                this[`location_${df.fieldname}_field`].set_value(me.location_info[df.fieldname]);
            })
		    	cur_pos.cart.location_visitdate_field.set_value(String(frappe.datetime.nowdate()))
				//me.get_default_so();
				
				
        }
        else{
			
			if(cur_pos.cart.location_visitdate_field)
			{
				cur_pos.cart.location_visitdate_field.set_value(String(frappe.datetime.nowdate()))
				//me.get_default_so();
				
				
			}
				
			
			
            
        }
		
		function handle_location_field_change() {
			const current_value = me.location_info[this.df.fieldname];
			const current_customer = me.customer_info.customer;
			
			if(this.value)
			{
				if(this.df.fieldname == 'so')
				{
				 me.non_sharable_slot=0;
				
				}
				
				if(this.df.fieldname=='visitdate')
				{
				    cur_pos.cart.location_so_field.value='';
				    me.location_info.so='';
				    me.non_sharable_slot=0;
                    cur_pos.cart.location_so_field.set_value('');
					//me.get_default_so();
				}
			}
			else{
				me.location_info.so='';
			}
		
			me.location_info[this.df.fieldname]=this.value;
			const frm = me.events.get_frm();
           
			if (this.value && current_value != this.value && this.df.fieldname == 'visitdate') {
				frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'visit_date', this.value);
               if(cur_frm.doc.__islocal==1)
			   {
				
				cur_pos.cart.location_so_field.get_query= function() {					
					return {
					 filters: [
					  ["Sales Order","customer", "=", current_customer?current_customer:''],
					  ["Sales Order","docstatus", "=", 1],
					  ["Sales Order","pos_status", "=", 'Open'],
					  ["Sales Order","delivery_date", "=", me.location_info.visitdate]
					 ]
					}
				}
				//me.get_default_so();
				
			   }
			   else{
				 
				
				cur_pos.cart.location_so_field.get_query= function() {					
					return {
					 filters: [
					  ["Sales Order","customer", "=", current_customer?current_customer:''],
					  ["Sales Order","docstatus", "=", 1],
					  ["Sales Order","pos_status", "=", 'Executed'],
					  ["Sales Order","delivery_date", "=", me.location_info.visitdate]
					 ]
					}
				}
			   }
				
			}
			if (this.value && current_value != this.value && this.df.fieldname == 'so') {
					var sorder=this.value;
					var item_list_data=[];
					frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'sales_order', this.value);	
                    frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'sales_order_no', this.value);						
				if(cur_pos.cart.location_visitdate_field.value!='')
                {
					
                    me.get_positems(sorder);
					if(this.value)
					{
						frappe.call({
							method: "vim.custom_script.point_of_sale.point_of_sale.get_payment_entry",
							args: {
								sorder: sorder
							},
							async: false,
							callback: function(r) {
								item_list_data = (r.message['result_list'] || []); 
								
								var allocated_amount = 0;
								if(item_list_data.length>0)
								{
									Object.entries(item_list_data).forEach(([key, value]) => {
									
										allocated_amount=flt(value["allocated_amount"])
									});
									var child = cur_frm.add_child("advances");
									frappe.model.set_value(child.doctype, child.name, "allocated_amount", allocated_amount)
									cur_frm.refresh_field("advances")
								}
								
								
							}
						});
					}
                }
                   
			}
			
		}
		
	}
    
    async get_default_so()
	{
		if(cur_frm.doc.__islocal==1)
		{
			
			const  res = await frappe.db.get_value("Sales Order",{'customer': cur_frm.doc.customer,'delivery_date':cur_pos.cart.location_visitdate_field.value,'pos_status':'Open','docstatus':1}  , "name");
			
			if(cur_frm.doc.customer)
			{
				cur_pos.cart.location_so_field.set_value(String(res.message.name))
			}
		}

		
		//cur_pos.cart.location_so_field.set_value(String(res.message.name))
		//return res.message.name;
	}
	
    fetch_customer_transactions() {
		frappe.db.get_list('POS Invoice', {
			filters: { customer: this.customer_info.customer, docstatus: 1 },
			fields: ['name', 'grand_total', 'status', 'posting_date', 'posting_time', 'currency'],
			limit: 20
		}).then((res) => {
			const transaction_container = this.$customer_section.find('.customer-transactions');

			if (!res.length) {
				transaction_container.html(
					`<div class="no-transactions-placeholder">No recent transactions found</div>`
				)
				return;
			};

			const elapsed_time = moment(res[0].posting_date+" "+res[0].posting_time).fromNow();
			this.$customer_section.find('.customer-desc').html(`Last transacted ${elapsed_time}`);

			res.forEach(invoice => {
				const posting_datetime = moment(invoice.posting_date+" "+invoice.posting_time).format("Do MMMM, h:mma");
				let indicator_color = {
					'Paid': 'green',
					'Draft': 'red',
					'Return': 'gray',
					'Consolidated': 'blue'
				};

				transaction_container.append(
					`<div class="invoice-wrapper" data-invoice-name="${escape(invoice.name)}">
						<div class="invoice-name-date">
							<div class="invoice-name">${invoice.name}</div>
							<div class="invoice-date">${posting_datetime}</div>
						</div>
						<div class="invoice-total-status">
							<div class="invoice-total">
								${format_currency(invoice.grand_total, invoice.currency, 0) || 0}
							</div>
							<div class="invoice-status">
								<span class="indicator-pill whitespace-nowrap ${indicator_color[invoice.status]}">
									<span>${invoice.status}</span>
								</span>
							</div>
						</div>
					</div>
					<div class="seperator"></div>`
				)
			});
		});
	}
    //Added by Shiby
	// fetch_location_details() {
	// 	frappe.db.get_value('POS Profile', this.pos_profile, ["is_event"]).then(({ message }) => {
					
	// 		this.location_info = { ...message };
			
		
	// });
    
	// }

	load_invoice() {
		const frm = this.events.get_frm();
        
		
		this.fetch_customer_details(frm.doc.customer).then(() => {
			this.events.customer_details_updated(this.customer_info);
			this.update_customer_section();
		});
		//added by shiby
		this.location_info={}
		this.render_location_fields();
		this.fetch_location_details(frm.doc.name)
		this.non_sharable_slot=0;
		
       
		//
		this.$cart_items_wrapper.html('');
		if (frm.doc.items.length) {
          
			frm.doc.items.forEach(item => {
				this.update_item_html(item);
			});
		} else {
			this.make_no_items_placeholder();
			this.highlight_checkout_btn(false);
		}

		this.update_totals_section(frm);
     
		if(frm.doc.docstatus === 1) {
			this.$totals_section.find('.checkout-btn').css('display', 'none');
			this.$totals_section.find('.edit-cart-btn').css('display', 'none');
		} else {
			this.$totals_section.find('.checkout-btn').css('display', 'flex');
			this.$totals_section.find('.edit-cart-btn').css('display', 'none');
		}

		this.toggle_component(true);

		var tbl = cur_frm.doc.seleceted_packed_items || [];
        var item_list_data=[];
            var i = tbl.length;
            if(cur_frm.doc.is_return)
            {
                while (i--)
                 {
                    tbl[i].packed_quantity=tbl[i].packed_quantity*-1
                 }
                frappe.call({
                    method: "vim.custom_script.point_of_sale.point_of_sale.get_return_packed_items",
                    args: {
                        pos_invoice: cur_frm.doc.return_against
                    },
                    async: false,
                    callback: function(r) {
						item_list_data=   (r.message['result_list'] || []);
						
						var item_code="",parent_item='',set_no='',packed_quantity=0
                        Object.entries(item_list_data).forEach(([key, value]) => {
                            
							 item_code=value["item_code"]
							parent_item=value["parent_item"]
							set_no=value["set_no"]
							packed_quantity=value["packed_quantity"]
							
						
                            var itr = tbl.length;
							
                            while (itr--)
                            {
                              
                                if(tbl[itr].set_no==set_no && tbl[itr].parent_item==parent_item && tbl[itr].item_code==item_code)
                                 {
									
                                    var quantity=(parseInt(Math.abs(tbl[itr].packed_quantity))-parseInt(Math.abs(packed_quantity)))*-1
									frappe.model.set_value(tbl[itr].doctype, tbl[itr].name, "packed_quantity", quantity)
									frappe.model.set_value(tbl[itr].doctype, tbl[itr].name, "quantity", quantity*parseInt(tbl[itr].combo_qty))
									combo_qty
									cur_frm.refresh_field("seleceted_packed_items")
                                 }
                                }
                            
                           
							});
                        cur_frm.doc.seleceted_packed_items=tbl
                      
                        // cur_frm.refresh_field("seleceted_packed_items")
                    }
                });
               
            }
            cur_frm.refresh();


	}

	toggle_component(show) {
		show ? this.$component.css('display', 'flex') : this.$component.css('display', 'none');
	}
    //Added by Shiby
	clear_cart(){
        cur_pos.cart.location_event_slot_field.set_value(undefined)
        cur_pos.cart.location_event_slot_field.refresh();
		const frm = this.events.get_frm();
		if(frm.doc.items.length){
			frm.doc.items.forEach(item => {
				const $item = this.get_cart_item(item);	
                var current_item={}
                current_item.item_code = item.item_code
                current_item.batch_no = item.batch_no
                current_item.uom = item.uom
                frappe.model.set_value(item.doctype, item.name, 'qty', 0)
                    .then(() => {
                        frappe.model.clear_doc(item.doctype, item.name);
                        cur_pos.update_cart_html(current_item, true);
                        
                    })
                    .catch(e => console.log(e));
			    
				
			});
        this.events.numpad_event(undefined, "remove");

		}
			
	}
	//clear cart and added selected SO Items to cart
	async get_positems(sorder) {
		
       		const me=this;	
		
			const frm = this.events.get_frm();
		
			frm.doc.items.forEach(item => {
                
				const $item = this.get_cart_item(item);	
                var current_item={}
                current_item.item_code = item.item_code
                current_item.batch_no = item.batch_no
                current_item.uom = item.uom
                current_item.rate = item.rate
              // 
                
                frappe.model.set_value(item.doctype, item.name, 'qty', 0)
                    .then(() => {
                        frappe.model.clear_doc(item.doctype, item.name);
                        cur_pos.update_cart_html(current_item, true);
                        
                    })
                    .catch(e => console.log(e));
			    
				
			});
        this.events.numpad_event(undefined, "remove");
		
        if(sorder)
        {	
			const  res = await frappe.db.get_value("Sales Order",{'name': sorder,'pos_status':'Open'}  , "select_slot");
			
			// if(!res || !res.message.select_slot || res.message.select_slot=='')
			// {
			 	this.get_so_pos_items(sorder);
                
                
                //  frappe.db.get_value('Sales Order', {'name': sorder}, ['additional_discount_percentage','discount_amount','coupon_code']).then(({ message }) => {
                //     frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'applied_coupen',message.coupon_code);
                //     frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'couponcode',message.coupon_code);
                //     this.update_discount_so(message.additional_discount_percentage,message.discount_amount)
                    
                //  })
                frappe.db.get_value('Sales Order', {'name': sorder}, ['additional_discount_percentage','discount_amount','coupon_code']).then(({ message }) => {
                    console.log(message.coupon_code,message)  
                    this.update_discount_so(message.additional_discount_percentage,message.discount_amount)
                    frappe.db.get_value('Coupon Code', {'name':message.coupon_code}, ['coupon_code']).then(({ message }) => {
                      console.log(message.coupon_code,message)  
                    frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'applied_coupen',message.coupon_code);
                    frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'couponcode',message.coupon_code);
                    
                })
                 })
				
			// }
			// else{
			// 	frappe.db.get_value('Work Order', {'sales_order': sorder}, ['docstatus','status']).then(({ message }) => {
				
			// 		if(message.docstatus==1)
			// 		{
			// 			this.get_so_pos_items(sorder);	
			// 		}
			// 		else if(message.docstatus==undefined)
			// 		{
			// 			cur_pos.cart.location_so_field.set_value('')
			// 			frappe.show_alert({
			// 				indicator: 'red',
			// 				message: "Work Order Not Created"
			// 			});
			// 			return;
			// 		}
			// 		else {
						
			// 			cur_pos.cart.location_so_field.set_value('')
			// 			frappe.show_alert({
			// 				indicator: 'red',
			// 				message: "Work Order Not Submitted. Status: "+message.status
			// 			});
			// 			return;
						
			// 		}
	
			// 	});
	
			// }
		

        }
		
		
	}
	async	get_so_pos_items(sorder )
	{
		var item_list_data=[];var packed_list_data=[];
		const me=this;	
        
		frappe.call({
			method: "vim.custom_script.point_of_sale.point_of_sale.get_items",
			args: {
				sorder: sorder
			},
			async: false,
			callback: function(r) {
				item_list_data = (r.message['result_list'] || []); 
                packed_list_data= (r.message['packed_list_data'] || []); 
                ////console.log('Anuppppp', item_list_data);
				 let item_row = undefined;   if(item_list_data.length>0) 
				 {
					// console.log("getsoitem")
				 }             
				Object.entries(item_list_data).forEach(([key, value]) => {
                   
					//item_row = this.get_item_from_frm(item_code, batch_no, uom)
					var rate=0;var item_code = "";	var batch_no = "";	var serial_no = "";	var stock_uom = "";var conversion_factor = "";	var uom="";	var bundle_item="";				
					// item.price_list_rate,item.base_price_list_rate,item.base_rate,item.base_amount,item.base_net_rate,item.base_net_amount,
					// item.base_rate_with_margin,item.actual_qty,item.valuation_rate,item.conversion_factor,item.net_rate,item.net_amount
					item_code=(value["item_code"]);
					batch_no=(value["batch_no"]);
					serial_no=(value["serial_no"]);
					stock_uom=(value["stock_uom"]);
					rate=(value["rate"]);
					uom=(value["uom"]); 
					if(value["bundle_item"])
					{
						bundle_item=(value["bundle_item"]); 
					}
				
                    //cur_pos.item_selector.bundle_item=bundle_item==''?null:1
					me.events.so_item_selected({ field: 'qty', value: value["qty"], item: { item_code, batch_no, serial_no, stock_uom,rate,conversion_factor,uom }})
                    
					
				});
                Object.entries(packed_list_data).forEach(([key, value]) => {
                var child = cur_frm.add_child("seleceted_packed_items");
					frappe.model.set_value(child.doctype, child.name, "parent_item", value["parent_item"])
					frappe.model.set_value(child.doctype, child.name, "item_code", value["item_code"])
					frappe.model.set_value(child.doctype, child.name, "set_no",parseInt(value["set_no"]))
					frappe.model.set_value(child.doctype, child.name, "combo_qty",parseInt(value["qty"]))
					if(value["set_no"]!=0)
					{
						frappe.model.set_value(child.doctype, child.name, "packed_quantity", 0)
					}
					else{
						frappe.model.set_value(child.doctype, child.name, "packed_quantity", parseInt(value["packed_quantity"]))
					}
					
                    frappe.model.set_value(child.doctype, child.name, "default_item", value["default_item_in_pos"])
					cur_frm.refresh_field("seleceted_packed_items")
                })
				
				
			}
		});
		// callback();
	}
	//clear cart and added selected event to cart if non_sharable_slot=1
    // get_items_event(event) {
        
    //     const slot_= this.location_info.event_slot
       
	// 	//cur_pos.cart.slot_field.set_value('');
       
	
	// 	this.non_sharable_slot=0;	
	// 	if(event)
    //     {
	// 		frappe.db.get_value('Item', event, ["non_sharable_slot","minimum_sales_quantity"]).then(({ message }) => {
	// 			this.minimum_sales_quantity=message.minimum_sales_quantity
	// 			if (message.non_sharable_slot==1){
				
	// 				this.non_sharable_slot=1;
    //        			// $(`.slot-field`).css('display', 'block');
    //        			 var resultlist=[];var slotlist=[];
	// 				if(cur_pos.cart.location_visitdate_field.value){
    //        			 frappe.call({
    //                 "method": "vim.custom_script.point_of_sale.point_of_sale.get_slot_list",
    //                 async: false,
    //                 args:{item_name:event?event:'',is_new:0,delivery_date:cur_pos.cart.location_visitdate_field.value},
    //                 callback: function (r) {
						
    //                     resultlist = (r.message['result_list'] || []);
                        
    //                     Object.entries(resultlist).forEach(([key, value]) => {
    //                         var item = "";
    //                         item=(value["slot_name"]);
    //                         slotlist.push(item);
    //                     });
                        
    //                     this.slot_change=true;
	// 					cur_pos.cart.location_event_slot_field.df.options = slotlist
    //                     cur_pos.cart.location_event_slot_field.refresh();
                        
    //                 }})
                    
				
	// 				}
	// 				else{
	// 					frappe.show_alert({
	// 						indicator: 'red',
	// 						message: "Select Visit date"
	// 					});
	// 				}
            
				
	// 				}
	// 				else{
					
	// 					this.make_item_slot('',cur_pos.cart.location_event_field.value,this.minimum_sales_quantity)
					   
	// 				}
					
	// 			});	 
		
			
                       
    //     }
						
	// }
	//added selected event to cart if non_sharable_slot=0
    // make_item_slot(slot,item){
   
    //    const me=this;
    //     const item_code = item;
    //     let batch_no = '';
    //     let serial_no = '';
    //     let uom = '';
	// 	let slot_name='';
      
    //     batch_no = batch_no === "undefined" ? undefined : batch_no;
    //     serial_no = serial_no === "undefined" ? undefined : serial_no;
    //     uom = uom === "undefined" ? undefined : uom;
	// 	slot_name = slot === "undefined" ? undefined : slot;
    //     me.events.item_selected({ field: 'qty', value: me.minimum_sales_quantity, item: { item_code, batch_no, serial_no, uom,slot }});
      

    // }
	// get_branch_list(brandname){
	
	// 	var resultlist=[];
	// 	frappe.call({
	// 	"method": "vim.custom_script.point_of_sale.point_of_sale.get_branch_list",
	// 	async: false,
	// 	    args:{brand:brandname?brandname:''},
	// 	    callback: function (r) {
			
	// 		resultlist = (r.message['branch_list'] || []);
	// 		cur_pos.cart.location_branch_field.df.options = resultlist
			
	// 		cur_pos.cart.location_branch_field.set_value(cur_frm.doc.branch)
    //         cur_pos.cart.location_branch_field.refresh();
	// 	}
	// })
    
            
		
	// }
	save_as_draft(){
       
		cur_pos.save_draft_invoice();
        // if(cur_pos.cart.discount_field)
        // {
        //     this.disremark=''
        //     this.hide_discount_control(0,'') 
        //     this.discount_field.value=0;
            
        // }  
         

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
                
                cur_pos.update_discount_approval(discount, remarks);
                dialog.hide();
            },
            primary_action_label: __('Submit')
            });

dialog.show()
dialog.$wrapper.find('.modal-dialog').css("width", "400px");
dialog.$wrapper.find('.modal-dialog').css("height", "300px");
   
}

	
//end
	

}