from __future__ import unicode_literals
import frappe,erpnext
from frappe.utils import cint, flt, cstr, get_link_to_form, nowtime
from frappe import _, throw
from erpnext.stock.get_item_details import get_bin_details
from erpnext.stock.utils import get_incoming_rate
from erpnext.stock.get_item_details import get_conversion_factor
from erpnext.stock.doctype.item.item import set_item_default
from frappe.contacts.doctype.address.address import get_address_display
from erpnext.controllers.accounts_controller import get_taxes_and_charges
from erpnext.accounts.utils import get_fiscal_year#, check_if_stock_and_account_balance_synced
from erpnext.controllers.stock_controller import StockController
from erpnext.stock.stock_ledger import get_valuation_rate
from erpnext.controllers.sales_and_purchase_return import get_rate_for_return
from frappe.model.document import Document
from erpnext.accounts.general_ledger import make_gl_entries, make_reverse_gl_entries, process_gl_map
from erpnext.stock import get_warehouse_account_map
from erpnext.accounts.utils import get_fiscal_years, validate_fiscal_year, get_account_currency
from frappe.utils import (today, flt, cint, fmt_money, formatdate,
	getdate, add_days, add_months, get_last_day, nowdate, get_link_to_form)
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
class SalesInvoicePackedItem(Document):
	pass
@frappe.whitelist()
def update_stock_ledger():
	try:
		voucher_no=frappe.db.sql(""" select distinct voucher_no from `tabSales Invoice Packed Item`  where is_stock_updated=0 limit 100""",as_dict=True)	
		if voucher_no :
			for inv in voucher_no:	
				frappe.errprint([inv.voucher_no,"update_stock_ledger"])
				sl_entries = []
			# Loop over items and packed items table
				for d in get_item_list(inv.voucher_no):
			
					if frappe.get_cached_value("Item", d.item_code, "is_stock_item") == 1 and flt(d.qty):
						if flt(d.conversion_factor)==0.0:
							d.conversion_factor = get_conversion_factor(d.item_code, d.uom).get("conversion_factor") or 1.0

					# On cancellation or return entry submission, make stock ledger entry for
					# target warehouse first, to update serial no values properly
	
						if d.warehouse :
								sl_entries.append(get_sle_for_source_warehouse(d))

						if d.target_warehouse:
							sl_entries.append(get_sle_for_target_warehouse(d))

				frappe.db.sql("""update `tabSales Invoice Packed Item` set `is_stock_updated`= 1 where voucher_no='{0}'""".format(inv.voucher_no))
				frappe.db.commit()	

			make_sl_entries(sl_entries)
	except Exception as e:
		frappe.throw(e)
def make_sl_entries( sl_entries, allow_negative_stock=False,
			via_landed_cost_voucher=False):
		from erpnext.stock.stock_ledger import make_sl_entries
		
		make_sl_entries(sl_entries, allow_negative_stock, via_landed_cost_voucher)
def get_sle_for_source_warehouse( item_row):
		sle = get_sl_entries(item_row, {
			"actual_qty": -1*flt(item_row.qty),
			"incoming_rate": item_row.incoming_rate,
			"recalculate_rate": 0
		})
		if item_row.target_warehouse :
			sle.dependant_sle_voucher_detail_no = item_row.name

		return sle

def get_sle_for_target_warehouse( item_row):
		sle = get_sl_entries(item_row, {
			"actual_qty": flt(item_row.qty),
			"warehouse": item_row.target_warehouse
		})

		
			
		sle.update({
					"incoming_rate": item_row.incoming_rate,
					"recalculate_rate": 1
				})
			

		return sle
def get_sl_entries(d, args):
		sl_dict = frappe._dict({
			"item_code": d.get("item_code", None),
			"warehouse": d.get("warehouse", None),
			"posting_date": d.posting_date,
			"posting_time": d.posting_time,
			'fiscal_year': get_fiscal_year(d.posting_date, company=d.company),
			"voucher_type": d.voucher_type,
			"voucher_no": d.voucher_no,
			"voucher_detail_no": d.sales_invoice_name,
			"actual_qty": 1*flt(d.get("stock_qty")),
			"stock_uom": frappe.db.get_value("Item", args.get("item_code") or d.get("item_code"), "stock_uom"),
			"incoming_rate": 0,
			"company": d.company,
			"batch_no": '',
			"serial_no": '',
			"project": '',
			"is_cancelled":  0
		})

		sl_dict.update(args)
		return sl_dict

