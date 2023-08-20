import frappe
from erpnext.shopping_cart.product_query import ProductQuery
from erpnext.shopping_cart.filters import ProductFiltersBuilder
from vim.api import get_product_info_for_website as get_product_info
from erpnext.e_commerce.shopping_cart.product_info import get_product_info_for_website
from frappe.utils import cstr
from vim.api import sign_up 
from erpnext.e_commerce.shopping_cart.cart import _get_cart_quotation 
from frappe import  _ 
from frappe.utils import escape_html
from frappe.utils.oauth import get_oauth2_flow,get_oauth2_providers,get_info_via_oauth
import base64
import json, jwt

@frappe.whitelist(allow_guest=True)
def get_items(start = 0,per_page = 6,search = "" ) :
	# filter_engine = ProductFiltersBuilder()
	field_filters = None #frappe.parse_json(frappe.form_dict.field_filters)
	attribute_filters = None # frappe.parse_json(frappe.form_dict.attribute_filters)
	# adon_groups = frappe.get_all("Item Group",["name","lft","rgt"],filters = [{"is_party_adons":1}])
	# all_adons = set()
	# for  group in adon_groups :
	# 	subGroups =  frappe.get_list("Item Group",filters = {"lft":[">=",group["lft"]],"rgt":["<=",group["rgt"]]},pluck="name")
	# 	for sub in subGroups :
	# 		all_adons.add(sub)
	
	# start = 0  #frappe.parse_json(frappe.form_dict.start)
	# attribute_filters = filter_engine.get_attribute_fitlers()
	engine = ProductQuery() 
	# frappe.errprint([ engine.fields, engine.filters, engine.or_filters, start, engine.page_length])
	site_name = cstr(frappe.local.site)
	# frappe.errprint(site_name)
	
	filters = {"non_sharable_slot":"0","item_code":["like","%{}%".format(search)],
			 'disabled': 0 , 'show_in_website' : ['=', 1]
	}

	result = frappe.get_all("Item", fields=engine.fields, filters=filters, or_filters=[], start=start, limit=per_page)
	# result =  frappe.get_all("Item", fields=engine.fields, filters={"non_sharable_slot":"0","item_group":["in",all_adons]}, or_filters=[], start=start, limit=per_page)
	for item in result:
			product_info = get_product_info_for_website(item.item_code, skip_quotation_creation=True).get('product_info')
			if product_info:
				item.formatted_price = product_info['price'].get('formatted_price') if product_info['price'] else None
			if item['website_image'] :
				item['website_image'] = site_name+item['website_image']
			if item['image'] :
				item['image'] = site_name+item['image']

	# frappe.errprint(result)
	# items = engine.query(attribute_filters, field_filters, search, start)
	return result


@frappe.whitelist(allow_guest=True)
def get_event_items(start = 0,per_page = 6 ) :
	# filter_engine = ProductFiltersBuilder()
	search = None
	field_filters = None #frappe.parse_json(frappe.form_dict.field_filters)
	attribute_filters = None # frappe.parse_json(frappe.form_dict.attribute_filters)
	# start = 0  #frappe.parse_json(frappe.form_dict.start)
	# attribute_filters = filter_engine.get_attribute_fitlers()
	engine = ProductQuery()
	# frappe.errprint([ engine.fields, engine.filters, engine.or_filters, start, engine.page_length])
	site_name = cstr(frappe.local.site)
	# frappe.errprint(site_name)
	result = frappe.get_all("Item", fields=engine.fields, filters={"non_sharable_slot":"1"}, or_filters=[], start=start, limit=per_page)
	for item in result:
			product_info = get_product_info_for_website(item.item_code, skip_quotation_creation=True).get('product_info')
			if product_info:
				item.formatted_price = product_info['price'].get('formatted_price') if product_info['price'] else None
			if item['website_image'] :
				item['website_image'] = site_name+item['website_image']
			if item['image'] :
				item['image'] = site_name+item['image']

	# frappe.errprint(result)
	# items = engine.query(attribute_filters, field_filters, search, start)
	return result

@frappe.whitelist(allow_guest=True)
def get_product_details(item_code):
	site_name = cstr(frappe.local.site)
	fields  = ['name', 'item_name', 'item_code', 'website_image', 'variant_of', 'has_variants', 'item_group', 'image', 'web_long_description', 'description', 'route','non_sharable_slot',"maximum_sales_quantity","minimum_sales_quantity","dimension_brand"]
	item_info = frappe.get_value("Item",{"item_code":item_code} , fields,as_dict=True)
	# frappe.errprint(item_info)
	if item_info :
			product_info = get_product_info_for_website(item_code, skip_quotation_creation=True).get('product_info')
			if item_info ['website_image'] :
				item_info ['website_image'] = site_name+item_info ['website_image']
			if item_info ['image'] :
				item_info ['image'] = site_name+item_info ['image']
			if product_info :
				item_info["formatted_price"] = product_info['price'].get('formatted_price') if product_info['price'] else None
			uom = []
				# Item = frappe.get_doc('Item',item_code)
			uom_list = frappe.get_all("UOM Conversion Detail",filters={"parent":item_code} , fields=["uom"])

			if uom_list :
				for i in  uom_list:
					uom.append(i.uom)
			item_info["uom_list"] = uom

	return	item_info

