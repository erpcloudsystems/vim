import frappe
import json
import requests
import threading

base_url = "https://hyperbill.hyperpay.com"
# base_url = "http://private-anon-c1d913784a-hyperbill.apiary-mock.com"

login_cred = {
		"email": "anup@digitalconnexion.net",
		"password": "Vim@12345***"
		}

headers = {
'Content-Type': 'application/json',
'Accept': 'application/json'
}

class HyperSingleton:
	_instance = None
	_lock = threading.Lock()
	_URL = base_url + '/api/login'
	auth_token = None

	def __new__(cls):
		if cls._instance is None: 
			with cls._lock:
				if not cls._instance:
					cls._instance = super().__new__(cls)
		return cls._instance
	
	def __init__(self) :
		if not self.auth_token :
			self.set_authtoken() 


	def set_authtoken(self) :
			resp = requests.post(self._URL, headers = headers ,data=json.dumps(login_cred))
			tk = json.loads(resp.text)

			if resp.status_code != 200:
				frappe.errprint('error: ' + str(resp.status_code))
			else:
				if tk.get('response'):
					# Mock server has a different output schema
					self.auth_token = tk['response']['data']['accessToken']
				else:
					self.auth_token = tk['data']['accessToken']

	
	def get_authtoken(self) :
		if not self.auth_token : 
			self.set_authtoken() 
		return self.auth_token
	
	def reset_authtoken(self) :
		self.auth_token = None
		self.get_authtoken()

def get_authtoken() :
	hyperbillConnection = HyperSingleton()
	authToken = hyperbillConnection.get_authtoken()
	if not authToken : frappe.throw("Token not created")
	return authToken

def reset_authtoken():
	hyperbillConnection = HyperSingleton()
	hyperbillConnection.reset_authtoken()

def prepare_invoiceData(inv):
		payload = json.dumps({
		"expiration_date": str(inv.delivery_date),
		"payment_type": "DB",
		"merchant_invoice_number": inv.name,
		"name": frappe.get_value("Customer",inv.customer , "customer_pos_id") or frappe.get_value("Customer",inv.customer , "customer_name"),
		"email" :  frappe.get_value("Customer",inv.customer , "email_id") or "",
		"phone": frappe.get_value("Customer",inv.customer , "mobile_no") ,
		"lang": "en",
		# "email_template": "emailTemplate",
		# "sms_template": "smsTemplate",
		# "invoice_template": "invoiceTemplate",
		# "status_template": "statusTemplate",
		"desc" : ' <br>'.join([ ' ,'.join(["Item Id: " + str(item.item_code),"Item Name: " + str(item.item_name), "qty: " + str(item.qty), "amount: " + str(item.amount) ])  for item in frappe.db.get_all("Sales Order Item",
							filters = [{"parent":inv.name}],
							fields = ["item_code", "item_name","qty" , "amount"]
						)] ),
		# "customer_exid": str(inv.customer),
		# "grand_total": str(round(float(inv.advance_amount),2)),
		"amount": str(round(float(inv.advance_amount),2)),
		"vat": str(round(0,2)),
		# "net_discount_total": str(round(0,2)),
		"currency": inv.currency
		})
		return payload


@frappe.whitelist()
def process_submit(doctype,docname) :
	doc = frappe.get_doc(doctype,docname)
	onSumbmitinvoiceSync(doc,"submit")

@frappe.whitelist()
def onSumbmitinvoiceSync(doc,method) :
	# frappe.errprint([doc.advance_amount,not doc.advance_amount or float(doc.advance_amount) == 0 ])
	if not doc.advance_amount or float(doc.advance_amount) == 0 : return
	try :
		post_data = prepare_invoiceData(doc)
		createInvoice(doc.doctype, doc.name , post_data )
	except Exception as e: 
		
		# frappe.db.rollback()
		error = frappe.get_traceback()+ doc.doctype +"  => " + str(doc.name)
		frappe.log_error(error)
		raise Exception(e)
				
@frappe.whitelist()
def send_invoice_link(inv_id) :
	sendResponse = requests.request("GET", base_url + '/api/simpleInvoice/send/' + str(inv_id), headers=headers)
	if str(sendResponse.status_code).startswith('2') : 
		return True
	else:
		frappe.log_error(str(sendResponse))
		return False

