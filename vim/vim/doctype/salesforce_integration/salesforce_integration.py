# Copyright (c) 2022, aavu and contributors
# For license information, please see license.txt
from datetime import datetime
from telnetlib import STATUS
from warnings import filters
import frappe, requests, json, traceback
from frappe.model.document import Document


base_url = ""
username = ""
password = ""
clientid = ""
client_secret = ""
headers = {
		'Accept': 'application/json',
		'content-type': 'application/json',
	}
order_recordcount = 10
customer_recordcount = 10
items_recordcount = 10
pause_sync_process = False

class SalesforceIntegration(Document):
	pass

@frappe.whitelist(allow_guest=True)
def syncOrders():
	
	def prepare_postData(_ords = []):
		data = []
		for ord in _ords:
			
			if not ord.salesforceid or ord.salesforceid == '':
				tmp ={ 
				"PartyId":ord.opportunityid if ord.opportunityid else '',
				"ERPCode": ord.name,
				"AccountERPCode":ord.customer,
				"Amount":str(ord.grand_total),
				"Branch":ord.branch,
				"NumberofGuests": str(ord.no_of_entries),
				"PaymentMethod":"Debit Card",
				"OrderBookedName":ord.name,
				"Status":"Open",
				"OrderDate":str(ord.transaction_date),
				"Items" : [ {"ItemId":item.item_code,"ItemName":item.item_name } for item in frappe.db.get_all("Sales Order Item",
					filters = [{"parent":ord.name}],
					fields = ["item_code", "item_name"]
				)],
				
				"VisitOn":str(ord.delivery_date)
				}

				data.append(tmp)
		return data
	
	get_config()
	if pause_sync_process:
		return "Sync process paused!"

	pay_list = frappe.db.get_list("Payment Entry Reference",filters = [{"docstatus":"1"},{'reference_doctype': 'Sales Order'}],pluck = "reference_name")
	cust_list = frappe.db.get_list("Customer",filters = [{'salesforceid': ["!=",'']},{'salesforceid': ["!=",'1']},{"salesforce_sync_timestamp":["!=",""]},{"salesforce_sync_timestamp":["!=",None]}],pluck = "name")

	orders = frappe.db.get_all("Sales Order", filters = [{"ifnull(salesforceid, '')": ""},{"status": ["!=", "Draft"]},{"name":["in",pay_list]},{"customer":["in",cust_list]}, {"delivery_date":[">=", "20220722"]}],
	 fields = ["name", "transaction_date","branch","no_of_entries", "grand_total", "status", "delivery_date","customer","opportunityid","salesforceid"],
		page_length = order_recordcount)   
	
	post_data = prepare_postData(orders)
	if len(post_data) <= 0:
		return "No data to sync"
	res, sync_time, logid = sendSalesforceReq("/services/apexrest/api/createOrderBooked", post_data)
	
	try:
		if res['message']['statuscode'] == "200" :
			for ord in res["data"][0]["orders"]:
				if "OpportunityId" in ord.keys() and  paymentEntryUpdate(ord["ERPCode"],ord["OpportunityId"]) :
					updateSalesfroceID("Sales Order", ord["ERPCode"], ord["Id"], sync_time,ord["OpportunityId"])

			for ord in res["data"][0]["duplicateOrderBooked"]:
				if "OpportunityId" in ord.keys() and paymentEntryUpdate(ord["ERP Code"],ord["OpportunityId"]) :
					updateSalesfroceID("Sales Order", ord["ERP Code"], ord["SalesforceId"], sync_time,ord["OpportunityId"])
		else:
			raise Exception("Incorrect response schema")
	except:
		logSyncData(docid = logid, status = "Error", resp = res, sync_time = sync_time, err_msg = traceback.format_exc())
	
	return  res