@frappe.whitelist(allow_guest=True)
def get_item_group_list():
		filter_engine = ProductFiltersBuilder()
		item_list = filter_engine.get_field_filters()
		return item_list[0][1]
		
@frappe.whitelist(allow_guest=True)
def get_branch_list(brand) :

	branch_list = frappe.db.get_list("Dimension Branch",filters={'brand': brand
			 },pluck="name")
	return branch_list 

	# return {"branch_list":branch_list}


@frappe.whitelist(allow_guest=True)
def sign_up(email, full_name, mobile,city,national_id=None):
	# if not is_signup_enabled():
	# 	frappe.throw(_('Sign Up is disabled'), title='Not Allowed')

	user = frappe.db.get("User", {"email": email}) or frappe.db.get("User", {"mobile_no": mobile})
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

		from frappe.utils import random_string
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

		# if redirect_to:
		# 	frappe.cache().hset('redirect_after_login', user.name, redirect_to)

		if user.flags.email_sent:
			return 1, _("Please check your email for verification")
		else:
			return 2, _("Please ask your administrator to verify your sign-up")



@frappe.whitelist(allow_guest=True)
def get_brand_list(item_code = None):
	brand_list = None
	if item_code :
		brand_list = frappe.db.get_value('Item',item_code, 'dimension_brand')

	# branch_list = frappe.db.get_list('Dimension Branch',
	# fields=['name'],
	# as_list=True
	# )
	return brand_list

@frappe.whitelist(allow_guest=True)
def is_available(item_code = None,visit_date= None,branch = None) :
	if not item_code :return {"message": "Please provide item code"}
	if not visit_date :return {"message": "Please provide visit date"}
	import datetime as dt
	# ev_date = date.today()
	item =  frappe.get_doc("Item", item_code)
	# if not item : return 
	applicable_for = item.applicable_for
	# if applicable_for == "" : return {"available":True}
	weekDays = ("Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday")
	if visit_date :
		ev_date =  dt.datetime.strptime(visit_date,"%Y-%m-%d")
		weekday = weekDays[ev_date.weekday()]
	
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
				return {"available":False,"message":"This event is blocked for the selected event from {} to {} due to {}".format(block_list[0]["block_from"],block_list[0]["block_to"],block_list[0]["reason"]) }
			else :
				return {"available":False,"message":"No events are performed from {} to {} due to {}".format(block_list[0]["block_from"],block_list[0]["block_to"],block_list[0]["reason"]) }
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
							return {"available":False,"message":"Weekday event only, please select Weekend event or select Weekday date"}
						else :
							return {"available":False,"message":"Weekend event only, please select Weekday event or select Weekend date"}
					else : special_day =True
	if rate_for_specific_date_selling and not special_day:
		for dates in rate_for_specific_date_selling :
			if ev_date.date() ==dates.date :
					if dates.rate_applicable != applicable_for:
						if applicable_for == "Weekday":
							return {"available":False,"message":"Weekday event only, please select Weekend event or select Weekday date"}
						else :
							return {"available":False,"message":"Weekend event only, please select Weekday event or select Weekend date"}
					else : special_day =True
	# frappe.errprint([weekends,weekday,special_day])
	if len(weekends) > 0 and not special_day:
		if weekday in weekends:
			if applicable_for == "Weekday":
				return {"available":False,"message":"Weekday event only, please select Weekend event or select Weekday date"}
		elif applicable_for != "Weekday" :
			return {"available":False,"message":"Weekend event only, please select Weekday event or select Weekend date"}
	return {"available":True}

