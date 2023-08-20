from curses.ascii import NUL
from pickle import FALSE
import frappe
from frappe import throw, _
# from erpnext.shopping_cart.doctype.shopping_cart_settings.shopping_cart_settings \
# 	import get_shopping_cart_settings, show_quantity_in_website
from erpnext.shopping_cart.cart import _get_cart_quotation, _set_price_list
from erpnext.utilities.product import get_price as get_price_default, get_qty_in_stock, get_non_stock_item_status
from frappe.utils import flt,cint,fmt_money
from erpnext.shopping_cart.cart import * 
from frappe.core.doctype.user.user import *
from frappe.core.doctype.sms_settings.sms_settings import send_sms
from frappe.utils import cstr
from datetime import date,datetime,timedelta
@frappe.whitelist()
def vim_get_SO_information(customer_name):
	so_list = frappe.db.get_list('Sales Order',
	filters={
		'customer': customer_name
	},
	fields=['name'],
	order_by='date desc',
	start=10,
	page_length=20,
	as_list=True
)
	return so_list

@frappe.whitelist(allow_guest=True)
def vim_get_event_bookings(item_code = None,branch = None,brand =None, city = None) :
	from datetime import date
	import datetime as dt
	ev_date = date.today()
	cond = "date >= '"+ev_date.strftime("%m/%d/%Y") +"'"
	if item_code :
		cond += " and event_item = '"+ item_code +"'"
	if branch :
		cond += " and branch = '"+ branch +"'"
	if brand :
		cond += " and brand = '"+ brand +"'"
	if city :
		cond += " and city = '"+ city +"'"
	booked_rows = frappe.db.sql("""select name as id,'Booked' as title, CONCAT(date, 'T', from_time ) as start, CONCAT(date, 'T', to_time) as end, 0 as allDay , 'booked-slot' as classNames from `tabEvent Booking` where {cond}""".format(cond=cond),as_dict = 1)
	item_slots = frappe.db.sql("""select TIME(start_time) as start_time, TIME(end_time) as end_time, slot_name as name from `tabSlot List` where parent='{}'""".format(item_code),as_dict = 1)
	# frappe.errprint([item_slots,item_code])
	rows = []
	free_slot  ={}
	for i in range(60):
		for slot in item_slots:
			# frappe.errprint([str(slot['start_time']),str(slot['start_time'])[0:5]])
			if not frappe.db.sql("""select name as id,'Booked' as title, CONCAT(date, 'T', from_time ) as start, CONCAT(date, 'T', to_time) as end, 0 as allDay from `tabEvent Booking` where {cond} and date ='{0}' and slot = '{1}'""".format(ev_date,slot['name'],cond=cond),as_dict = 1) :
				# frappe.errprint([slot,"""select name as id,'Booked' as title, CONCAT(date, 'T', from_time ) as start, CONCAT(date, 'T', to_time) as end, 0 as allDay from `tabEvent Booking` where {cond} and date ='{0}' and slot = '{1}'""".format(ev_date,slot['name'],cond=cond),
				# frappe.db.sql("""select name as id,'Booked' as title, CONCAT(date, 'T', from_time ) as start, CONCAT(date, 'T', to_time) as end, 0 as allDay from `tabEvent Booking` where {cond} and date ='{0}' and slot = '{1}'""".format(ev_date,slot['name'],cond=cond),as_dict = 1) ])
				rows.append({'title':'Available',
				'start': dt.datetime.combine(ev_date, dt.datetime.strptime(":".join(str(slot['start_time']).split(":")[0:2]), '%H:%M').time()),
				'end': dt.datetime.combine(ev_date, dt.datetime.strptime(":".join(str(slot['end_time']).split(":")[0:2]), '%H:%M').time()),
				'allDay':0,
				'clickable':True,
				'name':slot['name'],
				'slot_date':ev_date,
				'slot_start':":".join(str(slot['start_time']).split(":")[0:2]),
				'slot_end':":".join(str(slot['end_time']).split(":")[0:2]),
				'backgroundColor': '#41e341',
				'classNames':'free-slot',
				'color':'green'})
		ev_date += dt.timedelta(days=1)
	for row in booked_rows :
		rows.append(row)
	return rows
	# return frappe.db.sql("""select name as id,'Booked' as title, CONCAT(date, 'T', from_time ) as start, CONCAT(date, 'T', to_time) as end, 0 as allDay from `tabEvent Booking`""",as_dict = 1)

@frappe.whitelist(allow_guest=True)
def get_product_info_for_website(item_code, skip_quotation_creation=False):
	"""get product price / stock info for website"""
	# frappe.errprint("API")
	cart_settings = get_shopping_cart_settings()
	if not cart_settings.enabled:
		return frappe._dict()

	cart_quotation = frappe._dict()
	if not skip_quotation_creation:
		cart_quotation = _get_cart_quotation()

	selling_price_list = cart_quotation.get("selling_price_list") if cart_quotation else _set_price_list(cart_settings, None)

	price = get_price(
		item_code,
		selling_price_list,
		cart_settings.default_customer_group,
		cart_settings.company
	)

	stock_status = get_qty_in_stock(item_code, "website_warehouse")
	product_info = {
		"price": price,
		"stock_qty": stock_status.stock_qty,
		"in_stock": stock_status.in_stock if stock_status.is_stock_item else get_non_stock_item_status(item_code, "website_warehouse"),
		"qty": 0,
		"uom": frappe.db.get_value("Item", item_code, "stock_uom"),
		"show_stock_qty": show_quantity_in_website(),
		"sales_uom": frappe.db.get_value("Item", item_code, "sales_uom"),
		"non_sharable_slot": frappe.db.get_value("Item", item_code, "non_sharable_slot")
	}

	if product_info["price"]:
		if frappe.session.user != "Guest":
			item = cart_quotation.get({"item_code": item_code}) if cart_quotation else None
			if item:
				product_info["qty"] = item[0].qty
	return frappe._dict({
		"product_info": product_info,
		"cart_settings": cart_settings
	})

