erpnext.PointOfSale.PastOrderSummary = class {
	constructor({ wrapper, events }) {
		this.wrapper = wrapper;
		this.events = events;
        this.sendinvoicesms=0;
        this.posinvoice=0;
		this.init_component();
	}

	init_component() {
		this.prepare_dom();
		this.init_email_print_dialog();
		this.bind_events();
		this.attach_shortcuts();
	}

	prepare_dom() {
		this.wrapper.append(
			`<section class="past-order-summary">
				<div class="no-summary-placeholder">
					Select an invoice to load summary data
				</div>
				<div class="invoice-summary-wrapper">
					<div class="abs-container">
						<div class="upper-section"></div>
						<div class="label">Items</div>
						<div class="items-container summary-container"></div>
						<div class="label">Totals</div>
						<div class="totals-container summary-container"></div>
						<div class="label">Payments</div>
						<div class="payments-container summary-container"></div>
						<div class="summary-btns"></div>
					</div>
				</div>
			</section>`
		);

		this.$component = this.wrapper.find('.past-order-summary');
		this.$summary_wrapper = this.$component.find('.invoice-summary-wrapper');
		this.$summary_container = this.$component.find('.abs-container');
		this.$upper_section = this.$summary_container.find('.upper-section');
		this.$items_container = this.$summary_container.find('.items-container');
		this.$totals_container = this.$summary_container.find('.totals-container');
		this.$payment_container = this.$summary_container.find('.payments-container');
		this.$summary_btns = this.$summary_container.find('.summary-btns');
	}

	init_email_print_dialog() {
		const email_dialog = new frappe.ui.Dialog({
			title: 'Email Receipt',
			fields: [
				{fieldname: 'email_id', fieldtype: 'Data', options: 'Email', label: 'Email ID'},
				// {fieldname:'remarks', fieldtype:'Text', label:'Remarks (if any)'}
			],
			primary_action: () => {
				this.send_email();
			},
			primary_action_label: __('Send'),
		});
		this.email_dialog = email_dialog;

		const print_dialog = new frappe.ui.Dialog({
			title: 'Print Receipt',
			fields: [
				{fieldname: 'print', fieldtype: 'Data', label: 'Print Preview'}
			],
			primary_action: () => {
				this.print_receipt();
			},
			primary_action_label: __('Print'),
		});
		this.print_dialog = print_dialog;
	}

	get_upper_section_html(doc) {
		const { status } = doc;
		let indicator_color = '';

		in_list(['Paid', 'Consolidated'], status) && (indicator_color = 'green');
		status === 'Draft' && (indicator_color = 'red');
		status === 'Return' && (indicator_color = 'grey');

		return `<div class="left-section">
					<div class="customer-name">${doc.customer}</div>
					<div class="customer-email">${this.customer_email}</div>
					<div class="cashier">Sold by: ${doc.owner}</div>
				</div>
				<div class="right-section">
					<div class="paid-amount">${format_currency(doc.paid_amount, doc.currency,2)}</div>
					<div class="invoice-name">${doc.name}</div>
					<span class="indicator-pill whitespace-nowrap ${indicator_color}"><span>${doc.status}</span></span>
				</div>`;
	}

	get_item_html(doc, item_data) {
		return `<div class="item-row-wrapper">
					<div class="item-name">${item_data.item_name}</div>
					<div class="item-qty">${item_data.qty || 0}</div>
					<div class="item-rate-disc">${get_rate_discount_html()}</div>
				</div>`;

		function get_rate_discount_html() {
			if (item_data.rate && item_data.price_list_rate && item_data.rate !== item_data.price_list_rate) {
				return `<span class="item-disc">(${item_data.discount_percentage}% off)</span>
						<div class="item-rate">${format_currency(item_data.rate, doc.currency,2)}</div>`;
			} else {
				return `<div class="item-rate">${format_currency(item_data.price_list_rate || item_data.rate, doc.currency,2)}</div>`;
			}
		}
	}

	get_discount_html(doc) {
		if (doc.discount_amount) {
			return `<div class="summary-row-wrapper">
						<div>Discount (${doc.additional_discount_percentage} %)</div>
						<div>${format_currency(doc.discount_amount, doc.currency,2)}</div>
					</div>`;
		} else {
			return ``;
		}
	}

	get_net_total_html(doc) {
		return `<div class="summary-row-wrapper">
					<div>Net Total</div>
					<div>${format_currency(doc.net_total, doc.currency,2)}</div>
				</div>`;
	}

	get_taxes_html(doc) {
		if (!doc.taxes.length) return '';

		let taxes_html = doc.taxes.map(t => {
			const description = /[0-9]+/.test(t.description) ? t.description : `${t.description} @ ${t.rate}%`;
			return `
				<div class="tax-row">
					<div class="tax-label">${description}</div>
					<div class="tax-value">${format_currency(t.tax_amount_after_discount_amount, doc.currency,2)}</div>
				</div>
			`;
		}).join('');

		return `<div class="taxes-wrapper">${taxes_html}</div>`;
	}

	get_grand_total_html(doc) {
		return `<div class="summary-row-wrapper grand-total">
					<div>Grand Total</div>
					<div>${format_currency(doc.grand_total, doc.currency,2)}</div>
				</div>`;
	}

	get_payment_html(doc, payment) {
		return `<div class="summary-row-wrapper payments">
					<div>${payment.mode_of_payment}</div>
					<div>${format_currency(payment.amount, doc.currency,2)}</div>
				</div>`;
	}

	bind_events() {
        const pome = this;
        cur_pos.item_selector.search_item_group.css('width','10%');
		this.$summary_container.on('click', '.return-btn', () => {
            const me = this;
        const dialog = new frappe.ui.Dialog({
        title: __('Approve Return'),
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
                    me.events.process_return(me.doc.name);
                    me.toggle_component(false);
                    me.$component.find('.no-summary-placeholder').css('display', 'flex');
                    me.$summary_wrapper.css('display', 'none');
                    dialog.hide();
                   
                }
                else
                {
                    frappe.show_alert({
                        message: __("No Permission."),
                        indicator: 'red'
                    })
                   
                }
                
                
               
            },
            primary_action_label: __('Login')
            });

            dialog.show()
            dialog.$wrapper.find('.modal-dialog').css("width", "400px");

               
            
			
		});

		this.$summary_container.on('click', '.edit-btn', () => {
			
			this.events.edit_order(this.doc.name);
			this.toggle_component(false);
			this.$component.find('.no-summary-placeholder').css('display', 'flex');
			this.$summary_wrapper.css('display', 'none');
		});

		this.$summary_container.on('click', '.delete-btn', () => {
			this.events.delete_order(this.doc.name);
			this.show_summary_placeholder();
		});

		this.$summary_container.on('click', '.delete-btn', () => {
			this.events.delete_order(this.doc.name);
			this.show_summary_placeholder();
			// this.toggle_component(false);
			// this.$component.find('.no-summary-placeholder').removeClass('d-none');
			// this.$summary_wrapper.addClass('d-none');
		});

		this.$summary_container.on('click', '.new-btn', () => {
			this.events.new_order();
            // setTimeout(() => {				
			 	//location.reload(true)
			// }, 100);
			this.toggle_component(false);
			this.$component.find('.no-summary-placeholder').css('display', 'flex');
			this.$summary_wrapper.css('display', 'none');
            $('.search-item-group').find('.dropdown-menu').find("a:first").trigger("click");
           
            
		});

		this.$summary_container.on('click', '.email-btn', () => {
			this.email_dialog.fields_dict.email_id.set_value(this.customer_email);
			this.email_dialog.show();
		});

		this.$summary_container.on('click', '.print-btn', () => {
			this.print_receipt();
		});
        this.$summary_container.on('click', '.send-btn', () => {
            console.log(this.doc,'dssdds')
            
			this.make_dialog(this.doc.customer,this.doc.name);
		});
        this.$summary_container.on('click', '.issue-btn', () => {
            const me=this
			let voucher = frappe.model.get_new_doc('Customer RFID');
		    voucher.pos_invoice =me.doc.name    
            frappe.set_route('Form', 'Customer RFID', voucher.name);
            cur_pos.show_header();
		});
	}
    