@frappe.whitelist(allow_guest=True)
def syncInvoices():

	def prepare_invoiceData(_invoices = []):
		data = []
		for record in _invoices:
			ord  = frappe.get_doc("Sales Invoice",record["name"])
			check_item_qry = """select soi.item_name, soi.item_code from `tabSales Invoice Item` as soi inner join  `tabItem` as i on soi.item_code = i.item_code  
			where i.salesforceid is null and soi.parent = '{}' """.format(ord.name)

			# unsynced_items = frappe.db.sql(check_item_qry,as_dict = 1)
			# if unsynced_items and len(unsynced_items) and unsynced_items[0]["item_code"] :
			# 	format_items_data_and_send(unsynced_items)

			unsynced_items = frappe.db.sql(check_item_qry,as_dict = 1)
			if unsynced_items and len(unsynced_items) and unsynced_items[0]["item_code"] :
				continue

			if ord:
				temp = {
				"ERPCode":  ord.name,
				"AccountERPCode": ord.customer,
				"PartyId": '',
				"InvoiceDate": str(ord.posting_date),
				"Amount":str(ord.grand_total),
				"pendingAmount": ord.outstanding_amount,
				"Discount": ord.discount_amount,
				"CouponCode": "",
				"Sales Order": '',
				"NumberofGuests": 0,
				"Active": "Yes",
				"Status": "Paid",
				"InvoiceBookedBy": "Employee",
					"Items" : [ {"ItemId":item.item_code,"ItemName":item.item_name,"qty" : int(item.qty) , "SalesforceId" : frappe.get_value("Item",item.item_code , "salesforceid") } for item in frappe.db.get_all("Sales Invoice Item",
							filters = [{"parent":ord.name}],
							fields = ["item_code", "item_name","qty"]
						)],
				"paymentmode" : [ {"Mode": item.mode_of_payment,"Amt":item.amount} for item in frappe.db.get_all("Sales Invoice Payment",
							filters = [{"parent":ord.name}],
							fields = ["mode_of_payment", "amount"]
						)]
					}
				data.append(temp)
		return data
	
	get_config()
	if pause_sync_process:
		return "Sync process paused!"
	cust_list = frappe.db.get_list("Customer",filters = [{'salesforceid': ["!=",'']},{'salesforceid': ["!=",'1']}],pluck = "name")
	invoice_list = frappe.db.sql("""select distinct A.name as name from `tabSales Invoice` A where salesforce_synced = 0 and customer in {0}  limit {1}""".format(tuple(cust_list), order_recordcount),as_dict = True)
	if len(invoice_list) <= 0:
		return "No data to sync"
	post_data = prepare_invoiceData(invoice_list)

	# return post_data
	
	res, sync_time, logid = sendSalesforceReq("/services/apexrest/api/createInvoice", post_data)
	try:		
		if res and res["message"]["statuscode"] == "200":
			for inv in res["data"][0]["Invoices"]:
				updateSalesfroceID("Sales Invoice", inv["ERPCode"], inv["Id"], sync_time)

			for inv in res["data"][0]["duplicateInvoices"]:
				updateSalesfroceID("Sales Invoice", inv["ERP Code"], inv["SalesforceId"], sync_time)

			if len(res["data"][0]["failedInvoices"]) > 0:
				raise Exception("Some records failed")
		else:
			raise Exception("Api Response Error")
	except:
		logSyncData(docid = logid, status = "Error", resp = res, sync_time = sync_time, err_msg = traceback.format_exc())
	
	return  res

def paymentEntryUpdate(sales_order,opportunityid) :
	def prepare_postData(opportunityid,_ords = []):
		data = []
		for ord in _ords:
			tmp ={ 
			"OppId": opportunityid,
			"DownPaymentDate": str(ord["posting_date"]),
			"DownPayment": ord["allocated_amount"]
			}

			data.append(tmp)

		return data

	pay_list = frappe.db.get_all("Payment Entry Reference",filters = [{"docstatus":"1"},{'reference_doctype': 'Sales Order'},
		{'reference_name':sales_order}],fields = ["allocated_amount"])
	pay_list = frappe.db.sql("""SELECT DISTINCT o.posting_date, oi.allocated_amount
			FROM `tabPayment Entry` o
			INNER JOIN `tabPayment Entry Reference` oi ON o.name = oi.parent
			WHERE reference_doctype = 'Sales Order' and reference_name = '{}'
			order by o.posting_date
			limit 1;
			""".format(sales_order),as_dict = 1)
	
	post_data = prepare_postData(opportunityid,pay_list)
	res, sync_time, logid = sendSalesforceReq("/services/apexrest/api/UpdateOpportunityPayment", post_data)
	if res['message']['statuscode'] == "200" :
		if len(res["data"][0]["Opportunities"]) > 0:
			return True
		return False
		
	else :
		return False
			# if paymentEntryUpdate(ord["ERPCode"],ord["OpportunityId"]) :
			# 	updateSalesfroceID("Payment Entry Reference", ord["ERPCode"], ord["Id"], sync_time,ord["OpportunityId"])
	# temp =	 {
	#     "OppId": "opportunityid",
	#     "DownPaymentDate": "2021-12-11",
	#     "DownPayment": 2000
	# 	}
	# return True
