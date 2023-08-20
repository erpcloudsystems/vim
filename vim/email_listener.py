import frappe
from frappe.utils import  get_formatted_email
STANDARD_USERS = ("Guest", "Administrator")




def send_first_coupon_mail(subject,coupon, now=None):
		"""send mail with login details"""
		from frappe.utils.user import get_user_fullname

		created_by = get_user_fullname(frappe.session['user'])
		if created_by == "Guest":
			created_by = "Administrator"

		user_doc=frappe.get_doc("User",frappe.session.user)

		sender = frappe.session.user not in STANDARD_USERS and get_formatted_email(frappe.session.user) or None
		message = "Welcome, You have received Coupon code it is valid for 30 days. Your coupon code is "+str(coupon)+ " please dont share this coupon, it is one time use coupon."
		frappe.sendmail(recipients=user_doc.email, sender=sender, subject=subject,
			 message= message, header=[subject, "green"],
			delayed=(not now) if now!=None else user_doc.flags.delay_emails, retry=3)