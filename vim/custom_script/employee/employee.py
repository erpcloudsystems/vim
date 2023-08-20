from __future__ import unicode_literals
import frappe
from frappe import _
from vim.vim.doctype.salesforce_integration.salesforce_integration import sendSalesforceReq, get_config
import json
from datetime import datetime,timedelta
import calendar
from calendar import mdays
@frappe.whitelist()
def generate_coupon(employee=None): 
	
	if 	employee:
		employee_list = frappe.get_list("Employee",  filters = {'name': employee,"allow_gift_coupon":1},fields=["name"])	
	else:
			employee_list=frappe.get_list("Employee",filters = {"allow_gift_coupon":1} , fields=["name"])	
	for emp in employee_list:
		emp_doc=frappe.get_doc("Employee",emp)	
		customer=emp_doc.customer
		if not emp_doc.customer:
			cell_number=emp_doc.cell_number
			frappe.errprint([emp_doc.cell_number,"emp_doc.cell_number",frappe.db.exists('Customer', {"mobile_no":cell_number})])
			if(frappe.db.exists('Customer', {"mobile_no":emp_doc.cell_number if emp_doc.cell_number  else ""})):
				customer=frappe.get_value("Customer",{"mobile_no":emp_doc.cell_number if emp_doc.cell_number  else ""})		
			if not customer:
					customer=create_cuastomer(emp_doc)		
			emp_doc.customer=customer
			emp_doc.save()
		coupon_price_rule=frappe.get_value("Company",emp_doc.company,"free_coupon_pricing_rule")
	
		starting_day_of_current_year = datetime.now().date().replace(month=1, day=1)    
		ending_day_of_current_year = datetime.now().date().replace(month=12, day=31)
		end_date=emp_doc.relieving_date if emp_doc.relieving_date and emp_doc.relieving_date < ending_day_of_current_year else ending_day_of_current_year
		st_date= emp_doc.date_of_joining if  emp_doc.date_of_joining > starting_day_of_current_year else starting_day_of_current_year
		coupon_count=((end_date.year - st_date.year) * 12 + (end_date.month - st_date.month))+1
		st_month=st_date
	
		if not coupon_price_rule:
			frappe.throw(_('The Free Coupon Pricing Rule has not been set in the Company.'))
		else:   
				for i in range(coupon_count):				
					month = st_month.month
					coupon_name=str(emp_doc.name)+"-"+str(calendar.month_abbr[month])+"-"+str(datetime.now().year)
					if not frappe.db.exists('Coupon Code', coupon_name):
						coupon_doc=frappe.new_doc('Coupon Code')
						coupon_doc.coupon_name=coupon_name
						coupon_doc.coupon_type="Gift Card"
						coupon_doc.pricing_rule=coupon_price_rule
						coupon_doc.valid_from=st_date
						coupon_doc.valid_upto=end_date
						coupon_doc.customer=customer
						coupon_doc.save()
					st_month= st_month + timedelta(mdays[st_month.month])
			
	
def get_customer_group():
		
	return frappe.db.get_single_value('Selling Settings', 'customer_group') or frappe.db.get_value('Customer Group', {'is_group': 0}, 'name')

def get_territory():
		
	return frappe.db.get_single_value('Selling Settings','territory') or _('All Territories')
def create_cuastomer(json_object):
		customer_doc = frappe.new_doc('Customer')
		customer_doc.customer_name = json_object.employee_name
		customer_doc.first_name = json_object.first_name
		customer_doc.last_name = json_object.last_name if json_object.last_name  else json_object.first_name
			
		customer_doc.last_name = json_object.first_name
		customer_doc.customer_type = 'Individual'
		customer_doc.customer_group = get_customer_group()
		customer_doc.territory = get_territory()
		customer_doc.mobile_no =  json_object.cell_number if json_object.cell_number  else ""
		customer_doc.customer_name_in_arabic = json_object.full_name_in_arabic if json_object.full_name_in_arabic  else ""
		customer_doc.email_id = json_object.personal_email if json_object.personal_email else ""

		customer_doc.insert(ignore_permissions=True)
		customer_doc.save()
		return customer_doc.name