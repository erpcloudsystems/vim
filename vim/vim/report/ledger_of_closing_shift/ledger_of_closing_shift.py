# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _

def execute(filters=None):	
	if not filters:
		return [], []
	columns = get_columns(filters)

	res = get_result(filters)
	## removed opening row
	
	data=[]
	frappe.errprint([len(res),"length"])
	for i in res:
		inv=i["voucher_no"]
		data.append({
				"posting_date":i.posting_date,
				"account":i.account ,
				"debit" : i.debit,
				"credit" : i.credit,
				"balance" : i.balance ,
				"voucher_no" : i.voucher_no ,
				"project" : i.project,
				"party_type":i.party_type,
				"party":i.party,
				"voucher_type":i.voucher_type,
				"cost_center":i.cost_center,
				"party_type":i.party_type,
				"against_voucher_type":i.against_voucher_type,
				"against_voucher":i.against_voucher,
				"remarks":i.remarks,
				"against":i.against,
				"owner":i.owner ,
				"pos_opening_entry":i.pos_opening_entry ,
				"sales_order":i.sales_order ,
				"period_end_date":i.period_end_date ,
				"period_start_date":i.period_start_date ,
				"pos_closing_entry":i.closing 
			})
		invc=inv
	chk=get_result_as_list(data,filters)	
	return columns, data



def get_result(filters):
	if  filters.get('closing_id') and not filters.get('against_account'):
		condition="and cl.name='{0}' ".format(filters.get('closing_id'))
	elif  filters.get('against_account') and not  filters.get('closing_id'):
		condition=" and gl.against='{0}'".format(filters.get('against_account'))
	elif filters and  filters.get('closing_id') and filters.get('against_account'):
		condition="and gl.against='{0}' and cl.name='{1}' ".format(filters.get('against_account'),filters.get('closing_id'))
	else:	
		condition=""
	sql = """				
select distinct gl.posting_date , gl.voucher_no , gl.account, gl.credit,gl.debit,gl.voucher_no,gl.voucher_type,gl.against,gl.party,gl.party,gl.against_voucher,gl.against_voucher_type,gl.project,gl.cost_center,gl.remarks,gl.party_type,
cl.name as closing,cl.owner,cl.pos_opening_entry,cl.period_start_date,period_end_date,pos.sales_order from `tabPOS Closing Entry` cl 
inner join `tabPOS Invoice Reference` ir on ir.parent = cl.name 
inner join `tabPOS Invoice` pos on pos.name = ir.pos_invoice 
inner join `tabGL Entry` gl on gl.voucher_no = pos.consolidated_invoice and gl.voucher_type = 'Sales Invoice'
where gl.posting_date BETWEEN '{1}' and '{2}' and ir.docstatus=1 {0}
	""".format(condition,filters.get('from_date'),filters.get('to_date'))
	raw =frappe.db.sql(sql,as_dict=1)
	frappe.errprint(sql)
	return raw




def get_result_as_list(data, filters):
	balance, balance_in_account_currency = 0, 0
	# inv_details = get_supplier_invoice_details()

	for d in data:
		if not d.get('posting_date'):
			balance, balance_in_account_currency = 0, 0

		balance = get_balance(d, balance, 'debit', 'credit')
		d['balance'] = balance

	

	return data


def get_balance(row, balance, debit_field, credit_field):
	
	balance += (row.get(debit_field, 0) -  row.get(credit_field, 0))
	return balance



def get_columns(filters):


	columns = [
		{
			"label": _("Posting Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 120
		},
		{
			"label": _("Account"),
			"fieldname": "account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 180
		},
		{
			"label": _("Debit SAR"),
			"fieldname": "debit",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("Credit (SAR)"),
			"fieldname": "credit",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("Balance (SAR)"),
			"fieldname": "balance",
			"fieldtype": "Float",
			"width": 130
		},
			{
			"label": _("Voucher Type"),
			"fieldname": "voucher_type",
			"width": 120
		},
		{
			"label": _("Voucher No"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 180
		},
		{
			'label': _('Booking ID'),
			'fieldname': "sales_order",
			'fieldtype': 'Link',
			'options':'Sales Order',
			'width': 150,
		},
				{
	 		'fieldname': "pos_opening_entry",
			'label':('POS opening entry ID'),
			'fieldtype': 'Data',
			'width': 200
		},
		
		{
	 		'fieldname': "period_start_date",
			'label':('POS opening Date & time'),
			'fieldtype': 'Data',
			'width': 170
		},
		{
	 		'fieldname': "owner",
			'label':('Cashier ID'),
			'fieldtype': 'Data',
			'width': 150
		},
			{
	 		'fieldname': "pos_closing_entry" ,
			'label':('POS closing ID'),
			'fieldtype': 'Data',
			'width': 200
		},
		{
	 		'fieldname':"period_end_date",
			'label':('POS closing Date & time'),
			'fieldtype': 'Data',
			'width': 170
		},
	]

	columns.extend([
		{
			"label": _("Against Account"),
			"fieldname": "against",
			"width": 170
		},
		{
			"label": _("Party Type"),
			"fieldname": "party_type",
			"width": 100
		},
		{
			"label": _("Party"),
			"fieldname": "party",
			"width": 100
		},
		{
			"label": _("Project"),
			"options": "Project",
			"fieldname": "project",
			"width": 100
		}
	])



	columns.extend([
		{
			"label": _("Cost Center"),
			"options": "Cost Center",
			"fieldname": "cost_center",
			"width":120
		},
		{
			"label": _("Against Voucher Type"),
			"fieldname": "against_voucher_type",
			"width": 120
		},
		{
			"label": _("Against Voucher"),
			"fieldname": "against_voucher",
			"fieldtype": "Dynamic Link",
			"options": "against_voucher_type",
			"width": 120
		},
		# {
		# 	"label": _("Supplier Invoice No"),
		# 	"fieldname": "bill_no",
		# 	"fieldtype": "Data",
		# 	"width": 120
		# },
		{
			"label": _("Remarks"),
			"fieldname": "remarks",
			"width": 400
		}
	])

	return columns



