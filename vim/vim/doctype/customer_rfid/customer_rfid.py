# Copyright (c) 2022, aavu and contributors
# For license information, please see license.txt

from wsgiref import validate
import frappe
from frappe.model.document import Document
from frappe.utils import add_to_date ,flt
from datetime import datetime
from collections import OrderedDict



class CustomerRFID(Document):
	
	def updte_rfid(self, docname,  rfid,gust_name,idx):
		if frappe.db.exists('Customer RFID Child', "%s" % (docname) ):
			str="""update `tabCustomer RFID Child` set rfid='{0}' where name='{1}' and parent='{2}' """.format(rfid,docname,self.name)
			frappe.db.sql(str)
			frappe.db.commit()
		else:
				cpi = frappe.new_doc("Customer RFID Child")
				cpi.gust_name=gust_name
				cpi.parent=self.name
				cpi.rfid=rfid
				cpi.parenttype=self.doctype
				cpi.parentfield="gust_detail"
				cpi.idx=idx
				cpi.insert()
				cpi.save()

		if frappe.db.exists('Customer RFID', "%s" % (self.name) ):
			str="""update `tabCustomer RFID` set no_of_gusts='{0}' where name='{1}'  """.format(self.no_of_gusts,self.name)
			frappe.db.sql(str)
			frappe.db.commit()
			# self.save()

	def add_child(self):
		for row in self.gust_detail:			
				cpi = frappe.new_doc("Customer RFID Child")
				cpi.gust_name=row.gust_name
				cpi.parent=self.name
				cpi.parenttype=self.doctype
				cpi.parentfield="gust_detail"
				cpi.idx=row.idx
				cpi.insert()
				cpi.save()
	def before_save(self):
			if frappe.db.exists('POS Invoice', "%s" % (self.pos_invoice) ):	
				docpos =	 frappe.get_doc('POS Invoice', {'name': self.pos_invoice})	
				docpos.rfid_attached=1
				docpos.save();
			rmvlist=[];
			data = self.get("gust_detail")	
			for j in data:
					
					if j.rfid==None or j.rfid=='':
							rmvlist.append(j)
			for i in rmvlist:
				if frappe.db.exists('Customer RFID Child', "%s" % (i.name) ):	
					docchild =	 frappe.get_doc('Customer RFID Child', {'name': i.name})			
					frappe.delete_doc("Customer RFID Child", docchild.name)	
	def remove_child(self, docname):
			if frappe.db.exists('Customer RFID Child', "%s" % (docname) ):
					docchild =	 frappe.get_doc('Customer RFID Child', {'name': docname})			
					frappe.delete_doc("Customer RFID Child", docchild.name)	
	def on_trash (self):
			frappe.errprint("on_delete")
			if frappe.db.exists('POS Invoice', "%s" % (self.pos_invoice) ):	
				update_pos = frappe.get_doc('POS Invoice',self.pos_invoice)
				if update_pos.name:							
						frappe.db.sql("""update `tabPOS Invoice` set `rfid_attached`= 0 where name='{0}'""".format(update_pos.name))
	
						
			
@frappe.whitelist()	
def get_family_details(customer):
	familyllist=[]
	
	pamily_list = frappe.db.sql("""select * from `tabCustomer Family Detail`  where parent='{0}' """.format(customer),as_dict = 1) 
	for data in pamily_list:
		family_data = OrderedDict()
		family_data['person_name'] = data.get('person_name') or ''
		family_data['phone_no'] = data.get('phone_no') or ''		
		familyllist.append(family_data)
	return {'familyllist': familyllist}
