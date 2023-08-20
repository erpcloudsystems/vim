from __future__ import unicode_literals
import frappe
from frappe import _
from vim.vim.doctype.salesforce_integration.salesforce_integration import sendSalesforceReq, get_config

@frappe.whitelist()
def validate(self,method):
	mobile_error_throw = False
	# if self.mobile_no and len(self.mobile_no) :
	# 	if len(self.mobile_no) != 10 or self.mobile_no[0] != '0' :
	# 			mobile_error_throw =True
	# 	else :
	# 		for x in self.mobile_no :
	# 			if x < '0' or  x > '9' :
	# 				mobile_error_throw =True
	# 				break
	if self.mobile_no and len(self.mobile_no) == 9 :
		self.mobile_no =  '0' + self.mobile_no
 
	if mobile_error_throw :
		frappe.throw("Mobile Number should be of length 10, consists of only numbers 0-9 and start with 0 ")
	
	self.full_name= ' '.join(filter(lambda x: x, [self.first_name, self.middle_name, self.last_name]))
	if self.middle_name:
		self.customer_name= ' '.join(filter(lambda x: x, [self.first_name, self.middle_name, self.last_name])).upper()
	else:
		self.customer_name= ' '.join(filter(lambda x: x, [self.first_name,  self.last_name])).upper()
	if self.city:
		district_name = frappe.db.get_value('City', self.name, ['district_name'])
		if district_name:
			self.district=district_name
	if self.nationality:
		code = frappe.db.get_value('Country', self.nationality, ['code'])
		if code:
			self.country_code=code

	
	if not self.get("customer_family_detail"):
		row = self.append('customer_family_detail', {})
		row.first_name =self.first_name
		row.middle_name =self.middle_name
		row.last_name =self.last_name
		row.person_name =self.customer_name
		row.relation ='self'
		row.adult =1
		row.phone_no =self.mobile_no
		row.email_id =self.email_id
		row.preferred_communication=self.preferred_communication
	if self.get("customer_family_detail"):
		for i in self.get("customer_family_detail"):

			query="""select * from `tabCustomer Family Detail` where parent='{0}' 
			and person_name='{1}' and dob='{2}' and name !='{3}'""".format(self.name,i.person_name,i.dob,i.name)
			
			data=frappe.db.sql(query,as_dict=True)
			
			if data:
				frappe.throw("Duplicate Family Details Found For Row No ("+str(i.idx)+")")
	
	# Manage family Details deletion in salesforce.
	syncSalesforce(self)

def syncSalesforce(self):
	if self.salesforceid:
		old_doc = self.get_doc_before_save()
		deleted_rec = []
		post_data = []

		if not old_doc:
			return

		for fam in old_doc.customer_family_detail:
			is_match = 0
			for curr in self.customer_family_detail:
				if fam.name == curr.name:
					is_match = 1
					break
			if is_match == 0:
				deleted_rec.append(fam)
				
		
		if deleted_rec:
			for fam in deleted_rec:
				if not fam.salesforceid:
					continue

				if not post_data:
					post_data.append(
						{
							"ERPcode": self.name,
							"SalesforceId": self.salesforceid,
							"firstName":"",
							"MiddleName":"",
							"LastName":"",
							"Mobile":"",
							"Phone":"null",
							"Email":"",
							"City":"",
							"District":"",
							"Nationality":"",
							"PreferredCommunication":"",
							"Active":"",
							"Contacts":[],
							"ContactsUpdate": []
						}
					)

				post_data[0]["ContactsUpdate"].append(
					{
						"ERPcode": fam.name,
						"SalesforceId": fam.salesforceid,
						"firstName": fam.first_name if fam.first_name else "",
						"LastName": fam.last_name if fam.last_name else "null",
						"Email": fam.email_id,
						"Phone": fam.phone_no,
						"Mobile": fam.phone_no,
						"PreferredCommunication": fam.preferred_communication,
						"PreferredColor": fam.favourite_colour,
						"Gender": fam.gender if fam.gender else "",
						"Active":"No",
						"FamilyRelationship": "Main" if (fam.relation and fam.relation.lower()) == "self" else fam.relation 
					}
				)

			if post_data:
				get_config()
				res, sync_time, logid = sendSalesforceReq("/services/apexrest/api/UpdateFamilyAccount", post_data)
				if res and res["message"]["statuscode"] == "200":
					pass
				else:
					frappe.throw("Unexpected error while syncing data to salesforce.")

	
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def customer_query(doctype, txt, searchfield, start, page_len, filters):
	from erpnext.controllers.queries import get_match_cond,get_filters_cond 
	conditions = []
	cust_master_name = frappe.defaults.get_user_default("cust_master_name")

	if cust_master_name == "Customer Name":
		fields = ["a.name", "a.customer_group", "a.territory"]
	else:
		fields = ["a.name", "a.customer_name", "a.customer_group", "a.territory"]

	fields = get_fields("Customer", fields)
	searchfields = frappe.get_meta("Customer").get_search_fields()
	searchfields = " or ".join(["a."+field + " like %(txt)s" for field in searchfields])
	return frappe.db.sql("""select {fields} from `tabCustomer` a
	left outer join `tabCustomer Family Detail` b on b.parent = a.name 
		where a.docstatus < 2
			and (({scond}) or b.phone_no like %(_txt)s ) and a.disabled=0
			{fcond} {mcond}
		order by
			if(locate(%(_txt)s, a.name), locate(%(_txt)s, a.name), 99999),
			if(locate(%(_txt)s, a.customer_name), locate(%(_txt)s, a.customer_name), 99999),
			a.idx desc,
			a.name, a.customer_name
		limit %(start)s, %(page_len)s""".format(**{
			"fields": ", ".join(fields),
			"scond": searchfields,
			"mcond": get_match_cond(doctype),
			"fcond": get_filters_cond(doctype, filters, conditions).replace('%', '%%'),
		}), {
			'txt': "%%%s%%" % txt,
			'_txt': txt.replace("%", ""),
			'start': start,
			'page_len': page_len
		})