@frappe.whitelist()
def update_cart(item_code, qty, additional_notes=None, with_items=False ,slot =None,delivery_date=None,brand=None,branch=None,city=None ,phone =None,uom = None , restapi =False):
	# try :
	user_name=frappe.get_doc("User",frappe.session.user)	
	if frappe.session.user !='Administrator' and user_name.user_type =='Website User':
		user=frappe.session.user
		if user:
			customer = None
			for d in frappe.get_all("Contact", fields=("name"), filters={"email_id": user}):
				contact_name = frappe.db.get_value("Contact", d.name)
				if contact_name:
					contact = frappe.get_doc('Contact', contact_name)
					doctypes = [d.link_doctype for d in contact.links]
					doc_name  = [d.link_name for d in contact.links]
					if  "Customer" in doctypes : 
						cust = doc_name[doctypes.index("Customer")]
						customer = frappe.get_doc('Customer', cust)
			
			if not customer : 
				if(frappe.session.user !='Guest'):
					# from erpnext.portal.utils import create_customer_or_supplier
					create_customer_or_supplier()
			if  (customer and customer.is_first_time_login==1):
				user_data=frappe.get_doc('User',frappe.session.user)
				if customer and not customer.mobile_no :
					customer.mobile_no = user_data.mobile_no
					update_cust = True
					if customer and not customer.email_id :
						customer.email_id = user_data.name
						update_cust = True
					if customer and not customer.first_name :
						customer.first_name  = customer.name.split(" ")[0]
						customer.last_name  = customer.name.split(" ")[1] if len(customer.name) > 1 else ""
						update_cust = True
					if customer and not customer.city :
						customer.city = user_data.location  
						update_cust = True
					if update_cust : 
						customer.flags.ignore_permissions = True
						customer.is_first_time_login = 0
						customer.save()
			# if not customer or (customer and customer.is_first_time_login==1):
			# 	if restapi :
			# 		return {"error":True,"message":"Please complete customer profile details for {} {}".format(user,frappe.get_all("Contact", fields=("name"), filters={"email_id": user}))}
			# 	frappe.throw("Please complete customer profile details")            
	quotation = _get_cart_quotation()
	# frappe.errprint(["cart",item_code, qty, additional_notes, with_items,slot,brand,branch,city])
	empty_card = False
	qty = flt(qty)
	if qty == 0:
		quotation_items = quotation.get("items", {"item_code": ["!=", item_code]})
		if quotation_items:
			quotation.set("items", quotation_items)
		else:
			empty_card = True

	else:
		if not cint(with_items) and slot:
			quotation_items = quotation.get("items", {"item_code": ["!=", item_code]})
			if quotation_items:
				quotation.set("items", quotation_items)

		quotation_items = quotation.get("items", {"item_code": item_code})
		if restapi :
			min_qty = frappe.db.get_value('Item', item_code, 'minimum_sales_quantity')
			max_qty = frappe.db.get_value('Item', item_code, 'maximum_sales_quantity')

			non_sharable_slot = frappe.db.get_value('Item',item_code, 'non_sharable_slot')
			if non_sharable_slot  : 
				if min_qty and qty<min_qty:
					qty = min_qty
					return {"error":True,"message":"Minimum Quantity alllowed is {}".format(min_qty)}
				if max_qty and qty > max_qty:
					qty = max_qty
					return {"error":True,"message":"Maximum Quantity alllowed is {}".format(max_qty)}
		if not quotation_items:
			non_sharable_slot = frappe.db.get_value('Item',item_code, 'non_sharable_slot')
			if non_sharable_slot  : 
				min_qty = frappe.db.get_value('Item', item_code, 'minimum_sales_quantity')
				if min_qty and qty<min_qty:
					qty = min_qty
				brand = frappe.db.get_value('Item',item_code, 'dimension_brand')
			quotation.append("items", {
				"doctype": "Quotation Item",
				"item_code": item_code, 
				"qty": qty,
				"additional_notes": additional_notes,
				"slot_name": slot,
				"delivery_date":delivery_date
			})
		else:
			if slot :
				min_qty = frappe.db.get_value('Item', item_code, 'minimum_sales_quantity')
				if min_qty and qty<min_qty:
					qty = min_qty
			quotation_items[0].qty = qty
			if additional_notes :
				quotation_items[0].additional_notes = additional_notes
			if slot :
				quotation_items[0].slot_name = slot
			if delivery_date :
				quotation_items[0].delivery_date = delivery_date
		quotation_items = quotation.get("items", {"item_code": item_code})
		if quotation_items and len(quotation_items) and uom : 
				quotation_items[0].uom = uom
		apply_cart_settings(quotation=quotation)
		quotation.flags.ignore_permissions = True
		quotation.payment_schedule = []
		if brand :
			quotation.brand = brand
		if phone :
			customer = frappe.db.sql("""select name from `tabCustomer` where mobile_no='{}' """.format(phone),as_dict = True)
			if len(customer) :
				quotation.customer_from_website = customer[0]['name']
				frappe.cache().set_value("web_customer-"+str(frappe.session.user), customer[0]['name'])
			# quotation.party_name =  quotation.customer_from_website
			# customer_user = frappe.db.get_value("Customer", quotation.customer_from_website,
			# ["email_id"], as_dict=1)
			# contact = get_contact_name(customer_user.email_id)
			
			# quotation.contact_person = contact
			# contact_info = frappe.db.get_value(
			# 			"Contact", contact,
			# 			["first_name", "last_name", "phone", "mobile_no"],
			# 			as_dict=1)
			# if contact_info:
			# 		contact_info.html = """ <b>%(first_name)s %(last_name)s</b> <br> %(phone)s <br> %(mobile_no)s""" % {
			# 			"first_name": contact_info.first_name,
			# 			"last_name": contact_info.last_name or "",
			# 			"phone": contact_info.phone or "",
			# 			"mobile_no": contact_info.mobile_no or ""
			# 		}
			# 		quotation.contact_display =contact_info.html
			# else :
			# 		quotation.contact_display =""
			
			# quotation.contact_email = customer_user.email_id
		if branch :
			quotation.branch = branch
			branch_warehouse = frappe.db.get_list('Dimension Branch',filters={"branch_name":branch},
				fields=['default_warehouse'],pluck='default_warehouse'
				)
			if branch_warehouse :
				quotation_items[0].warehouse = 	branch_warehouse[0]
			if not city :
				city =  frappe.db.get_value('Dimension Branch',branch, 'city')
			if city :
				quotation.city = city
			else : city = ""
	default_tax = frappe.db.get_list('Sales Taxes and Charges Template',filters={"is_default":1},
			fields=['name'],pluck='name',
			ignore_permissions=True)
	if default_tax :
		default_tax=default_tax[0]
		quotation.taxes_and_charges = default_tax
		if not quotation.taxes:
			from erpnext.controllers.accounts_controller import get_taxes_and_charges
			taxes = get_taxes_and_charges('Sales Taxes and Charges Template', default_tax)
			for tax in taxes :
				# frappe.errprint(["taxes",i,i.charge_type])
				quotation.append('taxes', tax)
	
		quotation.set_taxes()
	# except Exception as exec:
	# 	logerror(status = "Error", resp = exec,method="API Update Cart",ref_doc=None)
	if not empty_card:
		quotation.save(ignore_permissions=True)	
	else:
		quotation.delete()
		quotation = None
		frappe.cache().delete_key("web_customer-"+str(frappe.session.user))


	set_cart_count(quotation)

	context = get_cart_quotation(quotation)
	if restapi :
		return 	{"quoation":_get_cart_quotation() ,
		"session_user":frappe.session.user,
			"inputs":{
				"item_code" : item_code,"qty" : qty, "additional_notes" :additional_notes, "with_items":with_items ,"slot" : slot,"delivery_date" : delivery_date,"brand" : brand,"branch" : branch,"city":city,"phone":phone,"uom":uom
			}
			}

	if cint(with_items):
		return {
			"items": frappe.render_template("templates/includes/cart/cart_items.html",
				context),
			"taxes": frappe.render_template("templates/includes/order/order_taxes.html",
				context)
		}
	else:
		return {
			'name': quotation.name,
			'shopping_cart_menu': get_shopping_cart_menu(context)
		}

def logerror(status = None, resp = None,method=None,ref_doc=None):
	new_log=frappe.new_doc("Error Log")
	new_log.method=method
	new_log.error=str(resp)+str(ref_doc)
	new_log.insert(ignore_permissions =True)
	new_log.save(ignore_permissions =True)