@frappe.whitelist()
def get_customer_Detail():
	if(frappe.session.user !='Guest'):
		from erpnext.portal.utils import create_customer_or_supplier
		create_customer_or_supplier()

		user_data=frappe.get_doc('User',frappe.session.user)
		user=frappe.session.user 
		if user:
			customer = None
			mobile_no = frappe.db.get_value('User', {"email_id": frappe.session.user} , 'mobile_no')
			for d in frappe.get_list("Contact", fields=("name"), filters={"mobile_no": mobile_no}) or frappe.get_list("Contact", fields=("name"), filters={"email_id": user}) :
				contact_name = frappe.db.get_value("Contact", d.name)
				if contact_name:
					contact = frappe.get_doc('Contact', contact_name)
					if not contact.email_id :
						contact.add_email(frappe.session.user, is_primary=True)
						contact.save()
					doctypes = [d.link_doctype for d in contact.links]
					doc_name  = [d.link_name for d in contact.links]
					if  "Customer" in doctypes : 
						cust = doc_name[doctypes.index("Customer")]
						customer = frappe.get_doc('Customer', cust)
			if not customer: 
				customer=frappe.get_doc("Customer", {'name': user_data.first_name})

		
		customer_detail_qry="""select idx,name,relation, dob, person_name, hijri_dob, preferred_communication, favourite_colour, colour, school_name, email_id, phone_no,
		first_name, middle_name, last_name, child, adult, gender, child_name, favorite_character from `tabCustomer Family Detail`
		where parent='{0}'""".format(customer.name)
		cust_details=frappe.db.sql(customer_detail_qry,as_dict=True)
		qry="""select `tabContact`.name 'contact_name' from `tabDynamic Link`
				inner join `tabContact` on `tabContact`.name=`tabDynamic Link`.parent
				where `tabDynamic Link`.link_doctype='Customer' and link_name='{0}'""".format(customer.name)	
		contact=frappe.db.sql(qry,as_dict=True)
		char_qry='select name from `tabCharacters`'
		fav_char=frappe.db.sql(char_qry,as_dict=True)
		colour_qry="select name from `tabColor`"
		color=frappe.db.sql(colour_qry,as_dict=True)
		relation_qry='select name from `tabFamily Relation`'
		relation=frappe.db.sql(relation_qry,as_dict=True)
		prefcomm_qry='select name from `tabPreferred Communication`'
		preferred_communication=frappe.db.sql(prefcomm_qry,as_dict=True)
		country_qry='select name from `tabCountry`'
		country=frappe.db.sql(country_qry,as_dict=True)
		city_qry='select name from `tabCity`'
		city=frappe.db.sql(city_qry,as_dict=True)
		return {'customer':customer,'contact':contact,'user_data':user_data,'cust_details':cust_details,'fav_char':fav_char,'color':color,'relation':relation,'preferred_communication':preferred_communication,'country':country,'city':city}
	else:
		return {"error_code":404,"message":"User Not Found"} 
@frappe.whitelist()
def get_cart(allow_guest=True):
		cart_quotation = _get_cart_quotation()
		return cart_quotation

@frappe.whitelist(allow_guest=True)
def get_slot_list(item_code = None,visit_date= None,branch = None,brand =None, city = None,unit = None) :
	from vim.api import vim_get_slot_list 
	return vim_get_slot_list(item_code = item_code,visit_date= visit_date,branch = branch,brand =brand, city = city,unit = unit) 	

@frappe.whitelist()
def update_in_cart(item_code, qty, additional_notes=None, with_items=False ,slot =None,delivery_date=None,brand=None,branch=None,city=None ,phone =None,uom = None):
	from vim.api import update_cart
	slot_name = frappe.get_value("Item",{"item_code":item_code} , ["non_sharable_slot"],as_dict=True).non_sharable_slot
	if slot_name == 0 : 
		slot = None
		uom = None 
	return update_cart(item_code, qty, additional_notes=additional_notes, with_items=with_items ,slot =slot,delivery_date=delivery_date,brand=brand,branch=branch,city=city ,phone =phone,uom = uom,restapi=True)	


@frappe.whitelist()
def place_order(advance_amount = 0, payment_status = '', transactionid = ''):
	from vim.api import place_order  as vim_place_order
	return vim_place_order(restapi = True,advance_amount = float(advance_amount) if advance_amount else 0, payment_status = payment_status, transactionid = transactionid)	

@frappe.whitelist()
def get_order_details(sales_order):
	doc = frappe.get_doc("Sales Order", sales_order)
	return doc

@frappe.whitelist()
def get_order_list():
	from erpnext.controllers.website_list_for_contact import get_transaction_list
	return get_transaction_list("Sales Order")

@frappe.whitelist(allow_guest=True)
def forgot_passwrod(email_id) :
	user = email_id
	if user=="Administrator":
		return {"reset_link_sent": False, "message":'not allowed for this user'}

	try:
		user = frappe.get_doc("User", user)
		if not user.enabled:
			return {"reset_link_sent": False, "message":'User is disabled'}

		user.validate_reset_password()
		user.reset_password(send_email=True)

		return {"reset_link_sent": True, "message":"Password reset instructions have been sent to your email"}

	except frappe.DoesNotExistError:
		frappe.clear_messages()
		return {"reset_link_sent": False, "message":'User not found'}
	
@frappe.whitelist(allow_guest=True)
def check_internal_user():
	from vim.api import is_internal_user
	return {"is_interanl_user" : is_internal_user()}

# @frappe.whitelist()
# def get_customerdata():
# 	user_doc=frappe.get_doc("User",frappe.session.user)
# 	user= frappe.session.user
# 	if user:
# 		customer = None
# 		for d in frappe.get_all("Contact", fields=("name"), filters={"email_id": user}):
# 			contact_name = frappe.db.get_value("Contact", d.name)
# 			if contact_name:
# 				contact = frappe.get_doc('Contact', contact_name)
# 				doctypes = [d.link_doctype for d in contact.links]
# 				doc_name  = [d.link_name for d in contact.links]
# 				if  "Customer" in doctypes : 
# 					cust = doc_name[doctypes.index("Customer")]
# 					customer = frappe.get_doc('Customer', cust)
	