def get_fields(doctype, fields=None):
	if fields is None:
		fields = []
	meta = frappe.get_meta(doctype)
	search_fields = meta.get_search_fields()
	for i in range(len(search_fields)):
		search_fields[i] = "a."+search_fields[i]
	fields.extend(search_fields)

	if meta.title_field and not meta.title_field.strip() in fields:
		fields.insert(1, meta.title_field.strip())
	from frappe.utils import unique
	return unique(fields)


@frappe.whitelist()
def reset_syncedflag(self,method):
	self.db_set("salesforce_synced", False, notify = False, commit = True, update_modified = False)
	for fam in self.customer_family_detail:
		fam.db_set("salesforce_synced", False, notify = False, commit = True, update_modified = False)

def make_contact(args, is_primary_contact=1):
	mobile_no = frappe.db.get_value('User', {"email": frappe.session.user} , 'mobile_no')
	contact_name = frappe.db.get_value("Contact", {"mobile_no": mobile_no })
	contact = None
	# if len(check_contact) :
	# 	contact = frappe.get_doc("Contact" , check_contact[0]["parent"] )
	if not contact_name :
		contact = frappe.get_doc({
			'doctype': 'Contact',
			'first_name': args.get('name'),
			'is_primary_contact': is_primary_contact,
			'links': [{
				'link_doctype': args.get('doctype'),
				'link_name': args.get('name')
			}]
		})
	else :
		contact = frappe.get_doc('Contact', contact_name)
	contact.is_primary_contact = is_primary_contact
	if args.get('email_id'):
		contact.add_email(args.get('email_id'), is_primary=True)
	if args.get('mobile_no') or mobile_no :
		contact.add_phone(args.get('mobile_no'), is_primary_mobile_no=True)
	contact.save(ignore_permissions=True)

	return contact
	# check_contact = """ select parent from `tabDynamic Link` where link_name = "{}"	and parenttype = "Contact" limit 1 """.format(args.get('name'))
	# check_contact = frappe.db.sql(check_contact,as_dict= True)
	# contact = None
	# if len(check_contact) :
	# 	contact = frappe.get_doc("Contact" , check_contact[0]["parent"] )
	# if not contact :
	# 	contact = frappe.get_doc({
	# 		'doctype': 'Contact',
	# 		'first_name': args.get('name'),
	# 		'is_primary_contact': is_primary_contact,
	# 		'links': [{
	# 			'link_doctype': args.get('doctype'),
	# 			'link_name': args.get('name')
	# 		}]
	# 	})
	# contact.is_primary_contact = is_primary_contact
	# if args.get('email_id'):
	# 	contact.add_email(args.get('email_id'), is_primary=True)
	# if args.get('mobile_no'):
	# 	contact.add_phone(args.get('mobile_no'), is_primary_mobile_no=True)
	# contact.save(ignore_permissions=True)

	# return contact


def after_insert(self,method):
	# frappe.throw("Test")
	# if from_utils :
		# frappe.errprint(self.as_dict())
		if not self.first_name and not self.last_name :
			fullname = self.name
			from erpnext.e_commerce.doctype.e_commerce_settings.e_commerce_settings import get_shopping_cart_settings
			from frappe.utils.nestedset import get_root_of
			self.full_name = fullname
			self.first_name = fullname.split()[0]
			self.last_name = ''.join(fullname.split()[1:]) if len(fullname.split()) > 1 else ""
			self.customer_name =  fullname
			self.customer_type = "Individual"
			cart_settings = get_shopping_cart_settings()
			self.customer_group = cart_settings.default_customer_group
			self.territory = get_root_of("Territory")
			self.save()
			# self.mobile_no = frappe.db.get_value('User', {"email": frappe.session.user} , 'mobile_no')
			# self.email_id = frappe.session.user