def get_item_list(voucher_no):
	il = []
	
	list_item=frappe.db.sql("""select * from `tabSales Invoice Packed Item` where voucher_no='{0}' """.format(voucher_no),as_dict=True)
	
	for p in list_item:
						
						il.append(frappe._dict({
							'warehouse': p.warehouse ,
							'item_code': p.item_code,
							'qty': flt(p.total_quantity),
							"posting_date": p.posting_date,
							"posting_time": p.posting_time,
							"voucher_no": p.voucher_no,
							"voucher_detail_no": p.sales_invoice_name,
							'uom': p.uom,
							'batch_no': '',
							'serial_no': '',
							'name': p.sales_invoice_name,
							'target_warehouse': p.target_warehouse,
							"sales_invoice_name":p.sales_invoice_name,
							'company': p.company,
							'voucher_type': p.voucher_type,
							'allow_zero_valuation': p.allow_zero_valuation_rate,
							'sales_invoice_item': p.get("sales_invoice_item"),
							'dn_detail': p.get("dn_detail"),
							'incoming_rate': get_incoming_rate({
												"item_code": p.item_code,
												"warehouse": p.warehouse,
												"posting_date": p.posting_date,
												"posting_time": p.posting_time,
												"qty": p.total_quantity,
												"serial_no": '',
												"company": p.company,
												"voucher_type": p.voucher_type,
												"voucher_no": p.voucher_no,
												"allow_zero_valuation": p.allow_zero_valuation
				}, raise_error_if_no_rate=False)

						}))
	
	return il
@frappe.whitelist()
def make_gl_entries( gl_entries=None, from_repost=False):
	try:
		voucher_no=frappe.db.sql(""" select distinct voucher_no from `tabSales Invoice Packed Item`  where is_gl_created=0 limit 100""",as_dict=True)	
		if voucher_no :
			for inv in voucher_no:	
				frappe.errprint([inv.voucher_no,"glentry"])
				doc=frappe.get_doc("Sales Invoice",inv.voucher_no)
		
				from erpnext.accounts.general_ledger import make_gl_entries, make_reverse_gl_entries

				auto_accounting_for_stock = erpnext.is_perpetual_inventory_enabled(doc.company)
				if not gl_entries:
					gl_entries = doc.get_gl_entries(doc)

				if gl_entries:
			# if POS and amount is written off, updating outstanding amt after posting all gl entries
					update_outstanding = "No" if (cint(doc.is_pos) or doc.write_off_account or
						cint(doc.redeem_loyalty_points)) else "Yes"

					if doc.docstatus == 1:
						make_reverse_gl_entries(voucher_type=doc.doctype, voucher_no=doc.name)
						make_gl_entries(gl_entries, update_outstanding=update_outstanding, merge_entries=False, from_repost=from_repost)
					elif doc.docstatus == 2:
						make_reverse_gl_entries(voucher_type=doc.doctype, voucher_no=doc.name)

					if update_outstanding == "No":
						from erpnext.accounts.doctype.gl_entry.gl_entry import update_outstanding_amt
						update_outstanding_amt(doc.debit_to, "Customer", doc.customer,
							doc.doctype, doc.return_against if cint(doc.is_return) and doc.return_against else doc.name)

				elif doc.docstatus == 2 and cint(doc.update_stock) \
					and cint(auto_accounting_for_stock):
						make_reverse_gl_entries(voucher_type=doc.doctype, voucher_no=doc.name)
				frappe.db.sql("""update `tabSales Invoice Packed Item` set `is_gl_created`= 1 where voucher_no='{0}'""".format(inv.voucher_no))
				frappe.db.commit()
	except Exception as e:
		frappe.throw(e)
def get_gl_entries(doc, warehouse_account=None):
		from erpnext.accounts.general_ledger import merge_similar_entries

		gl_entries = []

		doc.make_customer_gl_entry(gl_entries)

		doc.make_tax_gl_entries(gl_entries)
		doc.make_internal_transfer_gl_entries(gl_entries)

		doc.make_item_gl_entries(gl_entries)

		# merge gl entries before adding pos entries
		gl_entries = merge_similar_entries(gl_entries)

		doc.make_loyalty_point_redemption_gle(gl_entries)
		doc.make_pos_gl_entries(gl_entries)
		doc.make_gle_for_change_amount(gl_entries)

		doc.make_write_off_gl_entry(gl_entries)
		doc.make_gle_for_rounding_adjustment(gl_entries)

		return gl_entries
	