@frappe.whitelist()
def place_order(restapi = False , advance_amount = 0, payment_status = '', transactionid = ''):
    
	quotation = _get_cart_quotation()
	cart_settings = frappe.db.get_value("Shopping Cart Settings", None,
		["company", "allow_items_not_in_stock"], as_dict=1)
	quotation.company = cart_settings.company

	for item in quotation.get("items"):
		min_qty = frappe.db.get_value('Item', item.item_code, 'minimum_sales_quantity')
		max_qty = frappe.db.get_value('Item', item.item_code, 'maximum_sales_quantity')
		non_sharable_slot = frappe.db.get_value('Item',item.item_code, 'non_sharable_slot')
		allow_multiple_event=0
		if non_sharable_slot  : 
			cond = "date = '"+item.delivery_date.strftime("%Y-%m-%d") +"'"
			if item.item_code :
				cond += " and event_item = '"+ item.item_code +"'"
			if quotation.branch :
				cond += " and branch = '"+ quotation.branch +"'"
				allow_multiple_event=frappe.db.get_value("Dimension Branch",quotation.branch,"allow_multiple_event")

			if quotation.brand :
				cond += " and brand = '"+ quotation.brand +"'"
			if quotation.city :
				cond += " and city = '"+ quotation.city +"'"
			if item.slot_name :
				cond += " and slot = '"+ item.slot_name +"'"
			if not allow_multiple_event:
				booked_rows = frappe.db.sql("""select name as id,'Booked' as title, CONCAT(date, 'T', from_time ) as start, CONCAT(date, 'T', to_time) as end, 0 as allDay , 'booked-slot' as classNames from `tabEvent Booking` where {cond}""".format(cond=cond),as_dict = 1)
				if  len(booked_rows) :
					if restapi : return {"error":True,"message":"Sorry for inconvenience, Slot is already booked for {} for date {} ".format(item.item_code,item.delivery_date)}
					frappe.throw("Sorry for inconvenience, Slot is already booked for {} for date {} ".format(item.item_code,item.delivery_date))
			if min_qty and item.qty<min_qty:
				# qty = min_qty
				frappe.throw("Minimum Quantity allowed for {} is {}".format(item.item_name , min_qty))
			if max_qty and item.qty > max_qty:
				# qty = max_qty
				frappe.throw("Maximum Quantity allowed fot {} is {}".format(item.item_name,max_qty))
	if quotation.customer_from_website :
		quotation.party_name =  quotation.customer_from_website
		customer_user = frappe.db.get_value("Customer", quotation.customer_from_website,
		["email_id"], as_dict=1)

		
		contact = get_contact_name(customer_user.email_id)
		
		quotation.contact_person = contact
		contact_info = frappe.db.get_value(
					"Contact", contact,
					["first_name", "last_name", "phone", "mobile_no"],
					as_dict=1)
		if contact_info:
				contact_info.html = """ <b>%(first_name)s %(last_name)s</b> <br> %(phone)s <br> %(mobile_no)s""" % {
					"first_name": contact_info.first_name,
					"last_name": contact_info.last_name or "",
					"phone": contact_info.phone or "",
					"mobile_no": contact_info.mobile_no or ""
				}
				quotation.contact_display =contact_info.html
		else :
				quotation.contact_display =""
		
		quotation.contact_email = customer_user.email_id
	quotation.flags.ignore_permissions = True
	quotation.submit()

	if quotation.quotation_to == 'Lead' and quotation.party_name:
		# company used to create customer accounts
		frappe.defaults.set_user_default("company", quotation.company)

	# if not (quotation.shipping_address_name or quotation.customer_address):
	# 	frappe.throw(_("Set Shipping Address or Billing Address"))

	from erpnext.selling.doctype.quotation.quotation import _make_sales_order
	sales_order = frappe.get_doc(_make_sales_order(quotation.name, ignore_permissions=True))
	sales_order.payment_schedule = []
	for item in sales_order.get("items"):
			if quotation.items[item.idx-1].delivery_date :
				item.delivery_date = quotation.items[item.idx-1].delivery_date
				if not sales_order.delivery_date or item.delivery_date < sales_order.delivery_date :
					sales_order.delivery_date = item.delivery_date
				if item.slot_name :
					sales_order.select_event = item.item_code
					sales_order.select_slot = item.slot_name
					sales_order.set_warehouse  =item.warehouse
					sales_order.no_of_entries = item.qty
			# frappe.errprint(["delivery_date",item.delivery_date,item.slot_name,quotation.items[item.idx-1].delivery_date])
	if not cint(cart_settings.allow_items_not_in_stock):
		for item in sales_order.get("items"):
			item.reserved_warehouse, is_stock_item = frappe.db.get_value("Item",
				item.item_code, ["website_warehouse", "is_stock_item"])
			if is_stock_item:
				item_stock = get_qty_in_stock(item.item_code, "website_warehouse")
				if not cint(item_stock.in_stock):
					throw(_("{1} Not in Stock").format(item.item_code))
				if item.qty > item_stock.stock_qty[0][0]:
					throw(_("Only {0} in Stock for item {1}").format(item_stock.stock_qty[0][0], item.item_code))
	address = frappe.db.sql("""select parent as address from `tabDynamic Link` where parenttype = 'Address'  and link_doctype = 'Warehouse' and link_name = '{}'""".format(sales_order.set_warehouse),as_dict = 1)
	if len(address) >0:
		sales_order.company_address = address[0]['address']
	sales_order.flags.ignore_permissions = True
	if advance_amount :
		sales_order.advance_amount = advance_amount 
	if payment_status == "paid":
		sales_order.payment_status = "Paid"
		sales_order.payment_invoice_id = transactionid
		
	sales_order.insert()
	sales_order.flags.ignore_permissions = True
	sales_order.submit()
	frappe.cache().delete_key("web_customer-"+str(frappe.session.user))
	if hasattr(frappe.local, "cookie_manager"):
		frappe.local.cookie_manager.delete_cookie("cart_count")
	return sales_order.name

# def place_order():
# 	quotation = _get_cart_quotation()
# 	cart_settings = frappe.db.get_value("Shopping Cart Settings", None,
# 		["company", "allow_items_not_in_stock"], as_dict=1)
# 	quotation.company = cart_settings.company

# 	for item in quotation.get("items"):
# 		min_qty = frappe.db.get_value('Item', item.item_code, 'minimum_sales_quantity')
# 		max_qty = frappe.db.get_value('Item', item.item_code, 'maximum_sales_quantity')
# 		non_sharable_slot = frappe.db.get_value('Item',item.item_code, 'non_sharable_slot')
# 		if non_sharable_slot  : 
# 			cond = "date = '"+item.delivery_date.strftime("%Y-%m-%d") +"'"
# 			if item.item_code :
# 				cond += " and event_item = '"+ item.item_code +"'"
# 			if quotation.branch :
# 				cond += " and branch = '"+ quotation.branch +"'"
# 			if quotation.brand :
# 				cond += " and brand = '"+ quotation.brand +"'"
# 			if quotation.city :
# 				cond += " and city = '"+ quotation.city +"'"
# 			if item.slot_name :
# 				cond += " and slot = '"+ item.slot_name +"'"
# 			booked_rows = frappe.db.sql("""select name as id,'Booked' as title, CONCAT(date, 'T', from_time ) as start, CONCAT(date, 'T', to_time) as end, 0 as allDay , 'booked-slot' as classNames from `tabEvent Booking` where {cond}""".format(cond=cond),as_dict = 1)
# 			if  len(booked_rows) :
# 				frappe.throw("Sorry for inconvenience, Slot is already booked for {} for date {} ".format(item.item_code,item.delivery_date))
# 			if min_qty and item.qty<min_qty:
# 				# qty = min_qty
# 				frappe.throw("Minimum Quantity allowed for {} is {}".format(item.item_name , min_qty))
# 			if max_qty and item.qty > max_qty:
# 				# qty = max_qty
# 				frappe.throw("Maximum Quantity allowed fot {} is {}".format(item.item_name,max_qty))
# 	if quotation.customer_from_website :
# 		quotation.party_name =  quotation.customer_from_website
# 		customer_user = frappe.db.get_value("Customer", quotation.customer_from_website,
# 		["email_id"], as_dict=1)

		
# 		contact = get_contact_name(customer_user.email_id)
# 		quotation.contact_person = contact
# 		quotation.contact_email = customer_user.email_id
# 	quotation.flags.ignore_permissions = True
# 	quotation.submit()

