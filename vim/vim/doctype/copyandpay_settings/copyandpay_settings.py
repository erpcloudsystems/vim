
import frappe

try:
	from urllib.parse import urlencode
	from urllib.request import build_opener, Request, HTTPHandler
	from urllib.error import HTTPError, URLError
except ImportError:
	from urllib import urlencode
	from urllib2 import build_opener, Request, HTTPHandler, HTTPError, URLError
import json
from frappe.model.document import Document
from frappe.utils import get_url, call_hook_method, cint, get_timestamp
from frappe.integrations.utils import (make_get_request, make_post_request, create_request_log,
	create_payment_gateway)
payment_request_name='';entityId='';
class CopyandPaySettings(Document):
	supported_currencies = ["SAR"]
	responseData=[]
	payment_responce=[]
	
	def validate(self):
			create_payment_gateway('CopyandPay')
			call_hook_method('payment_gateway_enabled', gateway='CopyandPay')
			# if not self.flags.ignore_mandatory:
			# 	self.validate_copyandpay_credentails()
	def validate_copyandpay_credentails(self):
			if self.entity_id:
				try:
					make_get_request(url="https://eu-test.oppwa.com/v1/checkouts/payment")
				except Exception:
					frappe.throw(_("Seems API Key or API Secret is wrong !!!"))
	def validate_transaction_currency(self, currency):
			if currency not in self.supported_currencies:
				frappe.throw(_("Please select another payment method. CopyandPay does not support transactions in currency '{0}'").format(currency))

	def get_payment_url(self, **kwargs):
		integration_request = create_request_log(kwargs, "Host", "CopyandPay")	
		payment_request_name=integration_request.reference_docname;entityId=self.entity_id;	
		responseData=request(payment_request_name,entityId)
		if responseData["id"]:
			return get_url("./copyandpay_checkout?token={0}&checkoutId={1}&entityId={2}".format(integration_request.name,responseData["id"],entityId))
		else:
				frappe.errprint(responseData)
	def create_request(self, data):
		self.data = frappe._dict(data)
		
		try:
			self.integration_request = frappe.get_doc("Integration Request", self.data.token)
			
			self.integration_request.update_status(self.data, 'Queued')
			return self.authorize_payment(self.data.checkoutid)

		except Exception:
			frappe.log_error(frappe.get_traceback())
			return{
				"redirect_to": frappe.redirect_to_message(_('Server Error'), _("Seems issue with server's copyandpay config. Don't worry, in case of failure amount will get refunded to your account.")),
				"status": 401
			}
	def authorize_payment(self,checkoutid):
			"""
			An authorization is performed when user’s payment details are successfully authenticated by the bank.
			The money is deducted from the customer’s account, but will not be transferred to the merchant’s account
			until it is explicitly captured by merchant.
			"""
			
			data = json.loads(self.integration_request.data)
			
			try:
				self.integration_request.update_status(data, 'Completed')
				self.flags.status_changed_to = "Completed"

			except:
				frappe.log_error(frappe.get_traceback())
				# failed
				pass

			status = 'Completed'

			redirect_to = data.get('redirect_to') or None
			redirect_message = data.get('redirect_message') or None
			if self.flags.status_changed_to in ("Authorized", "Verified", "Completed"):
				if self.data.reference_doctype and self.data.reference_docname:
					custom_redirect_to = None
					try:
						frappe.flags.data = data
						custom_redirect_to = frappe.get_doc(self.data.reference_doctype,
							self.data.reference_docname).run_method("on_payment_authorized", self.flags.status_changed_to)

					except Exception:
						frappe.log_error(frappe.get_traceback())

					if custom_redirect_to:
						redirect_to = custom_redirect_to

				redirect_url = 'payment-success?doctype={0}&docname={1}'.format(self.data.reference_doctype, self.data.reference_docname)
			else:
				redirect_url = 'payment-failed'

			if redirect_to:
				redirect_url += '&' + urlencode({'redirect_to': redirect_to})
			if redirect_message:
				redirect_url += '&' + urlencode({'redirect_message': redirect_message})

			return {
				"redirect_to": redirect_url,
				"status": status
			}
	
	
@frappe.whitelist()	
def request(ref_doc,entityId):
	if(ref_doc):
		grand_total = frappe.db.get_value("Payment Request", ref_doc, "grand_total")  
		
		url = "https://eu-test.oppwa.com/v1/checkouts"
		data = {
			'entityId' : str(entityId),
			'amount' :int(round(grand_total,0)),
			'currency' : 'SAR',
			'paymentType' : 'DB'
		}
		try:
			opener = build_opener(HTTPHandler)
			request = Request(url, data=urlencode(data).encode('utf-8'))
			request.add_header('Authorization', 'Bearer OGE4Mjk0MTc0YjdlY2IyODAxNGI5Njk5MjIwMDE1Y2N8c3k2S0pzVDg=')
			request.get_method = lambda: 'POST'
			response = opener.open(request)
			return json.loads(response.read());
		except HTTPError as e:
			return json.loads(e.read());
		except URLError as e:
			return e.reason;
responseData = request(payment_request_name,entityId);
print(responseData)
@frappe.whitelist()	
def payment_request(checkout_id):
	url = "https://eu-test.oppwa.com/v1/checkouts/{0}/payment".format(checkout_id)
	url += '?entityId=8a8294174b7ecb28014b9699220015ca'
	try:
		opener = build_opener(HTTPHandler)
		request = Request(url, data=b'')
		request.add_header('Authorization', 'Bearer OGE4Mjk0MTc0YjdlY2IyODAxNGI5Njk5MjIwMDE1Y2N8c3k2S0pzVDg=')
		request.get_method = lambda: 'GET'
		response = opener.open(request)
		return json.loads(response.read());
	except HTTPError as e:
		return json.loads(e.read());
	except URLError as e:
		return e.reason;

# responseData = request();
# print(responseData);