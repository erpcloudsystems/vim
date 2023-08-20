# Copyright (c) 2013, aavu and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _

def execute(filters=None):
	condition=""	
	if filters and  filters.get('date'):
		condition=condition+"and posting_date='{0}' ".format(filters.get('date'))
	sql = """				
		SELECT posting_date,cost_center,closing,cashier,pos_inv,mode_of_payment,sum(closing_amount) as amount,docstatus from(
        SELECT cl.posting_date,pos.cost_center,cl.name as closing,cl.owner as cashier,pos.name as pos_inv,mode_of_payment,closing_amount,cl.docstatus
		from `tabPOS Closing Entry` cl 
		inner join `tabPOS Invoice Reference` ir on ir.parent = cl.name 
        inner join `tabPOS Closing Entry Detail` clos on  cl.name=clos.parent
		inner join `tabPOS Invoice` pos on pos.name = ir.pos_invoice )x where docstatus=1 {0} group by closing
	""".format(condition)
	frappe.errprint(sql)
	raw =frappe.db.sql(sql,as_dict=1)
	result=[]
	if len(raw)!=0:
		additional_table_columns=get_pament_mode(filters)
		columns = get_columns(additional_table_columns)
		payment_rw=get_pament_amt(filters)
	
		for idx, i in enumerate(raw):	
			payment={}
			for val in payment_rw:
				if val.closing==i.closing:
					payment[val.mode_of_payment]=val.amount
			result.append({
						"date" : i.posting_date,
						"cost_center" : i.cost_center,
						"shift" :i.closing,
						"18#Cashier ID:Data:200" : i.cashier,
				})
			for col in additional_table_columns:
				result[-1][col.mode_of_payment]=0.00		
			for key in payment :
				result[-1][key] = (payment[key])
		return columns, result
	return [],[]



def get_pament_mode(filters):
	condition=''

	if filters and filters.get('date'):
		condition=condition+"and posting_date='{0}' ".format(filters.get('date'))
	sql = """SELECT posting_date,closing,pos_inv,mode_of_payment,sum(closing_amount) as amount,docstatus from(
        SELECT cl.posting_date,cl.name as closing,pos.name as pos_inv,mode_of_payment,closing_amount,cl.docstatus
		from `tabPOS Closing Entry` cl 
		inner join `tabPOS Invoice Reference` ir on ir.parent = cl.name 
        inner join `tabPOS Closing Entry Detail` clos on  cl.name=clos.parent
		inner join `tabPOS Invoice` pos on pos.name = ir.pos_invoice )x where docstatus=1 {0} group by mode_of_payment
	 """.format(condition)
	frappe.errprint(sql)
	data=frappe.db.sql(sql,as_dict=1)

	return data

def get_pament_amt(filters):
	condition=""
	
	if filters and  filters.get('date'):
		condition=condition+"and posting_date = '{0}' ".format(filters.get('date'))
	sql = """	SELECT posting_date,closing,pos_inv,mode_of_payment,(closing_amount) as amount,docstatus from(
        SELECT cl.posting_date,cl.name as closing,pos.name as pos_inv,mode_of_payment,closing_amount,cl.docstatus
		from `tabPOS Closing Entry` cl 
		inner join `tabPOS Invoice Reference` ir on ir.parent = cl.name 
        inner join `tabPOS Closing Entry Detail` clos on  cl.name=clos.parent
		inner join `tabPOS Invoice` pos on pos.name = ir.pos_invoice )x where docstatus=1 {0} group by closing,mode_of_payment

	 """.format(condition)
	frappe.errprint(sql)
	data=frappe.db.sql(sql,as_dict=1)
	return data

def get_columns(additional_table_columns):
	columns=[]

	columns+= [
		
        {
            'fieldname': "date",
            'label': ('Posting Date'),
            'fieldtype': 'Date',
        },
			{
	 		'fieldname': "cost_center",
            'label':('Cost Center'),
            'fieldtype': 'Link',
            'options': 'Cost Center',
			'width': 150
        },
		{
	 		'fieldname': "shift",
            'label':('Shift'),
            'fieldtype': 'Link',
            'options': 'POS Closing Entry',
			'width': 150
        },
		
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
	 		'fieldname': "18#Cashier ID:Data:200",
            'label':('Cashier ID'),
            'fieldtype': 'Data',
			'width': 150
        },
			
	
		
	]
	


	
	return columns

	