# 	if quotation.quotation_to == 'Lead' and quotation.party_name:
# 		# company used to create customer accounts
# 		frappe.defaults.set_user_default("company", quotation.company)

# 	# if not (quotation.shipping_address_name or quotation.customer_address):
# 	# 	frappe.throw(_("Set Shipping Address or Billing Address"))

# 	from erpnext.selling.doctype.quotation.quotation import _make_sales_order
# 	sales_order = frappe.get_doc(_make_sales_order(quotation.name, ignore_permissions=True))
# 	sales_order.payment_schedule = []
# 	for item in sales_order.get("items"):
# 			if quotation.items[item.idx-1].delivery_date :
# 				item.delivery_date = quotation.items[item.idx-1].delivery_date
# 				if not sales_order.delivery_date or item.delivery_date < sales_order.delivery_date :
# 					sales_order.delivery_date = item.delivery_date
# 				if item.slot_name :
# 					sales_order.select_event = item.item_code
# 					sales_order.select_slot = item.slot_name
# 					sales_order.set_warehouse  =item.warehouse
# 					sales_order.no_of_entries = item.qty
# 			# frappe.errprint(["delivery_date",item.delivery_date,item.slot_name,quotation.items[item.idx-1].delivery_date])
# 	if not cint(cart_settings.allow_items_not_in_stock):
# 		for item in sales_order.get("items"):
# 			item.reserved_warehouse, is_stock_item = frappe.db.get_value("Item",
# 				item.item_code, ["website_warehouse", "is_stock_item"])
# 			if is_stock_item:
# 				item_stock = get_qty_in_stock(item.item_code, "website_warehouse")
# 				if not cint(item_stock.in_stock):
# 					throw(_("{1} Not in Stock").format(item.item_code))
# 				if item.qty > item_stock.stock_qty[0][0]:
# 					throw(_("Only {0} in Stock for item {1}").format(item_stock.stock_qty[0][0], item.item_code))
# 	address = frappe.db.sql("""select parent as address from `tabDynamic Link` where parenttype = 'Address'  and link_doctype = 'Warehouse' and link_name = '{}'""".format(sales_order.set_warehouse),as_dict = 1)
# 	if len(address) >0:
# 		sales_order.company_address = address[0]['address']
# 	sales_order.flags.ignore_permissions = True
# 	sales_order.insert()
# 	sales_order.flags.ignore_permissions = True
# 	sales_order.submit()
# 	frappe.cache().delete_key("web_customer")
# 	if hasattr(frappe.local, "cookie_manager"):
# 		frappe.local.cookie_manager.delete_cookie("cart_count")
# 	return sales_order.name

@frappe.whitelist(allow_guest=True)
def get_branch_details(item_code = None):
	brand_list = ""
	if item_code :
		brand_list = frappe.db.get_value('Item',item_code, 'dimension_brand')

	branch_list = frappe.db.get_list('Dimension Branch',
	fields=['name'],
	as_list=True
	)
	uom = []
	if item_code and item_code!= '':
		Item = frappe.get_doc('Item',item_code)
		if Item :
			for i in  Item.uoms:
				uom.append(i.uom)
	# city_list = frappe.db.get_list('Dimension City',
	# fields=['name'],
	# as_list=True
	# )

	# phone_list = frappe.db.sql("""select mobile_no from `tabCustomer` where mobile_no !='' """,as_list = True)
	phone_list = frappe.db.get_list('Customer', filters={
			'mobile_no': ['!=',''],
			'disabled' : 0
		},
		pluck='mobile_no'
		)
	# return {"brand_list":brand_list,"branch_list":branch_list,"city_list":city_list,"phone_list":phone_list}
	return {"brand_list":brand_list,"branch_list":branch_list,"phone_list":phone_list,"uom_list":uom}



@frappe.whitelist(allow_guest=True)
def get_branch_list(brand):

	branch_list = frappe.db.get_list('Dimension Branch',
	fields=['name'],filters={"brand" : brand},
	as_list=True
	)

	return {"branch_list":branch_list}



@frappe.whitelist(allow_guest=True)
def get_customer(phone):

	# custmer = frappe.db.get_doc('Customer',filters={"mobile_no" : phone})
	custmer = frappe.db.sql("""select customer_name from `tabCustomer` where mobile_no='{}' """.format(phone))
	return custmer[0]


@frappe.whitelist(allow_guest=True)
def is_internal_user():
	# user = frappe.session.user if frappe.session.user else False
	# web_customer = frappe.cache().get_value("web_customer-"+str(frappe.session.user))
	# if web_customer : return False
	# if user :
	# 	p = frappe.db.get_value("User", user, "user_type", as_dict=True)
	# 	if p and p.get("user_type") == "System User": return True
			  
	return True if frappe.session.data.user_type == "System User" else False


@frappe.whitelist(allow_guest=True)
def sign_up(email, full_name, mobile,city,national_id,  redirect_to):
	from frappe.website.utils import is_signup_enabled
	if not is_signup_enabled():
		frappe.throw(_('Sign Up is disabled'), title='Not Allowed')

	user = frappe.db.get("User", {"email": email})
	if user:
		if user.disabled:
			return 0, _("Registered but disabled")
		else:
			return 0, _("Already Registered")
	else:
		if frappe.db.sql("""select count(*) from tabUser where
			HOUR(TIMEDIFF(CURRENT_TIMESTAMP, TIMESTAMP(modified)))=1""")[0][0] > 300:

			frappe.respond_as_web_page(_('Temporarily Disabled'),
				_('Too many users signed up recently, so the registration is disabled. Please try back in an hour'),
				http_status_code=429)

		from frappe.utils import random_string , escape_html
		user = frappe.get_doc({
			"doctype":"User",
			"email": email,
			"first_name": escape_html(full_name),
			"enabled": 1,
			"mobile_no":mobile,
			"location":city, 
			"new_password": random_string(10),
			"user_type": "Website User"
		})
		user.flags.ignore_permissions = True
		user.flags.ignore_password_policy = True
		user.insert()

		# set default signup role as per Portal Settings
		default_role = frappe.db.get_value("Portal Settings", None, "default_role")
		if default_role:
			user.add_roles(default_role)

		if redirect_to:
			frappe.cache().hset('redirect_after_login', user.name, redirect_to)

		if user.flags.email_sent:
			return 1, _("Please check your email for verification")
		else:
			return 2, _("Please ask your administrator to verify your sign-up")