# 		if not customer:
# 			return {"error":True, "message":"Customer not found please contact admin"}
# 		return {"customer_data" : customer,"user_image":user_doc.user_image}
# 	return {"error":True, "message":"User not found"}

@frappe.whitelist()
def get_customer_phone_list():
	from vim.api import is_internal_user
	if not is_internal_user() : 
		return {"error":True,"message" : "Don't have enough permissions"}
	phone_list = frappe.db.get_list('Customer', filters={
				'mobile_no': ['!=',''],
				'disabled' : 0
			},
			pluck='mobile_no'
			)
	return {"phone_list":phone_list}

@frappe.whitelist(allow_guest=True)
def get_customer_name(phone):
	from vim.api import get_customer
	return {"customoer_name" : get_customer(phone) } 


@frappe.whitelist()
def apply_coupon_code(applied_code):
	applied_referral_sales_partner = False  #If needed in future had to take it as input 
	quotation = True

	if not applied_code:
		return {"error" : True , "message":"Please enter a coupon code" }

	coupon_list = frappe.get_all('Coupon Code', filters={'coupon_code': applied_code})
	if not coupon_list:
		return {"error" : True , "message":"Please enter a valid coupon code" }

	coupon_name = coupon_list[0].name

	def validate_coupon_code(coupon_name):
		coupon = frappe.get_doc("Coupon Code", coupon_name)
		from frappe.utils import  getdate, today
		if coupon.valid_from:
			if coupon.valid_from > getdate(today()):
				return {"error" : True , "message" :_("Sorry, this coupon code's validity has not started") }
		if coupon.valid_upto is not None:
			if coupon.valid_upto < getdate(today()):
				return {"error" : True , "message" :_("Sorry, this coupon code's validity has expired")}
		if coupon.used >= coupon.maximum_use:
			return {"error" : True , "message" :_("Sorry, this coupon code is no longer valid")}
	validate = validate_coupon_code(coupon_name)
	if  validate : return validate
	quotation = _get_cart_quotation()
	if not len(quotation.items) :
		return {"error" : True , "message":"No Item in cart" }
	quotation.coupon_code = coupon_name
	quotation.flags.ignore_permissions = True
	quotation.save()

	if applied_referral_sales_partner:
		sales_partner_list = frappe.get_all('Sales Partner', filters={'referral_code': applied_referral_sales_partner})
		if sales_partner_list:
			sales_partner_name = sales_partner_list[0].name
			quotation.referral_sales_partner = sales_partner_name
			quotation.flags.ignore_permissions = True
			quotation.save()

	return quotation


@frappe.whitelist(allow_guest=True)
def get_unit_wise_price(item_code = None,uom = None) :
	from vim.api import get_price
	return get_price(item_code,uom)