@frappe.whitelist(allow_guest=True)
def syncCustomer():

	def prepare_postData(_custs = []):
		data = []
		for cust in _custs:
			tmp = {
				"ERPcode": cust.name,
				"firstName": cust.first_name,
				"MiddleName": cust.middle_name if cust.middle_name else " ",
				"LastName": cust.last_name if cust.last_name else "",
				"Mobile":  cust.mobile_no if cust.mobile_no else "null",
				"Phone": cust.mobile_no,
				"Email": cust.email_id,
				"City": cust.city if cust.city else "Jeddah",
				"District": cust.branch if cust.branch else "null",
				"Nationality": cust.nationality,
				"PreferredCommunication": cust.preferred_communication,
				"Active":"Yes" if not cust.disabled else "No",
				"Contacts": []
			}
			data.append(tmp)

		return data

	get_config()
	if pause_sync_process:
		return "Sync process paused!"

	customers = frappe.db.get_all("Customer",
		filters = [{"salesforce_synced" : 0}, {"salesforceid" : ""}, {"first_name" : ["!=" , ""]}],
		fields = ["name", "first_name", "middle_name", "last_name", "mobile_no", "email_id", "city", "nationality",
				"branch", "preferred_communication"],
		page_length = customer_recordcount
	)

	if len(customers) <= 0:
		return "No data to sync"

	post_data = prepare_postData(customers)
	res, sync_time, logid = sendSalesforceReq("/services/apexrest/api/FamilyAccount", post_data)

	try:		
		if res and res["message"]["statuscode"] == "200":
			for acc in res["data"][0]["accounts"]:
				updateSalesfroceID("Customer", acc["ERPCode"], acc["Id"], sync_time)

			for acc in res["data"][0]["duplicateAccount"]:
				updateSalesfroceID("Customer", acc["ERPCode"], acc["SalesforceId"], sync_time)

			if len(res["data"][0]["failedAccounts"]) > 0 or len(res["data"][0]["failedContacts"]) > 0:
				raise Exception("Some records failed")
		else:
			raise Exception("Api Response Error")
	except:
		logSyncData(docid = logid, status = "Error", resp = res, sync_time = sync_time, err_msg = traceback.format_exc())
	
	return res