@frappe.whitelist(allow_guest=True)
def check_login():
		if frappe.session.user=="Guest":
			frappe.msgprint("To add into cart first login")
		user_name=frappe.get_doc("User",frappe.session.user)	
		if frappe.session.user !='Administrator' and user_name.user_type =='Website User':
			user=frappe.session.user
			if user:
				customer = None
				for d in frappe.get_list("Contact", fields=("name"), filters={"email_id": user}):
					contact_name = frappe.db.get_value("Contact", d.name)
					if contact_name:
						contact = frappe.get_doc('Contact', contact_name)
						doctypes = [d.link_doctype for d in contact.links]
						doc_name  = [d.link_name for d in contact.links]
						if  "Customer" in doctypes : 
							cust = doc_name[doctypes.index("Customer")]
							customer = frappe.get_doc('Customer', cust)
				if not customer or (customer and customer.is_first_time_login==1):
					frappe.msgprint("Please complete customer profile details")            
		

@frappe.whitelist(allow_guest=True)
def successful_login() :
	roles = frappe.get_roles(frappe.session.user)
	cond = "name in (" 
	for role in roles:
		if role != roles[0] : cond += " ,"
		cond += "'" +role + "'"
	cond += ")"
	cond += " and home_page is not null  and home_page != '' order by modified"
	home_page_roles = frappe.db.sql("""select home_page from `tabRole`  where {cond}""".format(cond=cond),as_dict = 1) 
	# frappe.throw(["Login test",frappe.session.user,"tt"])
	if  home_page_roles:
		frappe.local.response["home_page"] = home_page_roles[-1]['home_page']
	user_name=frappe.get_doc("User",frappe.session.user)	
	if frappe.session.user !='Administrator' and user_name.user_type =='Website User':
		user=frappe.session.user
		if user:
			customer = None
			
			for d in frappe.get_list("Contact", fields=("name"), filters={"email_id": user}):
				contact_name = frappe.db.get_value("Contact", d.name)
				if contact_name:
					contact = frappe.get_doc('Contact', contact_name)
					doctypes = [d.link_doctype for d in contact.links]
					doc_name  = [d.link_name for d in contact.links]
					if  "Customer" in doctypes : 
						cust = doc_name[doctypes.index("Customer")]
						customer = frappe.get_doc('Customer', cust)
			# # else : 
			# if not customer: 
			# 	customer=frappe.get_doc("Customer", {'name': user_name.first_name}) 
		
			if not customer or (customer and not customer.is_first_time_login):
				frappe.local.response["home_page"]="customer_details"	
@frappe.whitelist(allow_guest=True)
def vim_get_slot_list(item_code = None,visit_date= None,branch = None,brand =None, city = None,unit = None) :
		# from datetime import date
	import datetime as dt
	# ev_date = date.today()
	ev_date =  dt.datetime.strptime(visit_date,"%Y-%m-%d")
	cond = "date >= '"+ev_date.strftime("%m/%d/%Y") +"'"
	# cond = "date >= '"+ev_date +"'"
	allow_multiple_event=0
	if item_code :
		cond += " and event_item = '"+ item_code +"'"
	if branch :
		cond += " and branch = '"+ branch +"'"
		allow_multiple_event=frappe.db.get_value("Dimension Branch",branch,"allow_multiple_event")
	if brand :
		cond += " and brand = '"+ brand +"'"
	if city :
		cond += " and city = '"+ city +"'"
	booked_rows = frappe.db.sql("""select name as id,'Booked' as title, CONCAT(date, 'T', from_time ) as start, CONCAT(date, 'T', to_time) as end, 0 as allDay , 'booked-slot' as classNames from `tabEvent Booking` where {cond}""".format(cond=cond),as_dict = 1)
	slot_cond = ""
	if unit :
		slot_cond += " and uom = '"+ unit +"'"
	item_slots = frappe.db.sql("""select TIME(start_time) as start_time, TIME(end_time) as end_time, slot_name as name from `tabSlot List` where parent='{}' {slot_cond} order by idx""".format(item_code,slot_cond=slot_cond),as_dict = 1)
	# frappe.errprint(["Slot",item_slots,item_code])
	rows = []
	free_slot  ={}
	
	for i in range(1):
		for slot in item_slots:	
			if not allow_multiple_event:
				if not frappe.db.sql("""select name as id,'Booked' as title, CONCAT(date, 'T', from_time ) as start, CONCAT(date, 'T', to_time) as end, 0 as allDay from `tabEvent Booking` where {cond} and date ='{0}' and slot = '{1}'""".format(ev_date,slot['name'],cond=cond),as_dict = 1) :
					if not frappe.db.sql("""select name as id,from_time  as start, to_time as end from `tabEvent Booking` where {cond} and from_time<'{2}' and  to_time>'{3}' and date ='{0}' """.format(ev_date,slot['name'],slot['end_time'],slot['start_time'],cond=cond),as_dict = 1) : 
							rows.append({
								'Name':slot['name'] + " "+":".join(str(slot['start_time']).split(":")[0:2]) + "-"+":".join(str(slot['end_time']).split(":")[0:2]),
						"id": slot['name']})
			else:
				rows.append({
								'Name':slot['name'] + " "+":".join(str(slot['start_time']).split(":")[0:2]) + "-"+":".join(str(slot['end_time']).split(":")[0:2]),
						"id": slot['name']})			
		# ev_date += dt.timedelta(days=1)
	# for row in booked_rows :
	# 	rows.append(row)
	return rows
	# return frappe.db.sql("""select name as id,'Booked' as title, CONCAT(date, 'T', from_time ) as start, CONCAT(date, 'T', to_time) as end, 0 as allDay from `tabEvent Booking`""",as_dict = 1)