def get_stock_ledger_details(voucher_no):
		stock_ledger = {}
		stock_ledger_entries = frappe.db.sql("""
			select
				name, warehouse, stock_value_difference, valuation_rate,
				voucher_detail_no, item_code, posting_date, posting_time,
				actual_qty, qty_after_transaction
			from
				`tabStock Ledger Entry`
			where
				voucher_type='Sales Invoice' and voucher_no='{0}'
		""".format(voucher_no), as_dict=True)

		for sle in stock_ledger_entries:
			stock_ledger.setdefault(sle.voucher_detail_no, []).append(sle)
		return stock_ledger		
def get_debit_field_precision():
		if not frappe.flags.debit_field_precision:
			frappe.flags.debit_field_precision = frappe.get_precision("GL Entry", "debit_in_account_currency")

		return frappe.flags.debit_field_precision
def get_voucher_details(voucher_no, default_expense_account, default_cost_center, sle_map):
		
			frappe.errprint(voucher_no)
			details =frappe.db.sql("""select * from `tabSales Invoice Packed Item` where voucher_no='{0}'""".format(voucher_no),as_dict=True)
			frappe.errprint(voucher_no)
			if default_expense_account or default_cost_center:
				for d in details:
					if default_expense_account and not d.get("expense_account"):
						d.expense_account = default_expense_account
					if default_cost_center and not d.get("cost_center"):
						d.cost_center = default_cost_center

			return details

def check_expense_account(item):
		if not item.get("expense_account"):
			msg = _("Please set an Expense Account in the Items table")
			frappe.throw(_("Row #{0}: Expense Account not set for the Item {1}. {2}")
				.format(item.idx, frappe.bold(item.item_code), msg), title=_("Expense Account Missing"))

		else:
			is_expense_account = frappe.get_cached_value("Account",
				item.get("expense_account"), "report_type")=="Profit and Loss"
			
			if is_expense_account and not item.get("cost_center"):
				frappe.throw(_("{0} : Cost Center is mandatory for Item {1}").format(
					_('Sales Invoice'),  item.get("item_code")))
def update_stock_ledger_entries(sle,voucher_no,company):
		sle.valuation_rate = get_valuation_rate(sle.item_code, sle.warehouse,
		'Sales Invoice', voucher_no, currency='SAR', company=company)

		sle.stock_value = flt(sle.qty_after_transaction) * flt(sle.valuation_rate)
		sle.stock_value_difference = flt(sle.actual_qty) * flt(sle.valuation_rate)

		if sle.name:
			frappe.db.sql("""
				update
					`tabStock Ledger Entry`
				set
					stock_value = %(stock_value)s,
					valuation_rate = %(valuation_rate)s,
					stock_value_difference = %(stock_value_difference)s
				where
					name = %(name)s""", (sle))

		return sle

def get_gl_dict( voucher_no,company,args, account_currency=None, item=None):
		"""this method populates the common properties of a gl entry record"""

		posting_date = args.get('posting_date') 
		fiscal_years = get_fiscal_years(posting_date, company=company)
		if len(fiscal_years) > 1:
			frappe.throw(_("Multiple fiscal years exist for the date {0}. Please set company in Fiscal Year").format(
				formatdate(posting_date)))
		else:
			fiscal_year = fiscal_years[0][0]

		gl_dict = frappe._dict({
			'company': company,
			'posting_date': posting_date,
			'fiscal_year': fiscal_year,
			'voucher_type': 'Sales Invoice',
			'voucher_no': voucher_no,
			'remarks': '',
			'debit': 0,
			'credit': 0,
			'debit_in_account_currency': 0,
			'credit_in_account_currency': 0,
			'is_opening':  "No",
			'party_type': None,
			'party': None,
			'project': ''
		})

		accounting_dimensions = get_accounting_dimensions()
		dimension_dict = frappe._dict()

		
		if item and item.get('cost_center'):
				dimension_dict["cost_center"] = item.get("cost_center")

		gl_dict.update(dimension_dict)
		gl_dict.update(args)

		if not account_currency:
			account_currency = get_account_currency(gl_dict.account)

		if gl_dict.account :
			validate_account_currency(gl_dict.account, account_currency)

		if gl_dict.account :
			set_balance_in_account_currency(gl_dict, account_currency, 1,
											'SAR')

		return gl_dict

