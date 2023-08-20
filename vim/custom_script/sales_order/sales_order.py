# -*- coding: utf-8 -*-
# Copyright (c) 2021, Avu and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from collections import OrderedDict
from frappe import _
from frappe.model.document import Document
import json

@frappe.whitelist()
def before_submit(self,method):
	nonsharable_slot=0
	lst_date = ""
	new_date =""
	if self.delivery_date:
		import datetime
		delivery_date = self.delivery_date.strftime('%m-%d-%Y') if isinstance(self.delivery_date, datetime.datetime) or isinstance(self.delivery_date, datetime.date)  else self.delivery_date
		lst_date = delivery_date.split("-")
		# frappe.errprint([delivery_date,lst_date])
		new_date = lst_date[2]+"-"+lst_date[1]+"-"+lst_date[0]
	note = ''
	if self.select_event:

		item_doc=frappe.get_doc('Item',self.select_event)
		for item in self.get("items"):
			if self.select_event == item.item_code:
				note = item.additional_notes

		
		if item_doc:
			nonsharable_slot=item_doc.non_sharable_slot
			if nonsharable_slot==1:
				if not self.brand or not self.branch or not self.city:
					frappe.throw("Please select Branch, Brand, City Because you have select Non-Sharable-Slot Event")

		slot_list="select start_time,end_time from `tabSlot List` where slot_name='{0}' and parent = '{1}'".format(self.select_slot,self.select_event)
		slist=frappe.db.sql(slot_list,as_dict=True)

		if slist:
			doc = frappe.new_doc('Event Booking')
			if nonsharable_slot==1:
				
				doc.subject=self.select_event+'-'+new_date+'-'+self.brand+'-'+self.city+'-'+self.branch+'-'+self.select_slot
			else:
				doc.subject=self.select_event+'-'+new_date+'-'+self.select_slot	
			if self.select_event :
				doc.event_item = self.select_event
			if self.select_slot :
				doc.slot = self.select_slot
			doc.note = note
			doc.branch=self.branch
			doc.city=self.city
			doc.brand=self.brand
			doc.department=self.department
			doc.from_time=slist[0]["start_time"]
			doc.no_of_participants=self.no_of_entries
			doc.date=self.delivery_date
			doc.department=self.department
			doc.to_time=slist[0]["end_time"]
			doc.reference_name='Sales Order'
			doc.reference_id=self.name
			doc.flags.ignore_permissions = True
			doc.insert()
			

@frappe.whitelist()
def on_cancel(self,method):
	event="select name from `tabEvent Booking` where reference_name='Sales Order' and reference_id='{0}'".format(self.name)
	event_exist=frappe.db.sql(event,as_dict=True)
	if event_exist:		
		doc=frappe.get_doc('Event Booking',event_exist[0]["name"])
		if doc:
			doc.delete()

	

@frappe.whitelist()
def get_item_list(doctype, txt, searchfield, start, page_len, filters):
	# result_list = []
	# unitdetail = "select name from `tabItem` where is_fixed_asset=0 and is_stock_item=1 and is_sales_item=1 and has_variants=0 and (allowed_hrs > 0 or non_sharable_slot = 1)"
	
	# unitdetails= frappe.db.sql(unitdetail, as_dict=True)	


	unitdetails=frappe.db.sql("""select name,item_name from `tabItem` 
		where is_fixed_asset=%(is_fixed_asset)s and is_stock_item=%(is_stock_item)s and is_sales_item=%(is_sales_item)s and has_variants=%(has_variants)s and (allowed_hrs > 0 or non_sharable_slot = 1) 
		 and (name like %(txt)s or item_name like %(txt)s) 
		limit %(start)s, %(page_len)s""", {"start": start, "page_len":page_len, "txt": "%%%s%%" % txt,"is_fixed_asset": filters.get('is_fixed_asset'),"is_stock_item": filters.get('is_stock_item'),"is_sales_item": filters.get('is_sales_item'),"has_variants": filters.get('has_variants')})
		
	# for tkt in unitdetail:
	# 	unitdetail_data = OrderedDict()
	# 	unitdetail_data['name'] = tkt.get('name') or ''				
	# 	result_list.append(unitdetail_data)
	
	return unitdetails	