# def vim_get_slot_list(item_code = None,visit_date= None,branch = None,brand =None, city = None,unit = None) :
# 	# from datetime import date
# 	import datetime as dt
# 	# ev_date = date.today()
# 	ev_date =  dt.datetime.strptime(visit_date,"%Y-%m-%d")
# 	cond = "date >= '"+ev_date.strftime("%m/%d/%Y") +"'"
# 	# cond = "date >= '"+ev_date +"'"
# 	if item_code :
# 		cond += " and event_item = '"+ item_code +"'"
# 	if branch :
# 		cond += " and branch = '"+ branch +"'"
# 	if brand :
# 		cond += " and brand = '"+ brand +"'"
# 	if city :
# 		cond += " and city = '"+ city +"'"
# 	booked_rows = frappe.db.sql("""select name as id,'Booked' as title, CONCAT(date, 'T', from_time ) as start, CONCAT(date, 'T', to_time) as end, 0 as allDay , 'booked-slot' as classNames from `tabEvent Booking` where {cond}""".format(cond=cond),as_dict = 1)
# 	slot_cond = ""
# 	if unit :
# 		slot_cond += " and uom = '"+ unit +"'"
# 	item_slots = frappe.db.sql("""select TIME(start_time) as start_time, TIME(end_time) as end_time, slot_name as name from `tabSlot List` where parent='{}' {slot_cond} order by idx""".format(item_code,slot_cond=slot_cond),as_dict = 1)
# 	# frappe.errprint(["Slot",item_slots,item_code])
# 	rows = []
# 	free_slot  ={}
# 	for i in range(1):
# 		for slot in item_slots:
# 			# frappe.errprint([str(slot['start_time']),str(slot['start_time'])[0:5]])
# 			if not frappe.db.sql("""select name as id,'Booked' as title, CONCAT(date, 'T', from_time ) as start, CONCAT(date, 'T', to_time) as end, 0 as allDay from `tabEvent Booking` where {cond} and date ='{0}' and slot = '{1}'""".format(ev_date,slot['name'],cond=cond),as_dict = 1) :
# 				# frappe.errprint([slot,"""select name as id,'Booked' as title, CONCAT(date, 'T', from_time ) as start, CONCAT(date, 'T', to_time) as end, 0 as allDay from `tabEvent Booking` where {cond} and date ='{0}' and slot = '{1}'""".format(ev_date,slot['name'],cond=cond),
# 				if not frappe.db.sql("""select name as id,from_time  as start, to_time as end from `tabEvent Booking` where {cond} and from_time<'{2}' and  to_time>'{3}' and date ='{0}' """.format(ev_date,slot['name'],slot['end_time'],slot['start_time'],cond=cond),as_dict = 1) : 
# 					rows.append({
# 					'Name':slot['name'] + " "+":".join(str(slot['start_time']).split(":")[0:2]) + "-"+":".join(str(slot['end_time']).split(":")[0:2]),
# 					"id": slot['name']})
# 		# ev_date += dt.timedelta(days=1)
# 	# for row in booked_rows :
# 	# 	rows.append(row)
# 	return rows
# 	# return frappe.db.sql("""select name as id,'Booked' as title, CONCAT(date, 'T', from_time ) as start, CONCAT(date, 'T', to_time) as end, 0 as allDay from `tabEvent Booking`""",as_dict = 1)

@frappe.whitelist(allow_guest=True)
def check_available(item_code = None,visit_date= None,branch = None) :
	# from datetime import date
	import datetime as dt
	# ev_date = date.today()
	item =  frappe.get_doc("Item", item_code)
	if not item : return
	applicable_for = item.applicable_for
	if applicable_for == "" : return
	weekDays = ("Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday")
	if visit_date :
		ev_date =  dt.datetime.strptime(visit_date,"%Y-%m-%d")
		weekday = weekDays[ev_date.weekday()]
	else : return
	selling_setting = frappe.get_doc('Selling Settings')
	rate_for_specific_date = None
	rate_for_specific_date_selling = None
	weekends = [] 
	if branch : 
		block_list = frappe.db.sql("""select a.name , a.block_from , a.block_to ,a.reason,a.applicable_for from `tabBlock Order Booking` a 
		 inner join `tabBlock Branch` c on c.parent = a.name
		where   c.block_branch = '{0}'  and  a.block_from <='{2}'
		and a.block_to >='{2}' and a.applicable_for =0 and a.docstatus=1 """.format(branch,item_code,ev_date.strftime("%Y-%m-%d")),as_dict = 1)
		if not block_list and len(block_list)<1:
			block_list = frappe.db.sql("""select a.name , a.block_from , a.block_to ,a.reason,a.applicable_for from `tabBlock Order Booking` a 
			inner join `tabBlock Item`  b on  b.parent = a.name  inner join `tabBlock Branch` c on c.parent = a.name
			where c.block_branch = '{0}'  and b.item = '{1}'  and a.block_from <='{2}'
			and a.block_to >='{2}' and a.applicable_for =1 and a.docstatus=1 """.format(branch,item_code,ev_date.strftime("%Y-%m-%d")),as_dict = 1)
		
		if  block_list and len(block_list)>0:
			if block_list[0]["applicable_for"] == 1 :
				frappe.throw("This event is blocked for the selected event from {} to {} due to {}".format(block_list[0]["block_from"],block_list[0]["block_to"],block_list[0]["reason"]) )
			else :
				frappe.throw("No events are performed from {} to {} due to {}".format(block_list[0]["block_from"],block_list[0]["block_to"],block_list[0]["reason"]) )
		dim_branch = frappe.get_doc('Dimension Branch',{"branch_name":branch})
		if dim_branch.rate_for_specific_date and len(dim_branch.rate_for_specific_date)>0:
			rate_for_specific_date = dim_branch.rate_for_specific_date
		if  selling_setting.rate_for_specific_date and len(selling_setting.rate_for_specific_date)>0:
			rate_for_specific_date_selling = selling_setting.rate_for_specific_date
		if dim_branch.weekend_days :
			weekends = dim_branch.weekend_days.split(',')
		elif selling_setting.weekend_days :
			weekends = selling_setting.weekend_days.split(',')
	else :
		if  selling_setting.rate_for_specific_date and len(selling_setting.rate_for_specific_date)>0:
			rate_for_specific_date = selling_setting.rate_for_specific_date
		if selling_setting.weekend_days :
			weekends = selling_setting.weekend_days.split(',')
	special_day = False
	if rate_for_specific_date:
		for dates in rate_for_specific_date :
			if ev_date.date() ==dates.date :
					if dates.rate_applicable != applicable_for:
						if applicable_for == "Weekday":
							frappe.throw("Weekday event only, please select Weekend event or select Weekday date")
						else :
							frappe.throw("Weekend event only, please select Weekday event or select Weekend date")
					else : special_day =True
	if rate_for_specific_date_selling and not special_day:
		for dates in rate_for_specific_date_selling :
			if ev_date.date() ==dates.date :
					if dates.rate_applicable != applicable_for:
						if applicable_for == "Weekday":
							frappe.throw("Weekday event only, please select Weekend event or select Weekday date")
						else :
							frappe.throw("Weekend event only, please select Weekday event or select Weekend date")
					else : special_day =True
	# frappe.errprint([weekends,weekday,special_day])
	if len(weekends) > 0 and not special_day:
		if weekday in weekends:
			if applicable_for == "Weekday":
				frappe.throw("Weekday event only, please select Weekend event or select Weekday date")
		elif applicable_for != "Weekday" :
			frappe.throw("Weekend event only, please select Weekday event or select Weekend date")
	return 


@frappe.whitelist(allow_guest=True)
def get_price(item_code = None,uom = None) :
	if not item_code or not uom:
		return 
	cart_settings = get_shopping_cart_settings()
	if not cart_settings.enabled:
		return frappe._dict()

	cart_quotation = frappe._dict()
	skip_quotation_creation = True
	if not skip_quotation_creation:
		cart_quotation = _get_cart_quotation()

	selling_price_list = cart_quotation.get("selling_price_list") if cart_quotation else _set_price_list(cart_settings, None)
	currency = frappe.db.get_value("Price List", selling_price_list, "currency")
	if frappe.db.exists({
		'doctype': 'Item Price',
		'item_code': item_code,
		'uom': uom
		}) :


		
		price_list = frappe.get_doc("Item Price", {'item_code':item_code,'uom':uom})
		price = frappe.get_all("Item Price", fields=["price_list_rate", "currency"],
			filters={"price_list": price_list.name, "item_code": item_code})
		# frappe.errprint([price_list,price_list.price_list_rate])
		format_price = fmt_money(price_list.price_list_rate, currency=currency)

		return  {"formatted_price" : "<span>"+format_price+"</span>/<span>"+uom+"</span>"}
	else :
		uom_conversion_factor = frappe.db.sql("""select	C.conversion_factor
					from `tabUOM Conversion Detail` C
					inner join `tabItem` I on C.parent = I.name and C.uom = '%s'
					where I.item_code = '%s'""" %( uom,item_code))

		uom_conversion_factor = uom_conversion_factor[0][0] if uom_conversion_factor else 1
		
		price = frappe.get_all("Item Price", fields=["price_list_rate", "currency"],
			filters={"price_list": selling_price_list, "item_code": item_code})
		format_price = fmt_money(price[0]['price_list_rate'] * uom_conversion_factor, currency=currency)
		return  {"formatted_price" : "<span>"+format_price+"</span>/<span>"+uom+"</span>"}

