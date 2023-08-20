# Copyright (c) 2013, aavu and contributors
# For license information, please see license.txt

# import frappe


from __future__ import unicode_literals
from tokenize import String
import frappe, erpnext
from frappe import _
from frappe.utils import flt, cstr
from frappe.model.meta import get_field_precision
from frappe.utils.xlsxutils import handle_html
# from erpnext.accounts.report.sales_register.sales_register import get_mode_of_payments
from erpnext.selling.report.item_wise_sales_history.item_wise_sales_history import get_item_details, get_customer_details
import datetime as dt
from datetime import datetime
def execute(filters=None):
	return _execute(filters)

def _execute(filters=None, additional_table_columns=None, additional_query_columns=None):
	if not filters: filters = {}
	columns = get_columns(additional_table_columns, filters)
	
	fromdate=datetime.combine(datetime.strptime(str(filters.from_date), '%Y-%m-%d'), datetime.strptime(str(filters.posting_time),"%H:%M:%S").time())
	todate=datetime.combine(datetime.strptime(str(filters.to_date), '%Y-%m-%d'), datetime.strptime(str(filters.posting_timeto),"%H:%M:%S").time())
	filters["fromdate"] = fromdate
	filters["todate"] = todate
	frappe.errprint(filters)
	company_currency = frappe.get_cached_value('Company',  filters.get('company'),  'default_currency')

	item_list = get_items(filters, additional_query_columns)
	if item_list:
		itemised_tax, tax_columns = get_tax_accounts(item_list, columns, company_currency)

	mode_of_payments = get_mode_of_payments(set([d.parent for d in item_list]))
	so_dn_map = get_delivery_notes_against_sales_order(item_list)

	data = []
	total_row_map = {}
	skip_total_row = 0
	prev_group_by_value = ''

	if filters.get('group_by'):
		grand_total = get_grand_total(filters, 'POS Invoice')

	customer_details = get_customer_details()
	item_details = get_item_details()

	for d in item_list:
		customer_record = customer_details.get(d.customer)
		item_record = item_details.get(d.item_code)

		delivery_note = None
		if d.delivery_note:
			delivery_note = d.delivery_note
		elif d.so_detail:
			delivery_note = ", ".join(so_dn_map.get(d.so_detail, []))

		if not delivery_note and d.update_stock:
			delivery_note = d.parent

		row = {
			'posting_date': d.posting_date,
			'posting_time':d.posting_time,
			'owner':d.owner,
			'invoice': d.parent,
			'item_group': item_record.item_group if item_record else d.item_group,
			'itemgroup': d.itemgrp,
			'pos_profile':d.pos_profile,
			'item_code': d.item_code,
			'item_name': item_record.item_name if item_record else d.item_name,
			'customer_name': customer_record.customer_name,
            'applied_coupen':d.applied_coupen,
            'item_discount':d.item_discount
			
		}

		if additional_query_columns:
			for col in additional_query_columns:
				row.update({
					col: d.get(col)
				})

		row.update({
			'stock_qty': d.stock_qty,
			'mode_of_payment': ", ".join(mode_of_payments.get(d.parent, [])),
			
		})

		if d.stock_uom != d.uom and d.stock_qty:
			row.update({
				'rate': (d.base_net_rate * d.qty)/d.stock_qty,
				'amount': d.base_net_amount
			})
		else:
			row.update({
				'rate': d.base_net_rate,
				'amount': d.base_net_amount
			})
		row.update({
			'discount_amount': d.discount_amount
			
		})
		total_tax = 0
		for tax in tax_columns:
			item_tax = itemised_tax.get(d.name, {}).get(tax, {})
			row.update({
				frappe.scrub(tax + ' Rate'): item_tax.get('tax_rate', 0),
				frappe.scrub(tax + ' Amount'): item_tax.get('tax_amount', 0),
			})
			total_tax += flt(item_tax.get('tax_amount'))

		row.update({
			'total_tax': total_tax,
			'total': d.base_net_amount + total_tax,
			'currency': company_currency
		})

		if filters.get('group_by'):
			row.update({'percent_gt': flt(row['total']/grand_total) * 100})
			group_by_field, subtotal_display_field = get_group_by_and_display_fields(filters)
			data, prev_group_by_value = add_total_row(data, filters, prev_group_by_value, d, total_row_map,
				group_by_field, subtotal_display_field, grand_total, tax_columns)
			add_sub_total_row(row, total_row_map, d.get(group_by_field, ''), tax_columns)

		data.append(row)

	if filters.get('group_by') and item_list:
		total_row = total_row_map.get(prev_group_by_value or d.get('item_name'))
		total_row['percent_gt'] = flt(total_row['total']/grand_total * 100)
		data.append(total_row)
		data.append({})
		add_sub_total_row(total_row, total_row_map, 'total_row', tax_columns)
		data.append(total_row_map.get('total_row'))
		skip_total_row = 1

	return columns, data, None, None, None, skip_total_row