@frappe.whitelist()
def recreate_invoice(doc_name) :
	# import pudb; pu.db
	doc = frappe.get_doc('Sales Order', doc_name)
	if not doc:
		return "Sales Order not found!"
	# Close existing invoices if any
	if doc.payment_invoice_id:
		resp = requests.request("PUT", base_url + '/api/simpleInvoice/close/' + str(doc.payment_invoice_id), headers=headers)
	# Create a new invoice
	onSumbmitinvoiceSync(doc, "")

def createInvoice(doctype,docname,payload) :
	token  = get_authtoken()
	headers['Authorization'] = "Bearer " + token
	response = requests.request("POST", base_url + '/api/simpleInvoice' , headers=headers, data=payload)
	status = response.status_code
	response  = response.json()
	if str(status).startswith('2') and  response['data'] :
		id = response['data']['invoice_no']
		url = response['url']
		long_url = response['long_url']

		frappe.db.sql("""Update `tab{0}` A set payment_invoice_id = '{2}' , payment_status = "Pending" , url = '{3}' , long_url = '{4}' where A.name = "{1}" """.format(doctype, docname ,id, url , long_url))
		send_invoice_link(str(id))
		# sendfailed = False
		# if str(sendResponse.status_code).startswith('2') : 
		# 	sendResponse = sendResponse.json()
		# 	if sendResponse.get("status" , False) :
		# 		createPaymentEntry(doctype, docname, id )
		# 	else :
		# 		sendfailed = True
		# else :
		# 	sendfailed = True
		
		# if sendfailed :
		# 	sendResponse = str(sendResponse)
		# 	frappe.log_error(sendResponse)
		# 	response = str(response)
		# 	frappe.log_error(response)
	else :
		# frappe.new_doc("")
		## Error log
		response = str(response)
		frappe.log_error(str(payload) + '\n' + response)
		raise Exception("Some error while creating Invoice. Check error logs for more details.")


# def syncinvoices() :
# 		invoice_list = frappe.db.sql("""select A.name as name from `tabSales Order`
# 		  A where payment_invoice_id  IS NOT NULL and doscstatus = 1 and is_return = 0 and advance_amount > 0  limit 5""",as_dict = True)
		
# 		if len(invoice_list) > 0:
		
# 			for invoice in invoice_list :
# 				try :
# 					inv  = frappe.get_doc("Sales Order",invoice)
# 					post_data = prepare_invoiceData(inv)
# 					createInvoice(inv.doctype,inv.name, invoiceurl , post_data)

# 				except Exception as e: 
					
# 					# frappe.db.rollback()
# 					error = frappe.get_traceback()+" Sales Order => " + str(invoice["name"])
# 					frappe.log_error(error)

def createPaymentEntry(doctype, docname, id) :
	inv = frappe.get_doc(doctype, docname)
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	payement_entry = get_payment_entry("Sales Order",inv.name,party_amount = float(inv.advance_amount))
	payement_entry.hyperbill_reference = id
	payement_entry.save()
	frappe.db.commit()


def checkPaymentStatus() :
	payment_invoice_ids = frappe.db.sql("""select name , payment_invoice_id from `tabSales Order` where payment_status = "Pending" limit 10 """, as_dict = True)
	for  invoice in payment_invoice_ids :
		token  = get_authtoken()
		headers['Authorization'] = "Bearer " + token
		response = requests.request("GET", base_url + '/api/simpleInvoice/retrieve/' + invoice["payment_invoice_id"], headers=headers, )
		status = response.status_code
		response  = response.json()

		if str(status).startswith('2') :
			if  response['data']["status"] == "paid" :

				pe = frappe.get_last_doc('Payment Entry', filters={"hyperbill_reference": invoice["payment_invoice_id"] })
				pe.submit()

				frappe.db.sql("""Update `tab{0}` A set  payment_status = "Paid" where A.name = "{1}" """.format("Sales Order", invoice["name"]))

			# elif response['data']["status"] != "paid" or response['data']["status"] != "pending" :
			# 	dc = frappe.db.get_doc("Sales Order",invoice["name"] )
			# 	onSumbmitinvoiceSync(dc , "Submit")
			elif response['data']["status"] != "declined" :
				frappe.db.sql("""Update `tab{0}` A set  payment_status = "Declined" where A.name = "{1}" """.format("Sales Order", invoice["name"]))
	
				