@frappe.whitelist(allow_guest=True)
def get_validity(item_code =None):
	from datetime import date ,timedelta 
	import datetime as dt
	v_date = date.today()
	valid_from = v_date.strftime("%d/%m/%Y") 
	set_validity_period =	frappe.db.get_value("Item", item_code, "set_validity_period")
	valid_to=""
	if set_validity_period:
		valid_to = (date.today() + timedelta(days=set_validity_period)).strftime("%d/%m/%Y")
	return {"valid_from":valid_from,"valid_to":valid_to,"if_zero":set_validity_period}

	
@frappe.whitelist(allow_guest=True)
def update_password(new_password, logout_all_sessions=0, key=None, old_password=None):
	#validate key to avoid key input like ['like', '%'], '', ['in', ['']
	from frappe.core.doctype.user.user import test_password_strength,handle_password_test_fail,_get_user_for_update_password,reset_user_data
	from frappe.utils import  today
	from frappe.utils.password import update_password as _update_password
	if key and not isinstance(key, str):
		frappe.throw(_('Invalid key type'))

	result = test_password_strength(new_password, key, old_password)
	feedback = result.get("feedback", None)

	if feedback and not feedback.get('password_policy_validation_passed', False):
		handle_password_test_fail(result)

	res = _get_user_for_update_password(key, old_password)
	if res.get('message'):
		frappe.local.response.http_status_code = 410
		return res['message']
	else:
		user = res['user']

	logout_all_sessions = cint(logout_all_sessions) or frappe.db.get_single_value("System Settings", "logout_on_password_reset")
	_update_password(user, new_password, logout_all_sessions=cint(logout_all_sessions))

	user_doc, redirect_url = reset_user_data(user)

	# get redirect url from cache
	redirect_to = frappe.cache().hget('redirect_after_login', user)
	if redirect_to:
		redirect_url = redirect_to
		frappe.cache().hdel('redirect_after_login', user)

	frappe.local.login_manager.login_as(user)

	frappe.db.set_value("User", user, "last_password_reset_date", today())
	frappe.db.set_value("User", user, "reset_password_key", "")
	if user_doc.user_type == "System User":
		return "/app"
	else:
		redirect_url = "/customer_details"
		return redirect_url if redirect_url else "/"


# New POS Changes

from  frappe.auth import LoginManager 


@frappe.whitelist(allow_guest=True)
def alt_login(usr=None, pwd=None):
	# No need to pass usr & pwd in login function, it takes it internally from "get_cached_user_pass()" function
	LoginManager().login()	
	mobile_no = frappe.db.get_value('User', {"email": frappe.session.user} , 'mobile_no')

	contact_name = frappe.db.get_value("Contact", {"mobile_no": mobile_no})
	if contact_name:
		contact = frappe.get_doc('Contact', contact_name)
		if not contact.email_id :
			contact.add_email(frappe.session.user, is_primary=True)
			contact.save(ignore_permissions=True)
	return {
				"data": {
				"user": frappe.session.user,
				"sid": frappe.session.sid
				}
			}

def party_exists(doctype, user):
	# check if contact exists against party and if it is linked to the doctype
	mobile_no = frappe.db.get_value('User', {"email": user} , 'mobile_no')
	for d in frappe.get_list("Contact", fields=("name"), filters={"mobile_no": mobile_no}) :
		contact_name = frappe.db.get_value("Contact", d.name)
		if contact_name:
			contact = frappe.get_doc('Contact', contact_name)
			doctypes = [d.link_doctype for d in contact.links]
			if not contact.email_id :
				contact.add_email(user, is_primary=True)
				contact.save(ignore_permissions =True)
	contact_name = frappe.db.get_value("Contact", {"email_id": user})
	if contact_name:
		contact = frappe.get_doc('Contact', contact_name)
		doctypes = [d.link_doctype for d in contact.links]
		return doctype in doctypes
	# else :
	# 	mobile_no = frappe.db.get_value('User', {"email_id": user} , 'mobile_no')
	# 	contact_name = frappe.db.get_value("Contact", {"mobile_no": mobile_no })
	# 	if contact_name:
	# 		contact = frappe.get_doc('Contact', contact_name)
	# 		doctypes = [d.link_doctype for d in contact.links]
	# 		if not contact.email_id :
	# 			contact.add_email(user.email, is_primary=True)
	# 			contact.save()
	# 		return doctype in doctypes

	return False


# Doctype User override create conatct so, same mobile conattc is availale can be used
def create_contact(user, ignore_links=False, ignore_mandatory=False):
	from frappe.contacts.doctype.contact.contact import get_contact_name
	if user.name in ["Administrator", "Guest"]: return
	mobile_no = frappe.db.get_value('User', {"email_id": user.email_id} , 'mobile_no')
	# mobile_contact_name = frappe.db.get_value("Contact", {"mobile_no": mobile_no })
	# if mobile_contact_name and user.email:
	# 	mob_contact =  frappe.get_doc("Contact", mobile_contact_name)
	# 	mob_contact.add_email(user.email, is_primary=True)
	# 	mob_contact.save(ignore_permissions=True)

	for d in frappe.get_list("Contact", fields=("name"), or_filters={"email_id": user.email,"user": user.email,"mobile_no": mobile_no}) :
		contact_name = frappe.db.get_value("Contact", d.name)
		if contact_name:
			contact = frappe.get_doc('Contact', contact_name)
			doctypes = [d.link_doctype for d in contact.links]
			tosave = False
			if not contact.mobile_no :
				contact.mobile_no = mobile_no
				tosave = True
			if not contact.email_id or not contact.user :
				contact.email_id = user
				contact.user = user
				contact.add_email(user, is_primary=True)
				tosave = True
			if tosave :
				contact.save(ignore_permissions =True)
				frappe.db.commit()
				return
				
	contact_name = get_contact_name(user.email)
	if not contact_name :
			contact = frappe.get_doc({
				"doctype": "Contact",
				"first_name": user.first_name,
				"last_name": user.last_name,
				"user": user.name,
				"gender": user.gender,
			})

			if user.email:
				contact.add_email(user.email, is_primary=True)

			if user.phone:
				contact.add_phone(user.phone, is_primary_phone=True)

			if user.mobile_no:
				contact.add_phone(user.mobile_no, is_primary_mobile_no=True)
			contact.insert(ignore_permissions=True, ignore_links=ignore_links, ignore_mandatory=ignore_mandatory)
	else:
		contact = frappe.get_doc("Contact", contact_name)
		contact.first_name = user.first_name
		contact.last_name = user.last_name
		contact.gender = user.gender

		# Add mobile number if phone does not exists in contact
		if user.phone and not any(new_contact.phone == user.phone for new_contact in contact.phone_nos):
			# Set primary phone if there is no primary phone number
			contact.add_phone(
				user.phone,
				is_primary_phone=not any(
					new_contact.is_primary_phone == 1 for new_contact in contact.phone_nos
				)
			)

		# Add mobile number if mobile does not exists in contact
		if user.mobile_no and not any(new_contact.phone == user.mobile_no for new_contact in contact.phone_nos):
			# Set primary mobile if there is no primary mobile number
			contact.add_phone(
				user.mobile_no,
				is_primary_mobile_no=not any(
					new_contact.is_primary_mobile_no == 1 for new_contact in contact.phone_nos
				)
			)

		contact.save(ignore_permissions=True)


