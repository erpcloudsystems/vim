# Copyright (c) 2013, aavu and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _

def execute(filters=None):
	if not filters:
		return [], []		
	if  filters.get('cashier') and not filters.get('closing_id'):
		validate_filters(filters)
		condition="and cl.owner='{0}' ".format(filters.get('cashier'))
	elif  filters.get('closing_id') and not  filters.get('cashier'):
		condition=" and cl.name='{0}'".format(filters.get('closing_id'))
	elif filters and  filters.get('closing_id') and filters.get('cashier'):
		condition="and cl.owner='{0}' and cl.name='{1}' ".format(filters.get('cashier'),filters.get('closing_id'))
	else:	
		condition=""
	sql = """				
		SELECT distinct inv.name as invoice,pos.total as booking_amt,pos.name as pos,period_start_date,period_end_date,
		pos_opening_entry,cl.name as pos_closing_entry,cl.owner,sales_order as_bookinf_id,pos.posting_date as date,
		pos.customer,pos.cost_center,pos.paid_amount,pos.change_amount,pos.debit_to,inv.grand_total,inv.rounding_adjustment,inv.rounded_total,
        inv.posting_date,pos.total_advance,inv.total_taxes_and_charges,pos.grand_total as po_amt
		from `tabPOS Closing Entry` cl 
		inner join `tabPOS Invoice Reference` ir on ir.parent = cl.name 
		inner join `tabPOS Invoice` pos on pos.name = ir.pos_invoice 
		inner join `tabSales Invoice` inv on inv.name = pos.consolidated_invoice 
		where  pos.docstatus=1 and cl.docstatus=1 {0} order by 1
	""".format(condition)
	raw =frappe.db.sql(sql,as_dict=1)
	result=[]
	frappe.errprint(raw)
	
	if len(raw)!=0:
		additional_table_columns=get_pament_mode(filters)
		columns = get_columns(additional_table_columns)
		invoice_leap=""
		payment_rw=get_pament_amt(filters)
		frappe.errprint(payment_rw)
		net=0
		for idx, i in enumerate(raw):	
			payment={}
			for val in payment_rw:
				if val.pos==i.pos:
					payment[val.mode_of_payment]=val.amount
					if val.type=="Cash":
						net=val.amount


			result.append({
						"01#Invoice:Link/Sales Invoice:200":i.invoice if invoice_leap=="" or invoice_leap !=i.invoice else "",
						"02#Posting Date:Date:200" :i.posting_date if invoice_leap=="" or invoice_leap !=i.invoice else "",
						"03#Grand Total:Float:200" :i.grand_total if invoice_leap=="" or invoice_leap !=i.invoice else "" ,
						"04#Tax Amount:Float:200" : i.total_taxes_and_charges  if invoice_leap=="" or invoice_leap !=i.invoice else "",
						"05#Rounding Adjustment:Float:200" :i.rounding_adjustment if invoice_leap=="" or invoice_leap !=i.invoice else "" ,
						"06#Rounding Total:Float:200" : i.rounded_total if invoice_leap=="" or invoice_leap !=i.invoice else "",
						"07#Advance:Float:200" : i.total_advance ,
						"08#Booking Id:Link/Sales Order:200" : i.as_bookinf_id,
						"09#Booking amt:Float:200" :i.booking_amt if  i.as_bookinf_id else "" ,
						"10#POS:Link/POS Invoice:200" : i.pos,
						"11#Date:Date:200" : i.date,
						"12#Customer:Link/Customer:200" : i.customer,
						"13#Cost Center:Link/Cost Center:200" : i.cost_center,
						"14#POS Amt:Float:200" : i.po_amt,
						"15#Change Amt:Float:200" : i.change_amount,
						"16#Opening Entry date:Data:200" : i.period_start_date,
						"17#Closing Entry time:Data:200" :i.period_end_date,
						"18#Cashier ID:Data:200" : i.owner,
						"19#Closing ID:Data:200" :i.pos_closing_entry,
						"20#Opening ID:Data:200" :i.pos_opening_entry,
						"21#Recieved:Data:200" :i.paid_amount,
						"22#Account debited:Data:200" :i.debit_to,
						"net":float(net)-float(i.change_amount)
				})
			for col in additional_table_columns:
				result[-1][col.mode_of_payment]=0.00		
			for key in payment :
				result[-1][key] = (payment[key])
			invoice_leap=i.invoice
		frappe.errprint(result)
		return columns, result
	return [],[]



def validate_filters(filters):
	if not filters.get("closing_id"):
		frappe.throw(_("{0} is mandatory").format(_("Closing ID")))


def get_pament_mode(filters):
	if  filters and  filters.get('cashier'):
		condition="where p.owner='{0}'".format(filters.get('cashier'))
	elif  filters and  filters.get('closing_id'):
		condition="where p.name='{0}'".format(filters.get('closing_id'))
	elif filters and filters.get('closing_id') and filters.get('cashier'):
		condition="where p.owner='{0}' and p.name='{1}' ".format(filters.get('cashier'),filters.get('closing_id'))
	else:	
		condition=""

	sql = """select distinct mode_of_payment  from  `tabPOS Closing Entry` p inner join  `tabPOS Closing Entry Detail` c on c.parent=p.name {0} order by 1 """.format(condition)
	data=frappe.db.sql(sql,as_dict=1)
	return data