@frappe.whitelist(allow_guest=True)
def syncCustomerFamily():
	
	def prepare_postData(_fams = []):
		data = []
		for fam in _fams:
			if not any(fam.cust_name in cust.values() for cust in data):
				data.append(
					{
						"ERPcode": fam.cust_name,
						"SalesforceId": fam.cust_salesforceid,
						"firstName": fam.cust_first_name,
						"MiddleName": fam.cust_middle_name if fam.cust_middle_name else " ",
						"LastName": fam.cust_last_name if fam.cust_last_name else "",
						"Mobile": fam.cust_mobile_no if fam.cust_mobile_no else "null",
						"Phone": fam.cust_mobile_no,
						"Email": fam.cust_email_id,
						"City": fam.cust_city if fam.cust_city else "Jeddah",
						"District": fam.branch if fam.branch else "null",
						"Nationality": fam.cust_nationality,
						"PreferredCommunication": fam.cust_preferred_communication,
						"Active":"Yes" if not fam.cust_disabled else "No",
						"Contacts":[],
						"ContactsUpdate": []
					}
				)

			for cust in data:
				if cust["ERPcode"] == fam.cust_name:
					if fam.salesforceid:
						cust["ContactsUpdate"].append(
							{
								"ERPcode": fam.name,
								"SalesforceId": fam.salesforceid,
								"firstName": fam.person_name.split(" ")[0] if fam.person_name else "",
								"LastName": fam.last_name if fam.last_name else "null",
								"Email": fam.email_id,
								"Phone": fam.phone_no,
								"Mobile": fam.phone_no,
								"PreferredCommunication": fam.preferred_communication,
								"PreferredColor": fam.favourite_colour,
								"Gender": fam.gender if fam.gender else "",
								"Active":"Yes",
								"FamilyRelationship": "Main" if (fam.relation and fam.relation.lower()) == "self" else fam.relation 
							}
						)
					else:
						cust["Contacts"].append(
							{
								"ERPcode": fam.name,
								"firstName": fam.person_name.split(" ")[0] if fam.person_name else "",
								"LastName": fam.last_name if fam.last_name else "null",
								"Email": fam.email_id,
								"Phone": fam.phone_no,
								"Mobile": fam.phone_no,
								"PreferredCommunication": fam.preferred_communication,
								"PreferredColor": fam.favourite_colour,
								"Gender": fam.gender if fam.gender else "",
								"Active":"Yes",
								"FamilyRelationship": "Main" if (fam.relation and fam.relation.lower()) == "self" else fam.relation 
							}
						)
					break
		return data

	get_config()
	if pause_sync_process:
		return "Sync process paused!"

	family = frappe.db.sql("""
		select tcfd.salesforceid,tcfd.name, tcfd.first_name, tcfd.last_name, tcfd.person_name, tcfd.email_id, tcfd.phone_no
		, tcfd.preferred_communication, tcfd.favourite_colour, tcfd.gender, tcfd.relation
		, cust.name 'cust_name', cust.first_name 'cust_first_name', cust.middle_name 'cust_middle_name'
		, cust.last_name 'cust_last_name', cust.mobile_no 'cust_mobile_no', cust.email_id 'cust_email_id'
		, cust.city 'cust_city', cust.nationality 'cust_nationality', cust.branch 'cust_branch'
		, cust.preferred_communication 'cust_preferred_communication', cust.salesforceid 'cust_salesforceid'
		, cust.disabled cust_disabled
		from `tabCustomer Family Detail` as tcfd 
		inner join tabCustomer as cust on tcfd.parent = cust.name
		where (tcfd.salesforce_synced = 0 or cust.salesforce_synced = 0) and cust.salesforceid is not null and cust.salesforceid != 1
		limit """ + str(customer_recordcount) + """;
		""", as_dict = 1)
	
	if len(family) <= 0:
		return "No data to sync"

	post_data = prepare_postData(family)
	res, sync_time, logid = sendSalesforceReq("/services/apexrest/api/UpdateFamilyAccount", post_data)
	
	try:
		# To check if there was an exception or the response was not as expected
		if res and res["message"]["statuscode"] == "200":
			for acc in res["data"][0]["accounts"]:
				updateSalesfroceID("Customer", acc["ERPCode"], acc["Id"], sync_time)
				
			for fam in res["data"][0]["Contacts Inserted"]:
				updateSalesfroceID("Customer Family Detail", fam["ERPCode"], fam["Id"], sync_time)

			for fam in res["data"][0]["duplicateContacts"]:
				updateSalesfroceID("Customer Family Detail", fam["ERPCode"], fam["SalesforceId"], sync_time)

			for fam in res["data"][0]["Contacts updated"]:
				updateSalesfroceID("Customer Family Detail", fam["ERPCode"], fam["Id"], sync_time)

			if len(res["data"][0]["failedAccounts"]) > 0:
				raise Exception("Some records failed")
			
		else:
			raise Exception("Api Response Error")
	except:
		logSyncData(docid = logid, status = "Error", resp = res, sync_time = sync_time, err_msg = traceback.format_exc())

	return res

def get_config():
	config = frappe.get_single('Salesforce Integration')
	global base_url, username, password, clientid, client_secret, order_recordcount, customer_recordcount, pause_sync_process
	base_url = config.base_url
	username = config.username
	password = config.password
	clientid = config.client_id
	client_secret = config.client_secret
	order_recordcount = config.order_batch_count if config.order_batch_count else 10 
	customer_recordcount = config.customer_batch_count if config.customer_batch_count else 10 
	pause_sync_process = config.pause_sync_process
	
	
def get_accesstoken():
	res = requests.post(base_url + "/services/oauth2/token?grant_type=password&client_id=" + clientid + "&client_secret=" + client_secret + "&username=" + username + "&password=" + password + "")
	return res.json()["access_token"]


def sendSalesforceReq(api_end, data):
	_token = get_accesstoken()
	# frappe.errprint(_token)
	headers["Authorization"] = "Bearer " + _token
	headers["Content-Type"] = 'application/json'
	logid = logSyncData(endpoint = api_end, req = data)
	res = {}
	try:
		res = requests.post(base_url + api_end, headers = headers, data= json.dumps(data))
		# frappe.errprint(res)

		if res.status_code == 200:
			res = res.json()
			sync_time = frappe.utils.now()
			if res["message"] and res["message"]["statuscode"] == "200":
				logSyncData(docid = logid, status = "Success", resp = res, sync_time = sync_time)
			else:
				logSyncData(docid = logid, status = "Error", resp = res, sync_time = sync_time, err_msg = "Unexpected Response from API.")
		else:
			raise Exception()
	except Exception as exec:
		sync_time = frappe.utils.now()
		logSyncData(docid = logid, status = "Error", resp = exec, sync_time = sync_time, err_msg = "API server error.")
		res = None
	return res, sync_time, logid