@frappe.whitelist()
def update_data(**kwargs):
	name  = kwargs["name"] if "name" in kwargs else ""
	first_name = kwargs["first_name"] if "first_name" in kwargs else ""
	last_name = kwargs["last_name"] if "last_name" in kwargs else ""
	nationality = kwargs["nationality"] if "nationality" in kwargs else ""
	mobile_no = kwargs["mobile_no"]  if "mobile_no" in kwargs else ""
	city = kwargs["city"]  if "city" in kwargs else ""
	preferred_communication = kwargs["preferred_communication"]  if "preferred_communication" in kwargs else ""
	child_family_details = kwargs["child_family_details"]  if "child_family_details" in kwargs else ""
	adult_family_details = kwargs["adult_family_details"]  if "adult_family_details" in kwargs else ""
	customer_family_detail = kwargs["customer_family_detail"]  if "customer_family_detail" in kwargs else ""
	channel= kwargs["channel"]  if "channel" in kwargs else None
	email= kwargs["email"]  if "email" in kwargs else None
	district= kwargs["district"] if "district" in kwargs else None
	 
	if not name : return {"error": True, "message": "Name shouldn't be blank","data": [kwargs,kwargs.values()]}
	mobile_error_throw = False
	if mobile_no and len(mobile_no) :
		if len(mobile_no) == 9 and mobile_no[0] != '0':
			mobile_no = '0' + mobile_no
		if len(mobile_no) != 10 or mobile_no[0] != '0' :
				mobile_error_throw =True
		else :
			for x in mobile_no :
				if x < '0' or  x > '9' : 
					mobile_error_throw =True
					break

	if mobile_error_throw :
		return {"error":True,"message":"Mobile Number should be of length 10, consists of only numbers 0-9 and start with 0 ", "mobile_no" : mobile_no}
	
	# testquery= """ Select name from `tabCustomer` where name= "{}" """.format(name)
	# testqueryres=frappe.db.sql(testquery,as_dict=True)
	# if True : return testquery,testqueryres
	query="""delete from `tabCustomer Family Detail` where parent='{0}'""".format(name)
	data=frappe.db.sql(query,as_dict=True)
	

	# doc=frappe.get_doc('Customer',name)
	doc = frappe.get_doc("Customer", {'name': name})
	chi=''
	if doc:
		doc.first_name=first_name
		doc.last_name=last_name
		doc.full_name=first_name+' '+last_name
		doc.nationality=nationality
		# doc.mobile_no=str(mobile_no)
		doc.city=city
		doc.preferred_communication=preferred_communication
		doc.favourite_venue = kwargs["favourite_venue"]  if "favourite_venue" in kwargs else ""
		arr_child = []
		if customer_family_detail:
			for i in customer_family_detail:
				if "child" in i and  str(i["child"]) == "1" : 
					arr_child.append(i)
			for j in arr_child:
				query="""select * from `tabCustomer Family Detail` where parent='{0}' 
				and child_name='{1}' and dob='{2}' and name !='{3}'""".format(name,j.get("child_name",""),j.get('dob'),'')
				data=frappe.db.sql(query,as_dict=True)
				if data:
					return {"error":True,"message":"Duplicate Family Details Found For Relation ("+str(j.get('relation'))+")"}
				dftl=doc.append('customer_family_detail')
				dftl.child=j.get("child")
				dftl.dob=j.get("dob","")
				dftl.school_name=j.get("school_name","")
				dftl.child_name=j.get("child_name","")
				dftl.favorite_character=j.get("favorite_character","")
				if j.get("gender") : dftl.gender=j.get("gender","")
				if j.get("favourite_colour") : dftl.favourite_colour=j.get("favourite_colour","")

		arr_adult=[]		
		if customer_family_detail:
			for i in customer_family_detail:
				if "adult" in i and  str(i["adult"]) == "1" : 
					arr_adult.append(i)
			for j in arr_adult:
				personname=j.get("first_name")+' '+j.get("last_name")
				if not j.get("first_name") or  not j.get("last_name"):
					return {"error":True,"message":"Enter First Name & Last name in Family Details for ("+j.get("relation")+")"}
				query="""select * from `tabCustomer Family Detail` where parent='{0}' 
				and person_name='{1}' and dob='{2}' and name !='{3}'""".format(name,personname,j.get('dob'),'')
				data=frappe.db.sql(query,as_dict=True)
				if data:
					return {"error":True,"message":"Duplicate Family Details Found For Relation ("+str(j.get('relation'))+")"}
				dftl=doc.append('customer_family_detail')
				dftl.adult=j.get("adult")
				dftl.dob=j.get("dob")
				dftl.first_name=j.get("first_name")
				dftl.last_name=j.get("last_name")
				dftl.person_name=personname
				dftl.preferred_communication=j.get("preferred_communication")
				dftl.phone_no=j.get("phone_no")		
				dftl.relation=j.get("relation")		
				dftl.email_id=j.get("email_id")	
				if j.get("gender") : dftl.gender=j.get("gender")
				if j.get("favourite_colour") : dftl.favourite_colour=j.get("favourite_colour")	
		doc.flags.ignore_permissions = True
		doc.save()
		profile_data = doc.as_dict()

		

		perc = profile_percetage(profile_data,arr_adult,arr_child)
		coupon_code = None
		if perc == 100 and not doc.first_coupon :
			coupon_code = create_coupon(doc.name)
			from . email_listener import send_first_coupon_mail
			send_first_coupon_mail(subject="Free Coupon for profile completion",coupon= coupon_code)
			# doc.first_coupon == 1
			# doc.save() 
	return {"updated_data":profile_data ,"profile_percetage" : perc ,"coupon_code":coupon_code} 

def profile_percetage(profile_data,arr_adult,arr_child):
			percent = 0
			if (profile_data.get("first_name") and profile_data.get("last_name")  and profile_data.get("email_id") and profile_data.get("preferred_communication") 
				and profile_data.get("nationality") and profile_data.get("city") ) :
				percent += 50
				
			# if (profile_data.user_image) {
			# 	//   percent += 25;
			# 	// }
			if arr_adult :
				percent += 25
				
			if arr_child :
				percent += 25
			
			return percent