def create_customer_or_supplier():
	'''Based on the default Role (Customer, Supplier), create a Customer / Supplier.
	Called on_session_creation hook.
	'''
	user = frappe.session.user

	if frappe.db.get_value('User', user, 'user_type') != 'Website User':
		# frappe.errprint("User not a website user.")
		return

	user_roles = frappe.get_roles()
	portal_settings = frappe.get_single('Portal Settings')
	default_role = portal_settings.default_role

	if default_role not in ['Customer', 'Supplier']:
		# frappe.errprint("Default role not in Customer or Supplier")
		return

	# create customer / supplier if the user has that role
	if portal_settings.default_role and portal_settings.default_role in user_roles:
		doctype = portal_settings.default_role
	else:
		doctype = None

	if not doctype:
		return
	# frappe.errprint(["after session",doctype,user,party_exists(doctype, user)])
	# frappe.throw("testing Login customer issue")
	if party_exists(doctype, user):
		# frappe.errprint("Party already exists")
		return

	party = frappe.new_doc(doctype)
	fullname = frappe.utils.get_fullname(user)
	from erpnext.shopping_cart.cart import get_debtors_account
	from frappe.utils.nestedset import get_root_of
	if doctype == 'Customer':
		cart_settings = get_shopping_cart_settings()

		if cart_settings.enable_checkout:
			debtors_account = get_debtors_account(cart_settings)
		else:
			debtors_account = ''

		party.update({
			"customer_name": fullname,
			"customer_type": "Individual"
		})

		if debtors_account:
			party.update({
				"accounts": [{
					"company": cart_settings.company,
					"account": debtors_account
				}]
			})
		if doctype == 'Customer':
			party.full_name = fullname
			party.customer_name =  fullname
			party.customer_type = "Individual"
			party.channel_used_at_registration_time = "Online Registration"

			# if debtors_account:
			# 	party.accounts.append({
			# 			"company": cart_settings.company,
			# 			"account": debtors_account
			# 		})
		# contact  = 
		# if user.email:
		# 	party.add_email(user.email, is_primary=True)

		# if user.phone:
		# 	party.add_phone(user.phone, is_primary_phone=True)

		# if user.mobile_no:
		# 	party.add_phone(user.mobile_no, is_primary_mobile_no=True)
	else:
		party.update({
			"supplier_name": fullname,
			"supplier_group": "All Supplier Groups",
			"supplier_type": "Individual"
		})
	party.flags.ignore_mandatory = True
	party.insert(ignore_permissions=True)

	# frappe.throw("Testing fullname {} {}".format(, party.customer_name))
	# frappe.throw("Testing party")

	alternate_doctype = "Customer" if doctype == "Supplier" else "Supplier"

	if party_exists(alternate_doctype, user):
		# if user is both customer and supplier, alter fullname to avoid contact name duplication
		fullname +=  "-" + doctype

	create_party_contact(doctype, fullname, user, party.name)

	return party

def create_party_contact(doctype, fullname, user, party_name):
	mobile_no = frappe.db.get_value('User', {"email": user} , 'mobile_no')
	# contact_name = frappe.db.get_value("Contact", {"mobile_no": mobile_no })
	for d in frappe.get_list("Contact", fields=("name"), filters={"mobile_no": mobile_no}) :
		contact_name = frappe.db.get_value("Contact", d.name)
		if contact_name:
			contact = frappe.get_doc('Contact', contact_name)
			doctypes = [d.link_doctype for d in contact.links]
			if not contact.email_id :
				contact.add_email(user.email, is_primary=True)
				contact.save(ignore_permissions =True)
	contact_name = frappe.db.get_value("Contact", {"mobile_no": mobile_no})
	if contact_name:
		contact = frappe.get_doc('Contact', contact_name)
	else :
		contact = frappe.new_doc("Contact")
		contact.append('email_ids', dict(email_id=user))
	contact.update({
		"first_name": fullname,
		"email_id": user
	})
	contact.append('links', dict(link_doctype=doctype, link_name=party_name))
	contact.flags.ignore_mandatory = True
	contact.save(ignore_permissions=True)

def reset_password(self, send_email=False, password_expired=False):
	from frappe.utils import random_string #, get_url

	key = random_string(32)
	self.db_set("reset_password_key", key)

	url = "/setpassword?key=" + key
	if password_expired:
			url = "/setpassword?key=" + key + '&password_expired=true'

	link = "https://web.vim.sa"+url #get_url(url)
	if send_email:
			self.password_reset_mail(link)

	return link

@frappe.whitelist(allow_guest=True)
def so_webhook(**kwargs):
	print("Webhook data  >>>>>>>>>>>> %s"%(kwargs))
	invoice = kwargs.get("invoice")
	
	def verify_payload():
		key = invoice.get("hook_key")
		if key and key == "vIm@123ViM":
			return True
		else:
			return False

	if not invoice:
		return
		
	if not verify_payload():
		frappe.local.response["http_status_code"] = 401
		return
	inv_no = invoice.get("merchant_invoice_number")
	if inv_no:
		inv_doc = frappe.get_doc("Sales Order", inv_no)
		inv_doc.payment_status = invoice.get("status")
		inv_doc.save()
	return inv_no
@frappe.whitelist(allow_guest=True)
def send_renew_sms(reference_id=None):
	now = datetime.now()
	futur_time_20=now + timedelta(minutes=20)
	futur_time_10=now + timedelta(minutes=10)
	current_time_20 = futur_time_20.strftime("%H:%M:%S")
	current_time_10= futur_time_10.strftime("%H:%M:%S")
	
	so_qry="""select reference_id,name from `tabEvent Booking` where date="{0}" and to_time between "{1}" and "{2}" and ifnull(renew_sms_sent_to_customer,0)=0 """.format(date.today(),current_time_10,current_time_20)
	so_list=frappe.db.sql(so_qry,as_dict = 1)
	frappe.errprint([so_qry,current_time_20,current_time_10,so_list])
	for itm in so_list:
			reference_id=itm["reference_id"]
			#frappe.errprint(reference_id)
			if frappe.db.exists("Sales Order",reference_id):
				so_doc=frappe.get_doc("Sales Order",reference_id)
				recv_list=[so_doc.contact_mobile]
				send_sms(recv_list, cstr('Click here to renew your booking.' + frappe.utils.get_url() + '/booking_renewal?'+reference_id ))
				frappe.db.sql("""update `tabEvent Booking` set `renew_sms_sent_to_customer`=1 where name='{0}'""".format(itm["name"]))
				frappe.db.commit()
				