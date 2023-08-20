from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint
import json
from six import string_types

no_cache = 1
checkout=''
token='';entityId=''
expected_keys = ('amount', 'title', 'description', 'reference_doctype', 'reference_docname',
	'payer_name', 'payer_email', 'order_id','token')
def get_context(context):	
	context.no_cache = 1
	context.checkout=frappe.form_dict['id']
	context.token=frappe.form_dict['token']
	context.entityId=frappe.form_dict['entityId']
	try:
		
		doc = frappe.get_doc("Integration Request", frappe.form_dict['token'])		
		payment_details = json.loads(doc.data)

		for key in expected_keys:
			context[key] = payment_details[key]

		
		context['token'] = frappe.form_dict['token']
		context['amount'] = flt(context['amount'])
		context['subscription_id'] = payment_details['subscription_id'] \
			if payment_details.get('subscription_id') else ''

	except Exception as e:	
		frappe.throw("")
		frappe.redirect_to_message(_('Invalid Token'),
			_('Seems token you are using is invalid!'),
			http_status_code=400, indicator_color='red')

		#frappe.local.flags.redirect_location = frappe.local.response.location
		raise frappe.Redirect