@frappe.whitelist()
def get_customerdata():
	if(frappe.session.user !='Guest'):
		from vim.api import create_customer_or_supplier
		create_customer_or_supplier()
	user_doc=frappe.get_doc("User",frappe.session.user)
	user= frappe.session.user
	if user:
		customer = None
		for d in frappe.get_all("Contact", fields=("name"), or_filters={"email_id": user,"user": user}):
			contact_name = frappe.db.get_value("Contact", d.name)
			if contact_name:
				contact = frappe.get_doc('Contact', contact_name)

				if not contact.email_id :
					contact.add_email(frappe.session.user, is_primary=True)
					contact.email_id = frappe.session.user
					for email_row in contact.email_ids :
						if email_row.is_primary and email_row.email_id != frappe.session.user :
							email_row.is_primary = 0
						if not email_row.is_primary and email_row.email_id == frappe.session.user :
							email_row.is_primary = 1
					contact.flags.ignore_permissions = True
					contact.save()
					frappe.db.commit()

				doctypes = [d.link_doctype for d in contact.links]
				doc_name  = [d.link_name for d in contact.links]
				if  "Customer" in doctypes : 
					cust = doc_name[doctypes.index("Customer")]
					customer = frappe.get_doc('Customer', cust)
				# qry="""select `tabContact`.name 'contact_name' from `tabDynamic Link`
				# 			inner join `tabContact` on `tabContact`.name=`tabDynamic Link`.parent
				# 			where `tabDynamic Link`.link_doctype='Customer' and link_name='{0}'""".format(customer.name)	
				# contact=frappe.db.sql(qry,as_dict=True)[0].contact_name
				user_data=frappe.get_doc('User',frappe.session.user)
		update_cust = False
		if customer and not customer.mobile_no :
			customer.mobile_no = user_data.mobile_no
			update_cust = True
		if customer and not customer.email_id :
			customer.email_id = user_data.name
			update_cust = True
		if customer and not customer.first_name :
			customer.first_name  = customer.name.split(" ")[0]
		if customer and not customer.last_name :
			customer.last_name  = customer.name.split(" ")[1] if len(customer.name.split(" ")) > 1 else customer.name.split(" ")[0]
			update_cust = True
		if customer and not customer.city :
			customer.city = user_data.location  
			update_cust = True
		
		if customer :
			arr_child = []
			for i in customer.customer_family_detail:
					if str(i.get("child")) == "1" : 
						arr_child.append(i)
			
			arr_adult=[]		
			for i in customer.customer_family_detail:
				if str(i.get("adult")) == "1" : 
					arr_adult.append(i)
				if i.get("relation") == 'self' :
					if not i.phone_no :
						i.phone_no = customer.mobile_no
						update_cust = True
					if not i.email_id :
						i.email_id = customer.email_id
						update_cust = True
					if not i.preferred_communication :
						i.preferred_communication = customer.preferred_communication
						update_cust = True
					if not i.first_name :
						i.first_name = customer.first_name
						update_cust = True

					if not i.last_name :
						i.last_name = customer.last_name
						update_cust = True

		if update_cust : 
			customer.flags.ignore_permissions = True
			customer.is_first_time_login = 0
			customer.save()
		perc = profile_percetage(customer.as_dict(),arr_adult,arr_child)
		if not customer:
			return {"error":True, "message":"Customer not found please contact admin"}
		return {"customer_data" : customer,"user_image":user_doc.user_image,"profile_percetage" : perc}
	return {"error":True, "message":"User not found"}
	


@frappe.whitelist(allow_guest=True)
def get_country_list() :
	return frappe.get_all("Country",pluck="name")


@frappe.whitelist(allow_guest=True)
def get_city_list() :
	return frappe.get_all("City",pluck="name")
	

@frappe.whitelist(allow_guest=True)
def get_preferred_communication_list() :
	return frappe.get_all("Preferred Communication",pluck="name")
	

@frappe.whitelist(allow_guest=True)
def get_relation_list() :
	return frappe.get_all("Family Relation",pluck="name")


@frappe.whitelist(allow_guest=True)
def get_characters_list() :
	return frappe.get_all("Characters",pluck="name")
	

@frappe.whitelist(allow_guest=True)
def get_color_list() :
	return frappe.get_all("Color",pluck="name")

@frappe.whitelist(allow_guest=True)
def get_country__code_list() :
	c_code='select name,code from `tabCountry`'
	c_code=frappe.db.sql(c_code,as_dict=True)
	return c_code

@frappe.whitelist()
def get_invoice_details(sales_invoice):
	doc = frappe.get_doc("Sales Invoice", sales_invoice)
	return doc

@frappe.whitelist()
def get_invoice_list():
	from erpnext.controllers.website_list_for_contact import get_transaction_list
	return get_transaction_list("Sales Invoice")

@frappe.whitelist()
def reset_password(old_password,new_password) :
	from frappe.core.doctype.user.user import verify_password
	verify_password(old_password)
	user=frappe.get_doc("User",frappe.session.user)
	user.new_password = new_password
	user.save()
	return "Succeeded"

@frappe.whitelist(allow_guest=True)
def get_brand_list() :
	return frappe.get_all("Dimension Brand",pluck="name")	


def create_coupon(customer):
	
	from datetime import date, timedelta
	coupon = frappe.get_doc({
			"doctype":"Coupon Code",
			"pricing_rule": frappe.db.get_value("Selling Settings", None, "coupon_code_default_pricing_rule"),
			"coupon_type" : "Gift Card",
			"coupon_name" :  frappe.generate_hash()[:10].upper(),
			"customer" : customer,
			"valid_upto" : (date.today()+timedelta(days=30)).isoformat()  
		})
	coupon.flags.ignore_permissions = True
	coupon.flags.ignore_password_policy = True
	coupon.coupon_code = coupon.coupon_name

	coupon.save()
	frappe.db.sql("""update `tabCustomer` set first_coupon = '1' where name = "{}" """.format(customer))
	frappe.db.commit()
	return coupon.coupon_code