def validate_account_currency(self, account, account_currency=None):
		valid_currency = [self.company_currency]
		if self.get("currency") and self.currency != self.company_currency:
			valid_currency.append(self.currency)

		if account_currency not in valid_currency:
			frappe.throw(_("Account {0} is invalid. Account Currency must be {1}")
				.format(account, (' ' + _("or") + ' ').join(valid_currency)))

def set_balance_in_account_currency(gl_dict, account_currency=None, conversion_rate=None, company_currency=None):
	if (not conversion_rate) and (account_currency != company_currency):
		frappe.throw(_("Account: {0} with currency: {1} can not be selected")
					 .format(gl_dict.account, account_currency))

def get_packed_item_list(voucher_no):
	il = []
	
	list_item=frappe.db.sql("""select * from `tabSales Invoice Packed Item` where voucher_no='{0}'""".format(voucher_no),as_dict=True)
	
	for p in list_item:
						il.append(frappe._dict({
							'warehouse': p.warehouse ,
							'item_code': p.item_code,
							'qty': flt(p.total_quantity),
							"posting_date": p.posting_date,
							"posting_time": p.posting_time,
							"voucher_no": p.voucher_no,
							"parent_item":p.parent_item,
							'uom': p.uom,
							'batch_no': '',
							'serial_no': '',
							'name': p.sales_invoice_name,
							'target_warehouse': p.target_warehouse,
							'company': p.company,
							'voucher_type': p.voucher_type,
							'allow_zero_valuation': p.allow_zero_valuation_rate,
							'sales_invoice_item': p.get("sales_invoice_item"),
							'dn_detail': p.get("dn_detail"),
							'rate':p.rate,
							'sales_invoice_name':p.sales_invoice_name,
							'incoming_rate': get_incoming_rate({
												"item_code": p.item_code,
												"warehouse": p.warehouse,
												"posting_date": p.posting_date,
												"posting_time": p.posting_time,
												"qty": p.total_quantity,
												"serial_no": '',
												"company": p.company,
												"voucher_type": p.voucher_type,
												"voucher_no": p.voucher_no,
												"allow_zero_valuation": p.allow_zero_valuation
				}, raise_error_if_no_rate=False)

						}))
	
	return il
@frappe.whitelist()	
def update_packed_item():
	try:
		voucher_no=frappe.db.sql(""" select distinct voucher_no from `tabSales Invoice Packed Item`  where is_updated=0 limit 50""",as_dict=True)	
		if voucher_no :
			for inv in voucher_no:	
				var_count=0
				frappe.errprint([inv.voucher_no,"update_packed_item"])
				for d in get_packed_item_list(inv.voucher_no):
					var_count+=1
					new_packed = frappe.new_doc('Packed Item')
					new_packed.warehouse=d.warehouse
					new_packed.parent_item=d.parent_item
					new_packed.item_code=d.item_code
					new_packed.qty=d.qty
					new_packed.rate=d.rate
					new_packed.uom=d.uom
					new_packed.parent=inv.voucher_no
					new_packed.parenttype='Sales Invoice'
					new_packed.parentfield='packed_items'
					bin = get_bin_qty(d.item_code, d.warehouse)
					new_packed.actual_qty = flt(bin.get("actual_qty"))
					new_packed.projected_qty = flt(bin.get("projected_qty"))
					new_packed.parent_detail_docname=d.sales_invoice_name
					new_packed.docstatus=1
					new_packed.incoming_rate=d.incoming_rate
					new_packed.insert()
					new_packed.save()
			
				frappe.db.sql("""update `tabSales Invoice Packed Item` set `is_updated`= 1 where voucher_no='{0}'""".format(inv.voucher_no))
				frappe.db.commit()
	except Exception as e:
		frappe.throw(e)
def get_bin_qty(item, warehouse):
	det = frappe.db.sql("""select actual_qty, projected_qty from `tabBin`
		where item_code = %s and warehouse = %s""", (item, warehouse), as_dict = 1)
	return det and det[0] or frappe._dict()
