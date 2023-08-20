from __future__ import unicode_literals, absolute_import
from six.moves import range
from six import string_types
import frappe
import json
from email.utils import formataddr
from frappe.core.utils import get_parent_doc
from frappe.utils import (get_url, get_formatted_email, cint, list_to_str,
	validate_email_address, split_emails, parse_addr, get_datetime)
from frappe.email.email_body import get_message_id
import frappe.email.smtp
import time
from frappe import _
from frappe.utils.background_jobs import enqueue
from frappe.core.doctype.communication.communication import Communication
from frappe.core.doctype.communication.email import get_recipients_cc_and_bcc, validate_email, notify,set_incoming_outgoing_accounts ,get_attach_link
class Customemail(Communication):
	# def prepare_to_notify(self):
	# 	frappe.errprint("self")
	# 	self._prepare_to_notify()
	# 	super(Communication, self).prepare_to_notify()
	def _notify(self, print_html=None, print_format=None, attachments=None,
		recipients=None, cc=None, bcc=None):
		notify(self, print_html, print_format, attachments, recipients, cc, bcc)	
	def notify(doc, print_html=None, print_format=None, attachments=None,
		recipients=None, cc=None, bcc=None):
			
		def prepare_to_notify_(doc, print_html=None, print_format=None, attachments=None):
			"""Prepare to make multipart MIME Email

			:param print_html: Send given value as HTML attachment.
			:param print_format: Attach print format of parent document."""
	
			view_link = frappe.utils.cint(frappe.db.get_value("System Settings", "System Settings", "attach_view_link"))

			if print_format and view_link:
				
					doc.content = get_attach_link(doc, print_format)

				
			set_incoming_outgoing_accounts(doc)

			if not doc.sender:
				doc.sender = doc.outgoing_email_account.email_id

			if not doc.sender_full_name:
				doc.sender_full_name = doc.outgoing_email_account.name or _("Notification")

			if doc.sender:
				# combine for sending to get the format 'Jane <jane@example.com>'
				doc.sender = get_formatted_email(doc.sender_full_name, mail=doc.sender)

			doc.attachments = []

			if print_html or print_format:
				doc.attachments.append({"print_format_attachment":1, "doctype":doc.reference_doctype,
					"name":doc.reference_name, "print_format":print_format, "html":print_html})

			if attachments:
				if isinstance(attachments, string_types):
					attachments = json.loads(attachments)

				for a in attachments:
					if isinstance(a, string_types):
						# is it a filename?
						try:
							# check for both filename and file id
							file_id = frappe.db.get_list('File', or_filters={'file_name': a, 'name': a}, limit=1)
							if not file_id:
								frappe.throw(_("Unable to find attachment {0}").format(a))
							file_id = file_id[0]['name']
							_file = frappe.get_doc("File", file_id)
							_file.get_content()
							# these attachments will be attached on-demand
							# and won't be stored in the message
							doc.attachments.append({"fid": file_id})
						except IOError:
							frappe.throw(_("Unable to find attachment {0}").format(a))
					else:
						doc.attachments.append(a)

		prepare_to_notify_(doc, print_html, print_format, attachments)

		if doc.outgoing_email_account.send_unsubscribe_message:
			unsubscribe_message = _("Leave this conversation")
		else:
			unsubscribe_message = ""
		if not recipients:
			recipients, cc, bcc = get_recipients_cc_and_bcc(doc, recipients, cc, bcc,
		fetched_from_email_account=True)
		
		frappe.sendmail(
			recipients=(recipients or []),
			cc=(cc or []),
			bcc=(bcc or []),
			expose_recipients="header",
			sender=doc.sender,
			reply_to=doc.incoming_email_account,
			subject=doc.subject,
			content=doc.content,
			reference_doctype=doc.reference_doctype,
			reference_name=doc.reference_name,
			attachments=doc.attachments,
			message_id=doc.message_id,
			unsubscribe_message=unsubscribe_message,
			delayed=True,
			communication=doc.name,
			read_receipt=doc.read_receipt,
			is_notification=True if doc.sent_or_received =="Received" else False,
			print_letterhead=frappe.flags.print_letterhead
		)
	