def get_columns(additional_table_columns, filters):
	columns = []

	if filters.get('group_by') != ('Item'):
		columns.extend(
			[
				{
			'label': _('Posting Date'),
			'fieldname': 'posting_date',
			'fieldtype': 'Date',
			'width': 120
		},
		{
			'label': _('Posting Time'),
			'fieldname': 'posting_time',
			'fieldtype': 'Time',
			'width': 120
		},
		{
			'label': _('POS Profile'),
			'fieldname': 'pos_profile',
			'fieldtype': 'Data',
			'width': 150
		},
		{
			'label': _('User Name'),
			'fieldname': 'owner',
			'fieldtype': 'Data',
			'width': 120
		},
		
		{
			'label': _('Invoice'),
			'fieldname': 'invoice',
			'fieldtype': 'Link',
			'options': 'POS Invoice',
			'width': 120
		},
		{
				'label': _('Item Group'),
				'fieldname': 'itemgroup',
				'fieldtype': 'Link',
				'options': 'Item Group',
				'width': 120
			}
				
				
			]
		)

	if filters.get('group_by') not in ('Item', 'Item Group'):
		columns.extend([
			
			{
				'label': _('Item Sub Group'),
				'fieldname': 'item_group',
				'fieldtype': 'Link',
				'options': 'Item Group',
				'width': 120
			}
			
		])

	columns.extend([
		{
					'label': _('Item Name'),
					'fieldname': 'item_name',
					'fieldtype': 'Data',
					'width': 120
				}
		
		
	])

	

	if filters.get('group_by') not in ('Customer', 'Customer Group'):
		columns.extend([
			
			{
				'label': _('Customer Name'),
				'fieldname': 'customer_name',
				'fieldtype': 'Data',
				'width': 120
			}
		])

	if additional_table_columns:
		columns += additional_table_columns

	

	

	columns += [
		
		
		
		{
			'label': _('Stock Qty'),
			'fieldname': 'stock_qty',
			'fieldtype': 'Float',
			'width': 100
		},
		{
			'label': _('Mode Of Payment'),
			'fieldname': 'mode_of_payment',
			'fieldtype': 'Data',
			'width': 120
		},
		{
			'label': _('Rate'),
			'fieldname': 'rate',
			'fieldtype': 'Float',
			'options': 'currency',
			'width': 100
		},
		{
			'label': _('Amount'),
			'fieldname': 'amount',
			'fieldtype': 'Currency',
			'options': 'currency',
			'width': 100
		},
		{
			'label': _('Discount'),
			'fieldname': 'discount_amount',
			'fieldtype': 'Currency',
			'options': 'currency',
			'width': 100
		},
        {
			'label': _('Coupon'),
			'fieldname': 'applied_coupen',
			'fieldtype': 'Data',
			'width': 100
		},
        {
			'label': _('Coupon Discount'),
			'fieldname': 'item_discount',
			'fieldtype': 'Currency',
			'options': 'currency',
			'width': 100
		}
	]

	if filters.get('group_by'):
		columns.append({
			'label': _('% Of Grand Total'),
			'fieldname': 'percent_gt',
			'fieldtype': 'Float',
			'width': 80
		})

	return columns