def updateSalesfroceID(doctype, docname, sfID, sync_time,opportunityId =None):
	fields = {
		"salesforceid": sfID,
		"salesforce_sync_timestamp": sync_time,
		"salesforce_synced": 1
	}
	# frappe.errprint([doctype, docname,fields])

	if opportunityId :
		fields["opportunityid"] = opportunityId
	frappe.db.set_value(doctype, docname,fields, update_modified=False)
	frappe.db.commit()


def logSyncData(endpoint = None, req = None, status = None, resp = None, docid = None, sync_time = None, err_msg = None):
	if docid:
		frappe.db.set_value("Salesforce Sync Logs", docid,{
			"status": status,
			"response_body": str(resp),
			"sync_time": sync_time,
			"error_message": err_msg
		}, update_modified=False)
		frappe.db.commit()
	else:
		doc = frappe.new_doc('Salesforce Sync Logs')
		doc.api_endpoint = endpoint
		doc.request_body = str(req)
		doc.insert()
		frappe.db.commit()
		return doc.name


def sendItem(post_data) :
	res, sync_time, logid = sendSalesforceReq("/services/apexrest/api/createProduct", [post_data])
	# frappe.errprint([res, sync_time, logid])

	try:		
		if res and res["message"]["statuscode"] == "200":
			for acc in res["data"][0]["Products"]:
				updateSalesfroceID("Item", acc["ItemName"], acc["Id"], sync_time)

			for acc in res["data"][0]["duplicateProducts"]:
				updateSalesfroceID("Item", acc["ItemName"], acc["SalesforceId"], sync_time)

			if len(res["data"][0]["failedProducts"]) > 0 :
				raise Exception("Some records failed")
		else:
			raise Exception("Api Response Error")
	except:
		logSyncData(docid = logid, status = "Error", resp = res, sync_time = sync_time, err_msg = traceback.format_exc())
	
	return res

@frappe.whitelist(allow_guest=True)
def syncItems():

	# frappe.errprint("sync items")

	get_config()
	if pause_sync_process:
		return "Sync process paused!"

	items = frappe.db.get_all("Item",
		filters = [{"salesforce_synced" : 0}, {"salesforceid" : ""}], 
		fields = ["item_code", "item_name"],
		page_length = items_recordcount
	)
	# frappe.errprint(items)
	if len(items) <= 0:
		return "No data to sync"
	format_items_data_and_send(items)

@frappe.whitelist(allow_guest=True)
def updateItems():


	get_config()
	if pause_sync_process:
		return "Sync process paused!"

	items = frappe.db.get_all("Item",
		filters = [{"salesforce_synced" : 0}, {"salesforceid" : ["!=" , ""]}], 
		fields = ["item_code", "item_name","salesforceid"],
		page_length = items_recordcount
	)

	if len(items) <= 0:
		return "No data to sync"
	def prepare_postData(_items = []):
		data = []
		for item in _items:
			
			tmp =  {
				"SalesforceId": item.get("salesforceid"),
				"ItemId": item.get("item_code"),
				"ItemName": item.get("item_name")
				}
			data.append(tmp)

		return data
	post_data = prepare_postData(items) 
	for data in post_data :
		res, sync_time, logid = sendSalesforceReq("/services/apexrest/api/UpdateProduct", [data])

		try:		
			if res and res["message"]["statuscode"] == "200":
				for acc in res["data"][0]["Products"]:
					updateSalesfroceID("Item", acc["Name"], acc["Id"], sync_time)

				# for acc in res["data"][0]["duplicateProducts"]:
				# 	updateSalesfroceID("Item", acc["Name"], acc["SalesforceId"], sync_time)

				if len(res["data"][0]["failedProducts"]) > 0 :
					raise Exception("Some records failed")
			else:
				raise Exception("Api Response Error" +str(res) )
		except:
			logSyncData(docid = logid, status = "Error", resp = res, sync_time = sync_time, err_msg = traceback.format_exc())
	
	return res



def format_items_data_and_send(items) :
	def prepare_postData(_items = []):
		data = []
		for item in _items:
			
			tmp =  {
				"SalesforceId": "",
				"ItemId": item.get("item_code"),
				"ItemName": item.get("item_name")
				}
			data.append(tmp)

		return data
	post_data = prepare_postData(items)
	for data in post_data :
		sendItem(data)


	
