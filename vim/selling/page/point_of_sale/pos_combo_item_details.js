erpnext.PointOfSale.ComboItemDetails = class {
	constructor({ wrapper, events, settings }) {
		this.wrapper = wrapper;
		this.events = events;		
		this.current_item = {};
		this.init_component();
		this.total_packed_qty=0;
		this.combo_items = [];
		this.set_items = [];
		this.combo_default_items = [];
		
	}

	init_component() {
		this.prepare_dom();
		this.combo_items = [];
		this.combo_default_items = [];
		this.set_items = [];
		this.init_child_components();
		this.bind_events();
		this.toggle_component(false);
        
      //this.init_numpad_components() ;
       
        //this.load_combo_items_data();
		// this.attach_shortcuts();
	}

	prepare_dom() {
		this.wrapper.append(
			`<section class="combo-item-details-container" style="width: 600px; overflow-y: scroll;" >            
            </section>`
		)
		this.$component = this.wrapper.find('.combo-item-details-container');       
	}

	init_child_components() {	
		
		this.$component.html(
			`<div class="combo-item-details-header">
				
				<div class="combo-close-btn" style=" text-align:right;">
					<svg width="32" height="32" viewBox="0 0 14 14" fill="none">
						<path d="M4.93764 4.93759L7.00003 6.99998M9.06243 9.06238L7.00003 6.99998M7.00003 6.99998L4.93764 9.06238L9.06243 4.93759" stroke="#8D99A6"/>
					</svg>
				</div>
				
				</div>
			</div>
			<div class="row col-md-12 total-qty"  >
				<div class="  col-md-3 label text-center" style="font-weight: bolder;">Total Qty</div>
				<div class=" col-md-5">
                <span class="input-group-append d-sm-inline-block">
            <button class="btn tot-btn" data-dir="inc" onclick="updatetotalQty(this)" >
             +
            </button>
            </span>
				<input class="form-control text-center combo-total-qty" style="font-weight: bolder;width: 50px;display: inline; !important " value=${this.total_packed_qty?this.total_packed_qty:0}   onclick="changetotqty(this)">
				<span class="input-group-append d-sm-inline-block">
            <button class="btn tot-btn" data-dir="dec" onclick="updatetotalQty(this)" 
            >
                -
            </button>
            </span>
                </div><div class="col-md-4 btn combo-item-rm-btn"  style="color: red;font-weight: bold">Remove from cart</div></div>
				
				<div class="col-md-12 combo-defalt-items-container" style=" align-self: flex-end;
				display: grid;
				 ">
				
			</div>
			<div class="col-md-12 combo-items-container" style=" align-self: flex-end;
			display: grid;
			">
				
			</div>
            <div  class="col-md-12  row" style="margin-left: 0px;"> <div ></div>
            <div class="col-md-12 btn combo-item-ok-btn"   style="font-weight: bold;text-align: right;background-color: var(--blue-500);
            color: rgb(255, 255, 255);
            ">OK</div><div ></div></div>
            <script>
            function updatetotalQty(elmnt) {
    
                var btn = $(elmnt),
                        input = btn.closest('.total-qty').find('input'),
                        oldValue = input.val().trim(),
                        newVal = 0;
                    if (btn.attr('data-dir') == 'inc') {
                        newVal = parseInt(oldValue) + 1;
                    }
                    else
                    {
                        if (oldValue >= 1) {
                            newVal = parseInt(oldValue) - 1;
                        }
                    }
                    input.val(newVal);
            
            }
            </script>
            `
		
		)
			
		

        this.$items_container = this.$component.find('.combo-items-container');
		this.$default_items_container = this.$component.find('.combo-defalt-items-container');
        
	}
    init_numpad_components(){
        this.$component.append(`<div class="combo-numpad-section"></div>`) 
        this.make_combo_numpad();
    }
   
	toggle_combo_item_details_section(item) {
       
		const { item_code, batch_no, uom ,rate} = this.current_item;
		this.total_packed_qty=cur_pos.combo_item_details.current_item.qty;
		
		const item_code_is_same = item && item_code === item.item_code;
		const batch_is_same = item && batch_no == item.batch_no;
		const uom_is_same = item && uom === item.uom;
		this.item_has_changed = !item ? false : item_code_is_same && batch_is_same && uom_is_same ? false : true;
       if(item){
			this.item_has_changed=true;
			//this.load_combo_items_data(item.item_code,item.qty);
	   }
	   else{
			this.item_has_changed=false;
	   }
	   this.events.toggle_combo_item_selector(this.item_has_changed);
		this.toggle_component(this.item_has_changed);
		
		if (this.item_has_changed) {
           
			this.doctype = item.doctype;
			this.item_meta = frappe.get_meta(this.doctype);
			this.name = item.name;
			this.item_row = item;
			this.currency = this.events.get_frm().doc.currency;
			this.current_item = { item_code: item.item_code, batch_no: item.batch_no, uom: item.uom ,rate:item.rate};
			this.load_combo_items_data(item.item_code,item.qty);
		}
      
	}
	toggle_component(show) {
		show ? this.$component.css('display', 'block') : this.$component.css('display', 'none');
        
	}
	check_set_total(){
		var setno_wise_qty=[]
		var setno=''
		this.set_items.forEach(item => {
			
				var check_item_set = cur_pos.combo_item_details.combo_items.filter(set => 
					(parseInt(set.set_no) === parseInt(item.set_no)
				   ));
				 
				   var settotal=0
				   if (check_item_set){
					
				   for (let rm = 0; rm < check_item_set.length; rm++) {
					settotal=settotal+Math.abs(check_item_set[rm].packed_quantity)
				   }
				}
				
				var current_item={} 
				current_item.set_no = item.set_no
				current_item.set_total = settotal
				var check_duplicate = setno_wise_qty.filter(d => 
					(parseInt(d.set_no) === parseInt(item.set_no)
				   ));
				  
				   if(check_duplicate.length==0){
					setno_wise_qty.push(current_item); 
				   }
				
			
			
		})
		return setno_wise_qty
	}
    bind_events() {
		const me=this;
		this.$component.on('click', '.combo-close-btn,.combo-item-ok-btn', () => {
			me.total_packed_qty=$('.combo-total-qty').val();			
			
            const { item_code, batch_no,serial_no,uom,rate } = me.current_item;
			let item_row = undefined; var flag=1;
			item_row = cur_pos.get_item_from_frm(item_code, batch_no, uom);
           
           if(this.combo_default_items.length ==0 && this.set_items.length>0 && cur_pos.combo_item_details.combo_items.length==0)
            {
                frappe.throw('Select Set Item')
            }
			var setno_wise_qty=me.check_set_total()
				setno_wise_qty.forEach(item => {
					if(item.set_total!=me.total_packed_qty){
						frappe.throw('Total Set Quantity must be Total Cart Quantity')
					}
					

			})
            if(cur_pos.combo_item_details.combo_items.reduce((accumulator, current) => accumulator + current.x, 0)!=0 || this.combo_default_items.length>0 ){
                
                cur_pos.combo_item_details.combo_items.forEach(item => {
               
                var filtered = cur_pos.combo_item_details.combo_items.filter((a)=>{if(a.set_no==item.set_no){return a}});
                let totqty =item.set_no!=0?  filtered.reduce(function (accumulator, items) {
                    
                    return accumulator + Math.abs(items.packed_quantity);
                  }, 0):0;
                 
                if(parseInt(Math.abs(totqty))>parseInt(Math.abs(me.total_packed_qty)))
                 {               
                   
                    frappe.throw('Set Quantity Exceeds Total Quantity')
                  }
                                    
                  else{
                    flag=1;
                  }
                  var check_item = cur_pos.combo_item_details.combo_items.filter(set => 
                    (parseInt(set.set_no) === parseInt(item.set_no)
                   ));
                 
                   var settotal=0
                   for (let rm = 0; rm < check_item.length; rm++) {
                    settotal=settotal+Math.abs(check_item[rm].packed_quantity)
                   }
                 
                   if( item.set_no!=0 && !cur_frm.doc.is_return && parseInt(Math.abs(settotal))<parseInt(Math.abs(me.total_packed_qty))){
                    
                    frappe.throw('Set quantity must be total quantity')
                    
                  }

                })
            if(flag==1){
              me.update_selected_pack_item()
              me.events.item_selected({ field: 'qty', value:flt(me.total_packed_qty) , item: { item_code, batch_no, serial_no, uom,rate }}).then(() => 
              {const event = {
                field: "qty",
                value:flt(me.total_packed_qty),
                item: { item_code, batch_no, uom }
            }
             
             setTimeout(() => {
                
                cur_pos.cart.make_no_items_placeholder();
             cur_frm.doc.items.forEach(item => {

                cur_pos.cart.update_item_html(item);
            });
            me.events.close_combo_item_details();
            }, 900);
            
        })
            
              
                
            }
            else{
                frappe.throw('Set Quantity Exceeds Total Quantity'
              )
            }
        }
        else{
            
            me.events.item_selected({ field: 'qty', value:0 , item: { item_code, batch_no, serial_no, uom }}).then(() => 
            {const event = {
              field: "qty",
              value:0,
              item: { item_code, batch_no, uom }
          }
           
           setTimeout(() => {
              
            cur_pos.cart.make_no_items_placeholder();
           cur_frm.doc.items.forEach(item => {

              cur_pos.cart.update_item_html(item);
          });
          me.events.close_combo_item_details();
          }, 900);
          
      })
               

        }
        
	})
    this.$component.on('click', '.combo-item-rm-btn', () => {
       // 
        me.events.combo_numpad_event();
		me.events.close_combo_item_details();
    })
	}
	update_selected_pack_item(){
		
		const frm = this.events.get_frm();
       
				if(cur_frm.doc.__islocal==1){

				}
                    
				  this.combo_default_items.forEach(item => 
					{
						var flag=0;	
						cur_pos.combo_item_details.combo_items.forEach(comboitem => {
                         
							if(item.item_code==comboitem.item_code && item.parent_item==comboitem.parent_item)
							{
								flag=1;
							}

						})
				
				  if(flag==0){
					var cur_item={};
					
					cur_item.item_code=item.item_code
					cur_item.parent_item=cur_pos.combo_item_details.current_item.item_code
					cur_item.packed_quantity=$('.combo-total-qty').val()
					cur_item.set_no=item.set_no
					cur_item.combo_qty=item.qty
					cur_item.default_item_in_pos=1					
					cur_pos.combo_item_details.combo_items.push(cur_item)

				  }
						
				  })
                 
				cur_pos.combo_item_details.combo_items.forEach(item => {
					var flag=0;	
                   
					frm.doc.seleceted_packed_items.forEach(citem => {
                        
						if(item.item_code==citem.item_code && item.parent_item==citem.parent_item)
							{
								flag=1;
								let combo_item_row = undefined;								
								combo_item_row = cur_pos.get_combo_item_from_frm(citem.item_code,citem.parent_item);
							
								frappe.model.set_value(combo_item_row.doctype, combo_item_row.name, 'packed_quantity', item.packed_quantity);
								cur_frm.refresh_field("seleceted_packed_items")
							}
				});
				
				
				if(flag==0){
				
						var child = cur_frm.add_child("seleceted_packed_items");
					frappe.model.set_value(child.doctype, child.name, "parent_item", item.parent_item)
					frappe.model.set_value(child.doctype, child.name, "item_code", item.item_code)
					frappe.model.set_value(child.doctype, child.name, "set_no", item.set_no)
					frappe.model.set_value(child.doctype, child.name, "combo_qty", item.combo_qty)
					frappe.model.set_value(child.doctype, child.name, "packed_quantity", item.packed_quantity)
                    frappe.model.set_value(child.doctype, child.name, "default_item", item.default_item_in_pos)
					cur_frm.refresh_field("seleceted_packed_items")
					
				}
				
			})
           if(cur_frm.doc.__islocal==1){
					
				}
        
       
           
	}
    async load_combo_items_data(item_code,qty) {
		$('.combo-total-qty').val(qty)
		
		this.get_items(item_code).then(({message}) => {
        
            cur_pos.combo_item_details.combo_items.forEach(citem => {
				message.ditems.forEach(item => {
					if(item.item_code==citem.item_code){
						item.packed_quantity=citem.packed_quantity
					}


				})

			})
			cur_pos.combo_item_details.combo_items.forEach(citem => {                
				message.items.forEach(item => {
					if(item.item_code==citem.item_code){
                       
						item.packed_quantity=citem.packed_quantity
					}


				})

			})
			
			this.combo_default_items=message.ditems;
			this.set_items=message.items
			this.render_item_list(message.items,message.sets,qty,message.ditems);
			
		});
	}

	get_items(item) {
		//const doc = this.events.get_frm().doc;		
		//let { item_group, pos_profile } = this;

		if(item){

        
            return frappe.call({
                method: "vim.custom_script.point_of_sale.point_of_sale.get_combo_items",
                freeze: true,
                args: { item },
            });
        }

	}

	render_item_list(items,sets,qty,ditems) {
		
		this.$items_container.html(''); var set_html='';var set_dhtml="";
		this.$default_items_container.html('');
		set_dhtml=`<div class="combo-defautl-item-wrapper" style="font-size: 12px;
		padding: 0.3rem;
		box-shadow: var(--shadow-base); position: relative; font-weight: bolder;background-color: rgba(7, 153, 163, 0.74); text-align: center;color:white;" >Default Items
		<table class="table mt-3 cart-table" style="margin:0px;margin-bottom:0px;margin-top: 0px!important;">
    
		<tbody><tr style="background-color:white!important;display: grid;
        grid-template-columns: repeat(5, minmax(0px, 1fr));">`
		ditems.forEach(item => {
		set_dhtml+=
		`<td style="width: 40%;padding: 0.55rem;font-weight: normal;"><div class="row col-md-12">
		<div  class="ditem-detail" data-item-code="${escape(item.item_code)}" data-qty="${escape(item.qty)}"
		data-description="${escape(item.description)}" data-set-no="${escape(item.set_no)}"
 >		<div><img class="h-full" src="${item.item_image}"  style="object-fit: cover;height: 40px;"></div><div>${frappe.ellipsis(item.item_code, 18)}</div></div>
				</div></td>`
		})
		set_dhtml+=`</tr></tbody></table></div>`
		this.$default_items_container.html(set_dhtml);
		sets.forEach(set => {
			set_html = this.get_combo_item_html(set,items,qty);
			this.$items_container.append(set_html);
		})
	}
	
    get_combo_item_html(set,items,qty) {
		var totqty=0;
		var sethtml= `<div class="combo-item-wrapper" style="font-size: 12px;
		padding: 0.3rem;
		box-shadow: var(--shadow-base); position: relative; font-weight: bolder;background-color: rgba(7, 153, 163, 0.74); text-align: center;color:white;">
	Set: ${set.set_no}
	<table class="table mt-3 cart-table" style="margin:0px;margin-bottom:0px;margin-top: 0px!important;">
    
    <tbody class="cart-items" >`
	items.forEach(item => {
		if(set.set_no==item.set_no)
		{
			
			sethtml+=`<tr style="background-color:white!important;"><td style="padding: 0.55rem;width: 10%;"><div class="d-flex"><div class="item-detail" data-item-code="${escape(item.item_code)}" data-qty="${escape(item.qty)}"
			   data-description="${escape(item.description)}" data-set-no="${escape(item.set_no)}"
			    ><div><img class="h-full" src="${item.item_image}"  style="object-fit: cover;height: 40px;"></div></div></div>
			   </td>
			   <td  style="width: 60%;
			   text-align: left;word-break: break-word;"> <div>
			   ${item.item_code}</div></td>
			   <td class="text-right" style="padding: 0.55rem;"width: 30%;" >
<div class="d-flex">

<div class="input-group number-spinner mt-1 mb-4" style="margin-bottom: 3.5px!important;" >
<span class="input-group-append d-sm-inline-block">
<button class="btn cart-btn" data-dir="up" style="padding:var(--padding-xs) var(--padding-sm);" onclick="updateQty(this)" data-item-code="${escape(item.item_code)}" data-qty="${escape(item.qty)}"
data-description="${escape(item.description)}" data-set-no="${escape(item.set_no)}">
    +
</button>
</span>

    <input class="form-control text-center cart-qty" readonly onchange="updatetotal(this)" value=${frappe.ellipsis(item.packed_quantity, 18)} data-item-code=${frappe.ellipsis(item.item_code, 18)} style="max-width: 70px;">
    <span class="input-group-prepend d-sm-inline-block">
    <button class="btn cart-btn" data-dir="dwn" style="padding:var(--padding-xs) var(--padding-sm);" onclick="updateQty(this)" data-item-code="${escape(item.item_code)}" data-qty="${escape(item.qty)}"
    data-description="${escape(item.description)}" data-set-no="${escape(item.set_no)}">
        –
    </button>
</span>
   
    </div>

<div>
    
    </div>
</div>

</td></tr>`
totqty+=item.packed_quantity
		}
	})
	
	sethtml+=` </tbody>
    
	<tfoot class="cart-tax-items">
		<!-- Total at the end of the cart items -->
<tr style="background-color: rgb(236, 238, 240)!important;">

<th  colspan="2" class="text-right item-grand-total" style="font-size: 12px; width:70%;" >Total Set Qty
</th>
<th class="text-left item-grand-total totals" style=" width:30%" >
${totqty}
</th>
</tr>
	</tfoot>

</table></div>
<script>
function updatetotal(elmnt) {
	
	var btn = $(elmnt)
	var tot=parseInt(btn.val().trim())+(isNaN($(elmnt).closest('table').find('tfoot th:eq(1)').text()) ? 0 : parseInt($(elmnt).closest('table').find('tfoot th:eq(1)').text()))
	$(elmnt).closest('table').find('tfoot th:eq(1)').text(tot)
}

function updateQty(elmnt) {
	var tot=isNaN($(elmnt).closest('table').find('tfoot th:eq(1)').text()) ? 0 : parseInt($(elmnt).closest('table').find('tfoot th:eq(1)').text());
	
	var btn = $(elmnt),
			input = btn.closest('.number-spinner').find('input'),
			oldValue = input.val().trim(),
			newVal = 0;
	
		if (btn.attr('data-dir') == 'up') {
			newVal = parseInt(oldValue) + 1;
			
			if(((isNaN(tot)?0:parseInt(tot))+1)>parseInt($('.combo-total-qty').val()))
			{
				newVal=oldValue;
				frappe.show_alert({
					indicator: 'red',
					message: "Selected Quantity exceeded Total Quantity :"+$('.combo-total-qty').val()
				});
			}
			else
			{
				tot=(isNaN(tot)?0:parseInt(tot))+1;
				var flag=0;		
				cur_pos.combo_item_details.combo_items.forEach(item => {				
				if(item.item_code==decodeURI(btn.attr('data-item-code')))
				{
					item.packed_quantity=newVal;flag=1;
				}
				})
				if(flag==0){
				
					var cur_item={};
					var item_code=String(btn.attr("data-item-code"));
					cur_item.item_code=decodeURI(item_code)
                    cur_item.parent_item=cur_pos.combo_item_details.current_item.item_code
					cur_item.packed_quantity=newVal
					cur_item.set_no=btn.attr("data-set-no")
					cur_item.combo_qty=btn.attr("data-qty")
					cur_item.default_item_in_pos=0
					cur_pos.combo_item_details.combo_items.push(cur_item)
					
				}
				
			}
			
		} else {
            if(parseInt($('.combo-total-qty').val())<0){
                newVal = parseInt(oldValue) - 1;
				tot=(isNaN(tot)?0:parseInt(tot))-1;
				var flag=0;		
				cur_pos.combo_item_details.combo_items.forEach(item => {				
				if(item.item_code==decodeURI(btn.attr('data-item-code')))
				{
					item.packed_quantity=newVal;flag=1;
				}
				})
				if(flag==0){
				
					var cur_item={};
					var item_code=String(btn.attr("data-item-code"));
					cur_item.item_code=decodeURI(item_code)
					cur_item.parent_item=cur_pos.combo_item_details.current_item.item_code
					cur_item.packed_quantity=newVal
					cur_item.set_no=btn.attr("data-set-no")
					cur_item.combo_qty=btn.attr("data-qty")
					cur_item.default_item_in_pos=0
					cur_pos.combo_item_details.combo_items.push(cur_item)
					
				}
            }
            else{
                if(oldValue>=1){
                    newVal = parseInt(oldValue) - 1;
                    tot=(isNaN(tot)?0:parseInt(tot))-1;
                    var flag=0;		
                    cur_pos.combo_item_details.combo_items.forEach(item => {				
                    if(item.item_code==decodeURI(btn.attr('data-item-code')))
                    {
                        item.packed_quantity=newVal;flag=1;
                    }
                    })
                    if(flag==0){
                    
                        var cur_item={};
                        var item_code=String(btn.attr("data-item-code"));
                        cur_item.item_code=decodeURI(item_code)
                        cur_item.parent_item=cur_pos.combo_item_details.current_item.item_code
                        cur_item.packed_quantity=newVal
                        cur_item.set_no=btn.attr("data-set-no")
                        cur_item.combo_qty=btn.attr("data-qty")
                        cur_item.default_item_in_pos=0
                        cur_pos.combo_item_details.combo_items.push(cur_item)
                        
                    }
                }
            }
			

			
		}
		input.val(newVal);
		$(elmnt).closest('table').find('tfoot th:eq(1)').text(tot)
		
	
  }
  function changetotqty(elmnt) { 
		cur_pos.combo_item_details.combo_items.forEach(item => {				
			if(item.default_item_in_pos==1)
			{
				item.item_qty=$('.combo-total-qty').val();
			}
			else{
				if(item.item_qty>$('.combo-total-qty').val())
				{
					
					frappe.show_alert({
						indicator: 'red',
						message: "Selected Quantity exceeded Total Quantity :"+$('.combo-total-qty').val()
			});
			$('.combo-total-qty').val(0)
				}
			}
			})
		
	}
</script>`



		
	return sethtml;	
	}
}
	
	
  



	
	