def get_conditions(filters):
	conditions = ""
	
	for opts in (
		
		("company", " and company=%(company)s"),
		("customer", " and `tabPOS Invoice`.customer = %(customer)s"),
		("item_code", " and `tabSatabPOSles Invoice Item`.item_code = %(item_code)s"),
		("from_date", " and `tabPOS Invoice`.posting_date>=%(from_date)s"),       
		("to_date", " and `tabPOS Invoice`.posting_date<=%(to_date)s"),
		("posting_time", " and `tabPOS Invoice`.creation >= %(fromdate)s"),
		("posting_timeto", " and `tabPOS Invoice`.creation <= %(todate)s")
	   ):
			if filters.get(opts[0]):
				conditions += opts[1]
	frappe.errprint(conditions)
	if filters.get("mode_of_payment"):
		conditions += """ and exists(select name from `tabSales Invoice Payment`
			where parent=`tabPOS Invoice`.name
				and ifnull(`tabSales Invoice Payment`.mode_of_payment, '') = %(mode_of_payment)s)"""

	if filters.get("warehouse"):
		conditions +=  """and ifnull(`tabPOS Invoice Item`.warehouse, '') = %(warehouse)s"""


	if filters.get("brand"):
		conditions +=  """and ifnull(`tabPOS Invoice Item`.brand, '') = %(brand)s"""

	if filters.get("item_group"):
		conditions +=  """and ifnull(`tabSaltabPOSes Invoice Item`.item_group, '') = %(item_group)s"""

	if not filters.get("group_by"):
		conditions += "ORDER BY `tabPOS Invoice`.posting_date asc,`tabPOS Invoice Item`.parent asc, `tabPOS Invoice Item`.item_group desc"
	else:
		conditions += get_group_by_conditions(filters, 'POS Invoice')

	return conditions

def get_group_by_conditions(filters, doctype):
	if filters.get("group_by") == 'Invoice':
		return "ORDER BY `tab{0} Item`.parent desc".format(doctype)
	elif filters.get("group_by") == 'Item':
		return "ORDER BY `tab{0} Item`.`item_code`".format(doctype)
	elif filters.get("group_by") == 'Item Group':
		return "ORDER BY `tab{0} Item`.{1}".format(doctype, frappe.scrub(filters.get('group_by')))
	elif filters.get("group_by") in ('Customer', 'Customer Group', 'Territory', 'Supplier'):
		return "ORDER BY `tab{0}`.{1}".format(doctype, frappe.scrub(filters.get('group_by')))

def get_items(filters, additional_query_columns):
	conditions = get_conditions(filters)

	if additional_query_columns:
		additional_query_columns = ', ' + ', '.join(additional_query_columns)
	else:
		additional_query_columns = ''
	
	return frappe.db.sql("""
		select
			`tabPOS Invoice Item`.name, `tabPOS Invoice Item`.parent,`tabUser`.full_name owner ,`tabPOS Invoice`.pos_profile,
			`tabPOS Invoice`.posting_date, `tabPOS Invoice`.debit_to,posting_time,
			'' unrealized_profit_loss_account,
			`tabPOS Invoice`.project, `tabPOS Invoice`.customer, `tabPOS Invoice`.remarks,
			`tabPOS Invoice`.territory, `tabPOS Invoice`.company, `tabPOS Invoice`.base_net_total,
			`tabPOS Invoice Item`.item_code, `tabPOS Invoice Item`.description,
			`tabPOS Invoice Item`.`item_name`, `tabPOS Invoice Item`.`item_group`,
			`tabPOS Invoice Item`.sales_order, `tabPOS Invoice Item`.delivery_note,
			`tabPOS Invoice Item`.income_account, `tabPOS Invoice Item`.cost_center,
			`tabPOS Invoice Item`.stock_qty, `tabPOS Invoice Item`.stock_uom,
			`tabPOS Invoice Item`.base_net_rate, `tabPOS Invoice Item`.base_net_amount, `tabPOS Invoice`.discount_amount, `tabPOS Invoice`.applied_coupen,`tabPOS Invoice Item`.discount_amount item_discount,
			`tabPOS Invoice`.customer_name, `tabPOS Invoice`.customer_group, `tabPOS Invoice Item`.so_detail,
			`tabPOS Invoice`.update_stock, `tabPOS Invoice Item`.uom, `tabPOS Invoice Item`.qty,ifnull(`tabItem Group`.parent,`tabItem Group`.name) itemgrp  {0}
		from `tabPOS Invoice` inner join tabUser on `tabPOS Invoice`.owner = tabUser.name, `tabPOS Invoice Item` inner join `tabItem Group` on `tabPOS Invoice Item`.item_group = `tabItem Group`.name
		
		where `tabPOS Invoice`.name = `tabPOS Invoice Item`.parent
			and `tabPOS Invoice`.docstatus = 1 {1} 
		""".format(additional_query_columns or '', conditions), filters, as_dict=1) #nosec