def get_pament_amt(filters):
	if  filters.get('cashier') and not filters.get('closing_id'):
		validate_filters(filters)
		condition="and cl.owner='{0}' ".format(filters.get('cashier'))
	elif  filters.get('closing_id') and not  filters.get('cashier'):
		condition=" and cl.name='{0}'".format(filters.get('closing_id'))
	elif filters and  filters.get('closing_id') and filters.get('cashier'):
		condition="and cl.owner='{0}' and cl.name='{1}' ".format(filters.get('cashier'),filters.get('closing_id'))
	else:	
		condition=""
	sql = """select type,mode_of_payment,amount,parent as pos from  `tabSales Invoice Payment` where parent in (SELECT pos.name from `tabPOS Closing Entry` cl inner join `tabPOS Invoice Reference` ir on ir.parent = cl.name inner join `tabPOS Invoice` pos on pos.name = ir.pos_invoice inner join `tabSales Invoice` inv on inv.name = pos.consolidated_invoice where  pos.docstatus=1 and cl.docstatus=1  {0} order by 1) """.format(condition)
	data=frappe.db.sql(sql,as_dict=1)
	return data

def get_columns(additional_table_columns):
	columns=[]

	columns+= [
		{
	 		'fieldname': '01#Invoice:Link/Sales Invoice:200',
            'label':('Sales Inoive No.'),
            'fieldtype': 'Link',
            'options': 'Sales Invoice',
			'width': 170
        },
        {
            'fieldname': "02#Posting Date:Date:200",
            'label': ('Posting Date'),
            'fieldtype': 'Date',
        },
		{
			'label': _('Grand Total'),
			'fieldname': "03#Grand Total:Float:200",
			'fieldtype': 'Float',
			'options': 'currency',
			'width': 120
		},
		{
			'label': _('Tax Amount'),
			'fieldname':  "04#Tax Amount:Float:200",
			'fieldtype': 'Float',
			'options': 'currency',
			'width': 120
		},
			{
			'label': _('Round adjustment'),
			'fieldname':"05#Rounding Adjustment:Float:200",
			'fieldtype': 'Float',
			'options': 'currency',
			'width': 120
		},
		{
			'label': _('Rounded Total'),
			'fieldname': "06#Rounding Total:Float:200",
			'fieldtype': 'Float',
			'options': 'currency',
			'width': 120
		},
			{
			'label': _('Booking ID'),
			'fieldname': "08#Booking Id:Link/Sales Order:200",
			'fieldtype': 'Link',
			'options':'Sales Order',
			'width': 150,
		},
		{
			'label': _('Booking amount'),
			'fieldname': "09#Booking amt:Float:200",
			'fieldtype': 'Float',
			'options': 'currency',
			'width': 120,
	
		},
		{
			'label': _('Advance Amount'),
			'fieldname':"07#Advance:Float:200",
			'fieldtype': 'Float',
			'options': 'currency',
			'width': 120
		},
		{
			'fieldname':"22#Account debited:Data:200",
            'label': ('Account debited'),
            'fieldtype': 'Data',
			'width':160

		},
		
		{
	 		'fieldname': "10#POS:Link/POS Invoice:200" ,
            'label':('POS'),
            'fieldtype': 'Link',
            'options': 'POS Invoice',
			'width': 200
        },
		  {
            'fieldname': "11#Date:Date:200",
            'label': ('Date'),
            'fieldtype': 'Date',
			'width': 120

        },

		{
	 		'fieldname': "12#Customer:Link/Customer:200",
            'label':('Customer'),
            'fieldtype': 'Link',
            'options': 'Customer',
			'width': 150
        },
			{
	 		'fieldname': "13#Cost Center:Link/Cost Center:200",
            'label':('Cost Center'),
            'fieldtype': 'Link',
            'options': 'Cost Center',
			'width': 150
        },
		{
	 		'fieldname': "14#POS Amt:Float:200",
            'label':('Pos Amt'),
            'fieldtype': 'Float',
			'options': 'currency',
			'width': 120
        }
	]
	for j in additional_table_columns:
		columns.append({
			"label": j.mode_of_payment,
			"fieldname": j.mode_of_payment,
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		

		})
	columns+= [
		{
	 		'fieldname': "net",
            'label':('Net Cash'),
            'fieldtype': 'Float',
			'options': 'currency',
			'width': 120
        },
		{
	 		'fieldname':"15#Change Amt:Float:200",
            'label':('Change Amt'),
            'fieldtype': 'Float',
			'options': 'currency',
			'width': 120
        },
		{
	 		'fieldname': "21#Recieved:Data:200",
            'label':('Amount Received'),
            'fieldtype': 'Float',
			'options': 'currency',
			'width': 120
        },
		{
	 		'fieldname': "20#Opening ID:Data:200",
            'label':('POS opening entry ID'),
            'fieldtype': 'Data',
			'width': 200
        },
		
		{
	 		'fieldname': "16#Opening Entry date:Data:200",
            'label':('POS opening Date & time'),
            'fieldtype': 'Data',
			'width': 170
        },
		{
	 		'fieldname': "18#Cashier ID:Data:200",
            'label':('Cashier ID'),
            'fieldtype': 'Data',
			'width': 150
        },
			{
	 		'fieldname': "19#Closing ID:Data:200" ,
            'label':('POS closing ID'),
            'fieldtype': 'Data',
			'width': 200
        },
		{
	 		'fieldname':"17#Closing Entry time:Data:200",
            'label':('POS closing Date & time'),
            'fieldtype': 'Data',
			'width': 170
        },
	
	
		
	]
	


	
	return columns

	