@frappe.whitelist()
def get_family_details(customer_name):	
	family_details="""select * from `tabCustomer Family Detail` where parent='{0}'""".format(customer_name)
	detail=frappe.db.sql(family_details,as_dict=True)
	return detail

@frappe.whitelist()
def get_slot_list(item_name,is_new,delivery_date):
	result_list = []
	unitdetail = "select name from `tabItem` where  non_sharable_slot = 1 and name='{0}'".format(item_name)
	shareable_slot= frappe.db.sql(unitdetail, as_dict=True)	
	if shareable_slot:
		
		if is_new:
			slot_list="select slot_name from `tabSlot List` where parent='{0}' and  slot_name not in (select select_slot from `tabSales Order` where select_event='{0}' and docstatus !=2 and date_format(delivery_date,'%Y-%m-%d')='{1}') ".format(item_name,delivery_date)
		else:
			slot_list="select slot_name from `tabSlot List` where parent='{0}'".format(item_name)
		
		slots=frappe.db.sql(slot_list,as_dict=True)
	
		for tkt in slots:
			unitdetail_data = OrderedDict()
			unitdetail_data['slot_name'] = tkt.get('slot_name') or ''				
			result_list.append(unitdetail_data)
	
	return {'result_list': result_list}	


@frappe.whitelist()
def get_item_details(item_name):
	result_list = []
	unitdetail = """select `tabItem`.item_code as 'item_code',`tabItem`.item_name as 'item_name',`tabItem`.stock_uom as 'stock_uom', `tabItem Price`.price_list_rate as 'rate',`tabItem`.non_sharable_slot 'non_sharable_slot' from `tabItem` 
					left join `tabItem Price` on `tabItem Price`.item_code=`tabItem`.item_code
					where `tabItem`.item_code='{0}'""".format(item_name)
	
	unitdetail= frappe.db.sql(unitdetail, as_dict=True)	
	for tkt in unitdetail:
		unitdetail_data = OrderedDict()
		unitdetail_data['item_code'] = tkt.get('item_code') or ''				
		unitdetail_data['item_name'] = tkt.get('item_name') or ''				
		unitdetail_data['stock_uom'] = tkt.get('stock_uom') or ''				
		unitdetail_data['rate'] = tkt.get('rate') or '0'	
		unitdetail_data['non_sharable_slot'] = tkt.get('non_sharable_slot') or '0'				
		result_list.append(unitdetail_data)
	
	return {'result_list': result_list}	

@frappe.whitelist()
def make_work_orders(items, sales_order, company, project=None):
	'''Make Work Orders against the given Sales Order for the given `items`'''
	items = json.loads(items).get('items')
	out = []

	for i in items:
		if not i.get("bom"):
			frappe.throw(_("Please select BOM against item {0}").format(i.get("item_code")))
		if not i.get("pending_qty"):
			frappe.throw(_("Please select Qty against item {0}").format(i.get("item_code")))

		work_order = frappe.get_doc(dict(
			doctype='Work Order',
			production_item=i['item_code'],
			bom_no=i.get('bom'),
			qty=i['pending_qty'],
			company=company,
			sales_order=sales_order,
			sales_order_item=i['sales_order_item'],
			project=project,
			fg_warehouse=i['warehouse'],
			source_warehouse=i['warehouse'],
			wip_warehouse=i['warehouse'],
			description=i['description']
		)).insert()
		work_order.set_work_order_operations()
		for k in work_order.required_items :
			k.source_warehouse = i['warehouse']
		work_order.save()
		out.append(work_order)
	return [p.name for p in out]