async validate_approver(){
    
   
}
	print_receipt() {
		const frm = this.events.get_frm();
		frappe.utils.print(
			this.doc.doctype,
			this.doc.name,
			frm.pos_print_format,
			this.doc.letter_head,
			this.doc.language || frappe.boot.lang
		);
        //this.$summary_container.find('.new-btn').click()
	}

	attach_shortcuts() {
		const ctrl_label = frappe.utils.is_mac() ? '⌘' : 'Ctrl';
		this.$summary_container.find('.print-btn').attr("title", `${ctrl_label}+P`);
		frappe.ui.keys.add_shortcut({
			shortcut: "ctrl+p",
			action: () => this.$summary_container.find('.print-btn').click(),
			condition: () => this.$component.is(':visible') && this.$summary_container.find('.print-btn').is(":visible"),
			description: __("Print Receipt"),
			page: cur_page.page.page
		});
		this.$summary_container.find('.new-btn').attr("title", `${ctrl_label}+Enter`);
		frappe.ui.keys.on("ctrl+enter", () => {
			const summary_is_visible = this.$component.is(":visible");
			if (summary_is_visible && this.$summary_container.find('.new-btn').is(":visible")) {
				this.$summary_container.find('.new-btn').click();
			}
		});
		this.$summary_container.find('.edit-btn').attr("title", `${ctrl_label}+E`);
		frappe.ui.keys.add_shortcut({
			shortcut: "ctrl+e",
			action: () => this.$summary_container.find('.edit-btn').click(),
			condition: () => this.$component.is(':visible') && this.$summary_container.find('.edit-btn').is(":visible"),
			description: __("Edit Receipt"),
			page: cur_page.page.page
		});
	}

	send_email() {
		const frm = this.events.get_frm();
		const recipients = this.email_dialog.get_values().email_id;
		const doc = this.doc || frm.doc;
		const print_format = frm.pos_print_format;

		frappe.call({
			method: "frappe.core.doctype.communication.email.make",
			args: {
				recipients: recipients,
				subject: __(frm.meta.name) + ': ' + doc.name,
				doctype: doc.doctype,
				name: doc.name,
				send_email: 1,
				print_format,
				sender_full_name: frappe.user.full_name(),
				_lang: doc.language
			},
			callback: r => {
				if (!r.exc) {
					frappe.utils.play_sound("email");
					if (r.message["emails_not_sent_to"]) {
						frappe.msgprint(__(
							"Email not sent to {0} (unsubscribed / disabled)",
							[ frappe.utils.escape_html(r.message["emails_not_sent_to"]) ]
						));
					} else {
						frappe.show_alert({
							message: __('Email sent successfully.'),
							indicator: 'green'
						});
					}
					this.email_dialog.hide();
				} else {
					frappe.msgprint(__("There were errors while sending email. Please try again."));
				}
			}
		});
	}

	add_summary_btns(map) {
		this.$summary_btns.html('');
		map.forEach(m => {
			if (m.condition) {
				m.visible_btns.forEach(b => {
					const class_name = b.split(' ')[0].toLowerCase();
					this.$summary_btns.append(
						`<div class="summary-btn btn btn-default ${class_name}-btn">${b}</div>`
					);
				});
			}
		});
		this.$summary_btns.children().last().removeClass('mr-4');
	}

	toggle_summary_placeholder(show) {
		if (show) {
			this.$summary_wrapper.css('display', 'none');
			this.$component.find('.no-summary-placeholder').css('display', 'flex');
		} else {
			this.$summary_wrapper.css('display', 'flex');
			this.$component.find('.no-summary-placeholder').css('display', 'none');
		}
	}
    make_dialog(customer,posinvoice_name){
        let a  = document.getElementsByClassName("send-btn")[0];
        
        frappe.call({
            method: "frappe.client.get_value",
            args: {
            "doctype": "Selling Settings",
            "fieldname": ["send_invoice_sms","pos_invoice"]
            }, callback: function(r) {
                console.log(r,'sdfdsf')
                this.sendinvoicesms=r.message.send_invoice_sms;
                this.posinvoice=r.message.pos_invoice;
                
                if(this.sendinvoicesms==1 && this.posinvoice==1){
                    frappe.call({
                        method: "frappe.client.get_value",
                        args: {
                        "doctype": "Customer",
                        "filters": {"name":customer},
                        "fieldname": "mobile_no"
                        }, callback: function(r) {
                        
                        const dialog = new frappe.ui.Dialog({
                            title: __('Send sms to'),
                            static: true,
                            fields: [
                                {
                                    fieldtype: 'Link', label: __('Customer'), fieldname: 'customer_name',
                                    options: 'Customer', reqd: 1,default:customer,read_only:1
                                },
                                {
                                    fieldtype: 'Int', label: __('Mobile No'),
                                     fieldname: 'mobile_no', reqd: 1,default:r.message["mobile_no"]
                                },
                              
                            ],
                            primary_action: async function({ customer_name,mobile_no }) {
                                    
                                        if(mobile_no.toString().length < 9 || mobile_no.toString().length > 10){
                                            frappe.throw("Invalid Mobile No !!")
                                        }
                                        return frappe.call({
                                            method: "invoice_sms.sms.send_sms.send_invoice_sms",
                                            args: {
                                                'mobile_no': mobile_no,
                                                'name': posinvoice_name,
                                                'type':'POS'
                                            },
                                            callback(res) {
                                                a.disabled=true;
                                                dialog.hide();
                                            }
                                        });
                              
                            },
                            primary_action_label: __('Submit')
                        });
                      
                        }});
                }
                else{
                    a.disabled=true;
                }
            }
            })
      
       
    }
	get_condition_btn_map(after_submission) {
		if (after_submission)
			return [{ condition: true, visible_btns: ['Print Receipt', 'Email Receipt','Issue RFID', 'New Order','Send SMS'] }];

		return [
			{ condition: this.doc.docstatus === 0, visible_btns: ['Edit Order', 'Delete Order'] },
			{ condition: !this.doc.is_return && this.doc.docstatus === 1, visible_btns: ['Print Receipt', 'Email Receipt','Issue RFID', 'Return']},
			{ condition: this.doc.is_return && this.doc.docstatus === 1, visible_btns: ['Print Receipt', 'Email Receipt']}
		];
	}

	load_summary_of(doc, after_submission=false) {
		after_submission ?
			this.$component.css('grid-column', 'span 10 / span 10') :
			this.$component.css('grid-column', 'span 6 / span 6');

		this.toggle_summary_placeholder(false);

		this.doc = doc;

		this.attach_document_info(doc);

		this.attach_items_info(doc);

		this.attach_totals_info(doc);

		this.attach_payments_info(doc);

		const condition_btns_map = this.get_condition_btn_map(after_submission);

		this.add_summary_btns(condition_btns_map);
        //this.print_receipt();
        
	}

	attach_document_info(doc) {
		frappe.db.get_value('Customer', this.doc.customer, 'email_id').then(({ message }) => {
			this.customer_email = message.email_id || '';
			const upper_section_dom = this.get_upper_section_html(doc);
			this.$upper_section.html(upper_section_dom);
		});
	}

	attach_items_info(doc) {
		this.$items_container.html('');
		doc.items.forEach(item => {
			const item_dom = this.get_item_html(doc, item);
			this.$items_container.append(item_dom);
			this.set_dynamic_rate_header_width();
		});
	}

	set_dynamic_rate_header_width() {
		const rate_cols = Array.from(this.$items_container.find(".item-rate-disc"));
		this.$items_container.find(".item-rate-disc").css("width", "");
		let max_width = rate_cols.reduce((max_width, elm) => {
			if ($(elm).width() > max_width)
				max_width = $(elm).width();
			return max_width;
		}, 0);

		max_width += 1;
		if (max_width == 1) max_width = "";

		this.$items_container.find(".item-rate-disc").css("width", max_width);
	}

	attach_payments_info(doc) {
		this.$payment_container.html('');
		doc.payments.forEach(p => {
			if (p.amount) {
				const payment_dom = this.get_payment_html(doc, p);
				this.$payment_container.append(payment_dom);
			}
		});
		if (doc.redeem_loyalty_points && doc.loyalty_amount) {
			const payment_dom = this.get_payment_html(doc, {
				mode_of_payment: 'Loyalty Points',
				amount: doc.loyalty_amount,
			});
			this.$payment_container.append(payment_dom);
		}
	}

	attach_totals_info(doc) {
		this.$totals_container.html('');

		const net_total_dom = this.get_net_total_html(doc);
		const taxes_dom = this.get_taxes_html(doc);
		const discount_dom = this.get_discount_html(doc);
		const grand_total_dom = this.get_grand_total_html(doc);
		this.$totals_container.append(net_total_dom);
		this.$totals_container.append(taxes_dom);
		this.$totals_container.append(discount_dom);
		this.$totals_container.append(grand_total_dom);
	}

	toggle_component(show) {
		show ? this.$component.css('display', 'flex') : this.$component.css('display', 'none');
	}
};