@frappe.whitelist()	
def update_bundle_double_qty():
		"""create table `tempUpdate Double Qty Invoice` as SELECT sitm.item_code,sitm.parent,0 is_updated from `tabSales Invoice Item` sitm 
				group by sitm.parent,sitm.item_code having count(item_code)>1"""
		try:
			voucher_no=frappe.db.sql(""" select  parent voucher_no,item_code from `tempUpdate Double Qty Invoice`  where is_updated=0 limit 100""",as_dict=True)	
			if voucher_no :
				for inv in voucher_no:	
					inv_item=frappe.db.sql("""select si.name, si.item_code,si.rate,si.parent,si.qty,group_concat(pos.name) reference_pos from `tabSales Invoice Item` si
							inner join(select p.name, pi.item_code,pi.net_rate, consolidated_invoice from `tabPOS Invoice`p inner join `tabPOS Invoice Item` pi on pi.parent=p.name where p.docstatus=1) 
							pos on pos.item_code=si.item_code and pos.consolidated_invoice=si.parent and pos.net_rate=si.rate 
							where si.parent='{0}' and si.item_code='{1}'
							group by si.item_code,si.rate,si.parent;""".format(inv.voucher_no,inv.item_code),as_dict=True)
					for i in inv_item:
							frappe.db.sql("""update `tabSales Invoice Item` set `reference_pos`= '{0}' where name='{1}'""".format(i.reference_pos,i.name))
							frappe.db.commit()
							seleceted_packed_items =[];
							packed_items=[]
							reference_pos=[];pos_invoices=[];pos_invoice_docs=[]				
							reference_pos=i.reference_pos.split(",")
							pos_invoices=[d for d in reference_pos ]
							pos_invoice_docs=[]	
							pos_invoice_docs = [frappe.get_doc("POS Invoice", d) for d in pos_invoices]
							sales_invoice_docs = frappe.get_doc("Sales Invoice", inv.voucher_no) 
							for p_doc in pos_invoice_docs:
								for s_item in  p_doc.get('seleceted_packed_items'):
									
									if s_item.parent_item==i.item_code:
										found = False                            
										for j in seleceted_packed_items:                                                           								
											if (j.item_code == s_item.item_code and j.parent_item == s_item.parent_item and 
											j.parent_detail_docname==i.reference_pos and  j.parent_item==i.item_code ):
												found = True
												j.quantity = j.quantity + s_item.quantity
												
										if not found:  
											s_item.parent_detail_docname=i.reference_pos
											s_item.item_id=i.name
											seleceted_packed_items.append(s_item)
								
							
							for p_item in  sales_invoice_docs.get('packed_items'):
									if(p_item.parent_item==i.item_code and i.name==p_item.parent_detail_docname):
										
										filter_arr= [p for p in seleceted_packed_items if p.item_id == p_item.parent_detail_docname 
										and p.parent_item==p_item.parent_item and p.item_code==p_item.item_code]
										if len(filter_arr)==0:
												
												frappe.db.sql("""delete from `tabPacked Item`  where name='{0}'""".format(p_item.name))
												frappe.db.commit()
										else:
												
												frappe.db.sql("""update `tabPacked Item` set `qty`= {0} where name='{1}'""".format(filter_arr[0].quantity,p_item.name))
												frappe.db.commit()
												
				
					frappe.db.sql("""update `tempUpdate Double Qty Invoice` set `is_updated`= 1 where parent='{0}' and item_code='{1}'""".format(inv.voucher_no,inv.item_code))
					frappe.db.commit()

		except Exception as e:
			frappe.throw(e)
@frappe.whitelist()	
def update_stock_ledger_bundle():
		voucher_no=frappe.db.sql(""" select  distinct parent voucher_no from `tempUpdate Double Qty Invoice`  where is_stock_updated=0 limit 10 """,as_dict=True)	
		if voucher_no :
				for inv in voucher_no:	
					doc=frappe.get_doc("Sales Invoice", inv.voucher_no) 
					frappe.db.sql("""delete from `tabStock Ledger Entry` where voucher_no='{0}'""".format(doc.name))
					frappe.db.commit()

		

					sl_entries = []
					# Loop over items and packed items table
					for d in get_item_list_bundle(doc):
						if frappe.get_cached_value("Item", d.item_code, "is_stock_item") == 1 and flt(d.qty):
							if flt(d.conversion_factor)==0.0:
								d.conversion_factor = get_conversion_factor(d.item_code, d.uom).get("conversion_factor") or 1.0

							# On cancellation or return entry submission, make stock ledger entry for
							# target warehouse first, to update serial no values properly

							if d.warehouse and ((not cint(doc.is_return) and doc.docstatus==1)
								or (cint(doc.is_return) and doc.docstatus==2)):
									sl_entries.append(doc.get_sle_for_source_warehouse(d))

							if d.target_warehouse:
								sl_entries.append(doc.get_sle_for_target_warehouse(d))

							if d.warehouse and ((not cint(doc.is_return) and doc.docstatus==2)
								or (cint(doc.is_return) and doc.docstatus==1)):
									sl_entries.append(doc.get_sle_for_source_warehouse(d))
					
					make_sl_entries_bundle(sl_entries)
					frappe.db.sql("""update `tempUpdate Double Qty Invoice` set `is_stock_updated`= 1 where parent='{0}'""".format(inv.voucher_no))
					frappe.db.commit()