def get_delivery_notes_against_sales_order(item_list):
	so_dn_map = frappe._dict()
	so_item_rows = list(set([d.so_detail for d in item_list]))

	if so_item_rows:
		delivery_notes = frappe.db.sql("""
			select parent, so_detail
			from `tabDelivery Note Item`
			where docstatus=1 and so_detail in (%s)
			group by so_detail, parent
		""" % (', '.join(['%s']*len(so_item_rows))), tuple(so_item_rows), as_dict=1)

		for dn in delivery_notes:
			so_dn_map.setdefault(dn.so_detail, []).append(dn.parent)

	return so_dn_map

def get_grand_total(filters, doctype):

	return frappe.db.sql(""" SELECT
		SUM(`tab{0}`.base_grand_total)
		FROM `tab{0}`
		WHERE `tab{0}`.docstatus = 1
		and posting_date between %s and %s
	""".format(doctype), (filters.get('from_date'), filters.get('to_date')))[0][0] #nosec

def get_deducted_taxes():
	return frappe.db.sql_list("select name from `tabPurchase Taxes and Charges` where add_deduct_tax = 'Deduct'")

def get_tax_accounts(item_list, columns, company_currency,
		doctype='POS Invoice', tax_doctype='Sales Taxes and Charges'):
	import json
	item_row_map = {}
	tax_columns = []
	invoice_item_row = {}
	itemised_tax = {}

	tax_amount_precision = get_field_precision(frappe.get_meta(tax_doctype).get_field('tax_amount'),
		currency=company_currency) or 2

	for d in item_list:
		invoice_item_row.setdefault(d.parent, []).append(d)
		item_row_map.setdefault(d.parent, {}).setdefault(d.item_code or d.item_name, []).append(d)

	conditions = ""
	if doctype == "Purchase Invoice":
		conditions = " and category in ('Total', 'Valuation and Total') and base_tax_amount_after_discount_amount != 0"

	deducted_tax = get_deducted_taxes()
	tax_details = frappe.db.sql("""
		select
			name, parent, description, item_wise_tax_detail,
			charge_type, base_tax_amount_after_discount_amount
		from `tab%s`
		where
			parenttype = %s and docstatus = 1
			and (description is not null and description != '')
			and parent in (%s)
			%s
		order by description
	""" % (tax_doctype, '%s', ', '.join(['%s']*len(invoice_item_row)), conditions),
		tuple([doctype] + list(invoice_item_row)))

	for name, parent, description, item_wise_tax_detail, charge_type, tax_amount in tax_details:
		description = handle_html(description)
		if description not in tax_columns and tax_amount:
			# as description is text editor earlier and markup can break the column convention in reports
			tax_columns.append(description)

		if item_wise_tax_detail:
			try:
				item_wise_tax_detail = json.loads(item_wise_tax_detail)

				for item_code, tax_data in item_wise_tax_detail.items():
					itemised_tax.setdefault(item_code, frappe._dict())

					if isinstance(tax_data, list):
						tax_rate, tax_amount = tax_data
					else:
						tax_rate = tax_data
						tax_amount = 0

					if charge_type == 'Actual' and not tax_rate:
						tax_rate = 'NA'

					item_net_amount = sum([flt(d.base_net_amount)
						for d in item_row_map.get(parent, {}).get(item_code, [])])

					for d in item_row_map.get(parent, {}).get(item_code, []):
						item_tax_amount = flt((tax_amount * d.base_net_amount) / item_net_amount) \
							if item_net_amount else 0
						if item_tax_amount:
							tax_value = flt(item_tax_amount, tax_amount_precision)
							tax_value = (tax_value * -1
								if (doctype == 'Purchase Invoice' and name in deducted_tax) else tax_value)

							itemised_tax.setdefault(d.name, {})[description] = frappe._dict({
								'tax_rate': tax_rate,
								'tax_amount': tax_value
							})

			except ValueError:
				continue
		elif charge_type == 'Actual' and tax_amount:
			for d in invoice_item_row.get(parent, []):
				itemised_tax.setdefault(d.name, {})[description] = frappe._dict({
					'tax_rate': 'NA',
					'tax_amount': flt((tax_amount * d.base_net_amount) / d.base_net_total,
						tax_amount_precision)
				})

	tax_columns.sort()
	for desc in tax_columns:
		columns.append({
			'label': _(desc + ' Rate'),
			'fieldname': frappe.scrub(desc + ' Rate'),
			'fieldtype': 'Float',
			'width': 100
		})

		columns.append({
			'label': _(desc + ' Amount'),
			'fieldname': frappe.scrub(desc + ' Amount'),
			'fieldtype': 'Currency',
			'options': 'currency',
			'width': 100
		})

	columns += [
		{
			'label': _('Total Tax'),
			'fieldname': 'total_tax',
			'fieldtype': 'Currency',
			'options': 'currency',
			'width': 100
		},
		{
			'label': _('Total'),
			'fieldname': 'total',
			'fieldtype': 'Currency',
			'options': 'currency',
			'width': 100
		},
		{
			'fieldname': 'currency',
			'label': _('Currency'),
			'fieldtype': 'Currency',
			'width': 80,
			'hidden': 1
		}
	]

	return itemised_tax, tax_columns