@frappe.whitelist(allow_guest=True)
def getSocialLogins():
	from frappe.utils.password import get_decrypted_password
	from frappe.utils.html_utils import get_icon_html
	from frappe.utils.oauth import get_oauth_keys
	providers = [i.name for i in frappe.get_all("Social Login Key", filters={"enable_social_login":1})]
	provider_logins = []
	for provider in providers:
		client_id, base_url = frappe.get_value("Social Login Key", provider, ["client_id", "base_url"])
		client_secret = get_decrypted_password("Social Login Key", provider, "client_secret")
		icon = get_icon_html(frappe.get_value("Social Login Key", provider, "icon"), small=True)
		if (get_oauth_keys(provider) and client_secret and client_id and base_url):
			provider_logins.append({
				"name": provider,
				"provider_name": frappe.get_value("Social Login Key", provider, "provider_name"),
				"auth_url": get_oauth2_authorize_url(provider, "/"),
				"icon": icon
			})
	
	return provider_logins


def get_oauth2_providers():
	out = {}
	providers = frappe.get_all("Social Login Key", fields=["*"])
	for provider in providers:
		authorize_url, access_token_url = provider.authorize_url, provider.access_token_url
		# if provider.custom_base_url:
		# 	authorize_url = provider.base_url + provider.authorize_url
		# 	access_token_url = provider.base_url + provider.access_token_url
		out[provider.name] = {
			"flow_params": {
				"name": provider.name,
				"authorize_url": authorize_url,
				"access_token_url": access_token_url,
				"base_url": provider.base_url
			},
			"redirect_uri": provider.redirect_url,
			"api_endpoint": provider.api_endpoint,
		}
		if provider.auth_url_data:
			out[provider.name]["auth_url_data"] = json.loads(provider.auth_url_data)

		if provider.api_endpoint_args:
			out[provider.name]["api_endpoint_args"] = json.loads(provider.api_endpoint_args)

	return out


def get_oauth2_authorize_url(provider, redirect_to):

	flow = get_oauth2_flow(provider)

	state = { "site": frappe.utils.get_url(), "token": frappe.generate_hash(), "redirect_to": redirect_to 	}

	frappe.cache().set_value("{0}:{1}".format(provider, state["token"]), True, expires_in_sec=120)

	# relative to absolute url
	data = {
		"redirect_uri": get_redirect_uri(provider),
		"state": base64.b64encode(bytes(json.dumps(state).encode("utf-8")))
	}

	oauth2_providers = get_oauth2_providers()

	# additional data if any
	data.update(oauth2_providers[provider].get("auth_url_data", {}))

	return flow.get_authorize_url(**data)


def get_redirect_uri(provider):
	keys = frappe.conf.get("{provider}_login".format(provider=provider))

	if keys and keys.get("redirect_uri"):
		# this should be a fully qualified redirect uri
		return keys["redirect_uri"]

	else:
		oauth2_providers = get_oauth2_providers()

		redirect_uri = oauth2_providers[provider]["redirect_uri"]

		# this uses the site's url + the relative redirect uri
		return redirect_uri #frappe.utils.get_url(redirect_uri)
	# return 

@frappe.whitelist(allow_guest=True)
def login_via_oauth2(provider, code, state, decoder=None):
	info = get_info_via_oauth(provider, code, decoder)
	if not info : {"error" : ("Email not verified with {0}").format(provider.title())}
	login_oauth_user(info, provider=provider, state=state)

def get_info_via_oauth(provider, code, decoder=None, id_token=False):
	flow = get_oauth2_flow(provider)
	oauth2_providers = get_oauth2_providers()

	args = {
		"data": {
			"code": code,
			"redirect_uri": get_redirect_uri(provider),
			"grant_type": "authorization_code"
		}
	}

	if decoder:
		args["decoder"] = decoder

	session = flow.get_auth_session(**args)

	if id_token:
		parsed_access = json.loads(session.access_token_response.text)

		token = parsed_access['id_token']

		info = jwt.decode(token, flow.client_secret, verify=False)
	else:
		api_endpoint = oauth2_providers[provider].get("api_endpoint")
		api_endpoint_args = oauth2_providers[provider].get("api_endpoint_args")
		info = session.get(api_endpoint, params=api_endpoint_args).json()

	if not (info.get("email_verified") or info.get("email")):
		return False

	return info

