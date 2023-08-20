from __future__ import unicode_literals
import frappe
from frappe import _

@frappe.whitelist()
def validate(self,method):
	if not self.city and self.user:
		user = frappe.get_doc("User",self.user)
		if user.location :
			self.city = user.location

	if not self.mobile_no or not any(new_contact.phone == self.mobile_no for new_contact in self.phone_nos):
			# Set primary mobile if there is no primary mobile number
			if self.user :
				user = frappe.get_doc("User",self.user)
				if user.mobile_no :
					self.add_phone(
						user.mobile_no,
						is_primary_mobile_no=not any(
							new_contact.is_primary_mobile_no == 1 for new_contact in self.phone_nos
						)
					)