def get_item_list_bundle(self):
		il = []
		for d in self.get("items"):
			if d.qty is None:
				frappe.throw(_("Row {0}: Qty is mandatory").format(d.idx))
			
			if has_product_bundle(d.item_code):
				for p in self.get("packed_items"):
					if p.parent_detail_docname == d.name and p.parent_item == d.item_code:
						# the packing details table's qty is already multiplied with parent's qty
						il.append(frappe._dict({
							'warehouse': p.warehouse or d.warehouse,
							'item_code': p.item_code,
							'qty': flt(p.qty),
							'uom': p.uom,
							'batch_no': cstr(p.batch_no).strip(),
							'serial_no': cstr(p.serial_no).strip(),
							'name': d.name,
							'target_warehouse': p.target_warehouse,
							'company': self.company,
							'voucher_type': self.doctype,
							'allow_zero_valuation': d.allow_zero_valuation_rate,
							'sales_invoice_item': d.get("sales_invoice_item"),
							'dn_detail': d.get("dn_detail"),
							'incoming_rate': p.get("incoming_rate")
						}))
			else:
				il.append(frappe._dict({
					'warehouse': d.warehouse,
					'item_code': d.item_code,
					'qty': d.stock_qty,
					'uom': d.uom,
					'stock_uom': d.stock_uom,
					'conversion_factor': d.conversion_factor,
					'batch_no': cstr(d.get("batch_no")).strip(),
					'serial_no': cstr(d.get("serial_no")).strip(),
					'name': d.name,
					'target_warehouse': d.target_warehouse,
					'company': self.company,
					'voucher_type': self.doctype,
					'allow_zero_valuation': d.allow_zero_valuation_rate,
					'sales_invoice_item': d.get("sales_invoice_item"),
					'dn_detail': d.get("dn_detail"),
					'incoming_rate': d.get("incoming_rate")
				}))
		return il

def has_product_bundle(item_code):
		return frappe.db.sql("""select name from `tabProduct Bundle`
			where new_item_code=%s and docstatus != 2""", item_code)
def make_sl_entries_bundle(sl_entries, allow_negative_stock=False,
		via_landed_cost_voucher=False):
		from erpnext.stock.stock_ledger import make_sl_entries
		make_sl_entries(sl_entries, allow_negative_stock, via_landed_cost_voucher)


@frappe.whitelist()
def make_gl_entries_bundle(gl_entries=None, from_repost=False):
		voucher_no=frappe.db.sql(""" select  distinct parent voucher_no from `tempUpdate Double Qty Invoice`  where is_gl_updated=0 """,as_dict=True)	
		if voucher_no :
			for inv in voucher_no:	
				doc=frappe.get_doc("Sales Invoice", inv.voucher_no) 
				from erpnext.accounts.general_ledger import make_gl_entries, make_reverse_gl_entries

				auto_accounting_for_stock = erpnext.is_perpetual_inventory_enabled(doc.company)
				if not gl_entries:
					gl_entries = doc.get_gl_entries()

				if gl_entries:
					# if POS and amount is written off, updating outstanding amt after posting all gl entries
					update_outstanding = "No" if (cint(doc.is_pos) or doc.write_off_account or
						cint(doc.redeem_loyalty_points)) else "Yes"

					if doc.docstatus == 1:
						make_reverse_gl_entries(voucher_type=doc.doctype, voucher_no=doc.name)
						make_gl_entries(gl_entries, update_outstanding=update_outstanding, merge_entries=False, from_repost=from_repost)
					
						

					if update_outstanding == "No":
						from erpnext.accounts.doctype.gl_entry.gl_entry import update_outstanding_amt
						update_outstanding_amt(doc.debit_to, "Customer", doc.customer,
							doc.doctype, doc.return_against if cint(doc.is_return) and doc.return_against else doc.name)

				elif doc.docstatus == 2 and cint(doc.update_stock) \
					and cint(auto_accounting_for_stock):
						make_reverse_gl_entries(voucher_type=doc.doctype, voucher_no=doc.name)
				frappe.db.sql("""update `tempUpdate Double Qty Invoice` set `is_gl_updated`= 1 where parent='{0}'""".format(inv.voucher_no))
				frappe.db.commit()