def login_oauth_user(data=None, provider=None, state=None, email_id=None, key=None, generate_login_token=False):
	# NOTE: This could lead to security issue as the signed in user can type any email address in complete_signup
	# if email_id and key:
	# 	data = json.loads(frappe.db.get_temp(key))
	#	# What if data is missing because of an invalid key
	# 	data["email"] = email_id
	#
	# elif not (data.get("email") and get_first_name(data)) and not frappe.db.exists("User", data.get("email")):
	# 	# ask for user email
	# 	key = frappe.db.set_temp(json.dumps(data))
	# 	frappe.db.commit()
	# 	frappe.local.response["type"] = "redirect"
	# 	frappe.local.response["location"] = "/complete_signup?key=" + key
	# 	return

	# json.loads data and state
	from six import string_types
	if isinstance(data, string_types):
		data = json.loads(data)

	if isinstance(state, string_types):
		state = base64.b64decode(state)
		state = json.loads(state.decode("utf-8"))

	if not (state and state["token"]):
		return {"error" : _("Invalid Request. Token is missing"), "http_status_code": 417}
		

	token = frappe.cache().get_value("{0}:{1}".format(provider, state["token"]), expires=True)
	if not token:
		return { "error" : _("Invalid Request. Invalid Token"), "http_status_code"  : 417 }
		

	def get_email(data):
		return data.get("email") or data.get("upn") or data.get("unique_name")

	user = get_email(data)

	if not user:
		return {"error" : _("Invalid Request. Please ensure that your profile has an email address") }
		

	try:
		if update_oauth_user(user, data, provider) is False:
			return 

	except Exception as ex:
		return {"Error" :  "Sorry. Signup from Website is disabled.",
			"success":False, "http_status_code"  :403 }

	frappe.local.login_manager.user = user
	frappe.local.login_manager.post_login()

	# because of a GET request!
	frappe.db.commit()

	if frappe.utils.cint(generate_login_token):
		login_token = frappe.generate_hash(length=32)
		frappe.cache().set_value("login_token:{0}".format(login_token), frappe.local.session.sid, expires_in_sec=120)

		frappe.response["login_token"] = login_token


	else:
		redirect_to = state.get("redirect_to")
		return {
			"desk_user" : frappe.local.response.get('message') == 'Logged In',
			"redirect_to" :redirect_to,
		}

def update_oauth_user(user, data, provider):
	if isinstance(data.get("location"), dict):
		data["location"] = data.get("location").get("name")

	save = False

	if not frappe.db.exists("User", user):

		# is signup disabled?
		if frappe.utils.cint(frappe.db.get_single_value("Website Settings", "disable_signup")):
			return {"error_message": "Signup is disabled" }
		
		def get_first_name(data):
			return data.get("first_name") or data.get("given_name") or data.get("name")

		def get_last_name(data):
			return data.get("last_name") or data.get("family_name")

		def get_email(data):
			return data.get("email") or data.get("upn") or data.get("unique_name")
		save = True
		user = frappe.new_doc("User")
		user.update({
			"doctype":"User",
			"first_name": get_first_name(data),
			"last_name": get_last_name(data),
			"email": get_email(data),
			"gender": (data.get("gender") or "").title(),
			"enabled": 1,
			"new_password": frappe.generate_hash(get_email(data)),
			"location": data.get("location"),
			"user_type": "Website User",
			"user_image": data.get("picture") or data.get("avatar_url")
		})

	else:
		user = frappe.get_doc("User", user)
		if not user.enabled:
			frappe.respond_as_web_page(_('Not Allowed'), _('User {0} is disabled').format(user.email))
			return False

	if provider=="facebook" and not user.get_social_login_userid(provider):
		save = True
		user.set_social_login_userid(provider, userid=data["id"], username=data.get("username"))
		user.update({
			"user_image": "https://graph.facebook.com/{id}/picture".format(id=data["id"])
		})

	elif provider=="google" and not user.get_social_login_userid(provider):
		save = True
		user.set_social_login_userid(provider, userid=data["id"])

	elif provider=="github" and not user.get_social_login_userid(provider):
		save = True
		user.set_social_login_userid(provider, userid=data["id"], username=data.get("login"))

	elif provider=="frappe" and not user.get_social_login_userid(provider):
		save = True
		user.set_social_login_userid(provider, userid=data["sub"])

	elif provider=="office_365" and not user.get_social_login_userid(provider):
		save = True
		user.set_social_login_userid(provider, userid=data["sub"])

	elif provider=="salesforce" and not user.get_social_login_userid(provider):
		save = True
		user.set_social_login_userid(provider, userid="/".join(data["sub"].split("/")[-2:]))

	elif not user.get_social_login_userid(provider):
		save = True
		user_id_property = frappe.db.get_value("Social Login Key", provider, "user_id_property") or "sub"
		user.set_social_login_userid(provider, userid=data[user_id_property])

	if save:
		user.flags.ignore_permissions = True
		user.flags.no_welcome_mail = True

		# set default signup role as per Portal Settings
		default_role = frappe.db.get_single_value("Portal Settings", "default_role")
		if default_role:
			user.add_roles(default_role)

		user.save()

@frappe.whitelist(allow_guest=True)
def resend_welcome(email_id):
	user_doc = frappe.get_doc('User', email_id)
	if user_doc:
		user_doc.send_welcome_mail_to_user()



		