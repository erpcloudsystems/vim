from __future__ import unicode_literals

import frappe,json
from collections import OrderedDict


@frappe.whitelist()
def get_customer_Detail():
	if(frappe.session.user !='Guest'):
		from erpnext.portal.utils import create_customer_or_supplier
		create_customer_or_supplier()

		user_data=frappe.get_doc('User',frappe.session.user)
		user=frappe.session.user 
		if user:
			customer = None
			frappe.errprint(frappe.get_list("Contact", fields=("name"), filters={"email_id": user}))
			for d in frappe.get_list("Contact", fields=("name"), filters={"email_id": user}):
				contact_name = frappe.db.get_value("Contact", d.name)
				if contact_name:
					contact = frappe.get_doc('Contact', contact_name)
					doctypes = [d.link_doctype for d in contact.links]
					doc_name  = [d.link_name for d in contact.links]
					if  "Customer" in doctypes : 
						cust = doc_name[doctypes.index("Customer")]
						customer = frappe.get_doc('Customer', cust)
			# else : 
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
		pass 


@frappe.whitelist()
def update(customer_array=[],arry_adult=[],arry_child=[],delete_list=[]):
	arr_cust=json.loads(customer_array)
	arr_adult=json.loads(arry_adult)
	arr_child=json.loads(arry_child)
	arr_delete=json.loads(delete_list)
	if arr_cust[0]['customer_primary_contact']:
		qry="""select phone from `tabContact Phone` where parent='{0}' and phone='{1}'""".format(arr_cust[0]['customer_primary_contact'],arr_cust[0]['mobile_no'])
		data_contact=frappe.db.sql(qry,as_dict=True)
		if not data_contact:
			contact=frappe.get_doc('Contact',arr_cust[0]['customer_primary_contact'])
			contact.append('phone_nos',{
				'phone':arr_cust[0]['mobile_no'],
				'is_primary_mobile_no':1
			})
			contact.save()
	if arr_delete:
		for j in arr_delete:
			delete_detail="""delete from `tabCustomer Family Detail` where name='{0}' and parent='{1}'""".format(j['name'],arr_cust[0]['name'])
			data_delete=frappe.db.sql(delete_detail,as_dict=True)
	if arr_cust:
		cust_qry="""update `tabCustomer` set first_name='{0}',last_name='{1}',customer_name='{2}',country_code='{3}',mobile_no='{4}',email_id='{5}',
		channel_used_at_registration_time='{6}',city='{7}',nationality='{8}',is_first_time_login='{9}',preferred_communication='{10}',customer_primary_contact='{11}' 
		,district='{12}' where name='{13}'""".format(arr_cust[0]['first_name'],arr_cust[0]['last_name'],
		arr_cust[0]['customer_name'],arr_cust[0]['country_code'],arr_cust[0]['mobile_no'],arr_cust[0]['email_id'],arr_cust[0]['channel_used_at_registartion_time'],
		arr_cust[0]['city'],arr_cust[0]['nationality'],arr_cust[0]['is_first_time_login'],arr_cust[0]['preferred_communication'],arr_cust[0]['customer_primary_contact'],arr_cust[0]['district'],arr_cust[0]['name'])
		data=frappe.db.sql(cust_qry,as_dict=True)
	if arr_adult:
		for i in arr_adult:
			
			if i['name']=='New':
				
				cust=frappe.get_doc('Customer',arr_cust[0]['name'])
				cust.append('customer_family_detail',{	
				'first_name':i['first_name'],
				'last_name':i['last_name'],
				'person_name':i['first_name']+" "+i['last_name'],
				'preferred_communication':i['preferred_communication'],
				'relation':i['relation'],
				'phone_no':i['phone_no'],
				'email_id':i['email_id'],
				'dob':i['dob'],
				'adult':1
				})
				cust.save()
			else:
				if not i['dob']:
					dob= ''	
				else:
					dob=  ",dob ='" + i['dob'] +"'"

				person_name=i['first_name'] +' ' +i['last_name']	
				adult_qry="""update `tabCustomer Family Detail` set first_name='{0}',last_name='{1}',person_name='{8}' ,preferred_communication='{2}',relation='{3}',phone_no='{4}',email_id='{5}'
				{6}  where name='{7}'""".format(i['first_name'],i['last_name'],i['preferred_communication'],i['relation'],i['phone_no'],i['email_id'],dob,i['name'],person_name)
				frappe.errprint(adult_qry)
				adultdata=frappe.db.sql(adult_qry,as_dict=True)

	if arr_child:
		for i in arr_child:
			frappe.errprint(i)
			if i['name']=='New':
				cust=frappe.get_doc('Customer',arr_cust[0]['name'])
				cust.append('customer_family_detail',{	
				'gender':i['gender'],
				'school_name':i['school_name'],
				'child_name':i['child_name'],
				'person_name':i['child_name'],
				'favorite_character':i['favourite_character'],
				'favourite_colour':i['favourite_color'],
				'dob':i['dob'],
				'child':1
				})
				cust.save()
				frappe.errprint('hi')
			else:	
				if not i['dob']:
					dob= ''	
				else:
					dob=  ",dob ='" + i['dob'] +"'"
				adult_qry="""update `tabCustomer Family Detail` set gender='{0}',child_name='{1}',person_name='{1}',school_name='{2}',favorite_character='{3}',favourite_colour='{4}' {5}
				  where name='{6}'""".format(i['gender'],i['child_name'],i['school_name'],i['favourite_character'],i['favourite_color'],dob,i['name'])
				adultdata=frappe.db.sql(adult_qry,as_dict=True)			



		