def add_total_row(data, filters, prev_group_by_value, item, total_row_map,
	group_by_field, subtotal_display_field, grand_total, tax_columns):
	if prev_group_by_value != item.get(group_by_field, ''):
		if prev_group_by_value:
			total_row = total_row_map.get(prev_group_by_value)
			data.append(total_row)
			data.append({})
			add_sub_total_row(total_row, total_row_map, 'total_row', tax_columns)

		prev_group_by_value = item.get(group_by_field, '')

		total_row_map.setdefault(item.get(group_by_field, ''), {
			subtotal_display_field: get_display_value(filters, group_by_field, item),
			'stock_qty': 0.0,
			'amount': 0.0,
			'bold': 1,
			'total_tax': 0.0,
			'total': 0.0,
			'percent_gt': 0.0
		})

		total_row_map.setdefault('total_row', {
			subtotal_display_field: 'Total',
			'stock_qty': 0.0,
			'amount': 0.0,
			'bold': 1,
			'total_tax': 0.0,
			'total': 0.0,
			'percent_gt': 0.0
		})

	return data, prev_group_by_value

def get_display_value(filters, group_by_field, item):
	if filters.get('group_by') == 'Item':
		if item.get('item_code') != item.get('item_name'):
			value =  cstr(item.get('item_code')) + "<br><br>" + \
			"<span style='font-weight: normal'>" + cstr(item.get('item_name')) + "</span>"
		else:
			value =  item.get('item_code', '')
	elif filters.get('group_by') in ('Customer', 'Supplier'):
		party = frappe.scrub(filters.get('group_by'))
		if item.get(party) != item.get(party+'_name'):
			value = item.get(party) + "<br><br>" + \
			"<span style='font-weight: normal'>" + item.get(party+'_name') + "</span>"
		else:
			value =  item.get(party)
	else:
		value = item.get(group_by_field)

	return value

def get_group_by_and_display_fields(filters):
	if filters.get('group_by') == 'Item':
		group_by_field = 'item_code'
		subtotal_display_field = 'invoice'
	elif filters.get('group_by') == 'Invoice':
		group_by_field = 'parent'
		subtotal_display_field = 'item_code'
	else:
		group_by_field = frappe.scrub(filters.get('group_by'))
		subtotal_display_field = 'item_code'

	return group_by_field, subtotal_display_field

def add_sub_total_row(item, total_row_map, group_by_value, tax_columns):
	total_row = total_row_map.get(group_by_value)
	total_row['stock_qty'] += item['stock_qty']
	total_row['amount'] += item['amount']
	total_row['total_tax'] += item['total_tax']
	total_row['total'] += item['total']
	total_row['percent_gt'] += item['percent_gt']

	for tax in tax_columns:
		total_row.setdefault(frappe.scrub(tax + ' Amount'), 0.0)
		total_row[frappe.scrub(tax + ' Amount')] += flt(item[frappe.scrub(tax + ' Amount')])

def get_mode_of_payments(invoice_list):
	mode_of_payments = {}
	if invoice_list:
		inv_mop = frappe.db.sql("""select parent, mode_of_payment
			from `tabSales Invoice Payment` where amount>0 and parent in (%s) group by parent, mode_of_payment""" %
			', '.join(['%s']*len(invoice_list)), tuple(invoice_list), as_dict=1)

		for d in inv_mop:
			mode_of_payments.setdefault(d.parent, []).append(d.mode_of_payment)

	return mode_of_payments

