from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (strip)
from frappe.utils import flt, cint, get_datetime, add_days, getdate, formatdate,get_time,get_link_to_form,nowdate
from datetime import datetime,timedelta
from cryptography.fernet import Fernet, InvalidToken
from passlib.hash import pbkdf2_sha256, mysql41
from passlib.registry import register_crypt_handler
from passlib.context import CryptContext
from pymysql.constants.ER import DATA_TOO_LONG
from psycopg2.errorcodes import STRING_DATA_RIGHT_TRUNCATION

class LegacyPassword(pbkdf2_sha256):
	name = "frappe_legacy"
	ident = "$frappel$"

	def _calc_checksum(self, secret):
		# check if this is a mysql hash
		# it is possible that we will generate a false positive if the users password happens to be 40 hex chars proceeded
		# by an * char, but this seems highly unlikely
		if not (secret[0] == "*" and len(secret) == 41 and all(c in string.hexdigits for c in secret[1:])):
			secret = mysql41.hash(secret + self.salt.decode('utf-8'))
		return super(LegacyPassword, self)._calc_checksum(secret)
register_crypt_handler(LegacyPassword, force=True)
passlibctx = CryptContext(
	schemes=[
		"pbkdf2_sha256",
		"argon2",
		"frappe_legacy",
	],
	deprecated=[
		"frappe_legacy",
	],
)
# def validate(doc, method):
# def after_insert(doc, method):
	# usr=frappe.session.user    
	# if frappe.db.exists("Employee",{"user_id":usr}):
	# 	emp_doc=frappe.get_doc("Employee",{"user_id":usr})
	# 	if emp_doc.allow_create_coupon:
	# 			if emp_doc.allowed_coupons>0 and (emp_doc.allowed_coupons-emp_doc.availed_coupons)>0:
	# 					emp_doc.availed_coupons=emp_doc.availed_coupons+1
	# 					emp_doc.save()	

def validate(doc, method):
	
	if doc.is_new():
		usr=frappe.session.user    
		if frappe.db.exists("Employee",{"user_id":usr}):
			emp_doc=frappe.get_doc("Employee",{"user_id":usr})
			if emp_doc.allow_create_coupon:
				starting_day_of_current_year = datetime.now().date().replace(month=1, day=1)    
				ending_day_of_current_year = datetime.now().date().replace(month=12, day=31)				
				qry="""select count(name)cnt from `tabCoupon Code` where owner='{0}' and date(valid_from) between date('{1}') and date('{2}') """.format(usr,starting_day_of_current_year.strftime("%Y-%m-%d") ,ending_day_of_current_year.strftime("%Y-%m-%d") )
				frappe.errprint([starting_day_of_current_year.strftime("%Y-%m-%d")])
				couponcount=frappe.db.sql(qry,as_dict = 1)
				coupon_count=0
				if couponcount:
					coupon_count=couponcount[0].cnt
				
				if not emp_doc.allowed_coupons>0 or not (emp_doc.allowed_coupons-coupon_count)>0:
						frappe.throw("""The allowed number of coupons has been exceeded. Allowed:{0} Availed:{1}""".format(emp_doc.allowed_coupons,emp_doc.availed_coupons))

@frappe.whitelist()
def validate_user_permission():
	usr=frappe.session.user
	
	roles = frappe.get_roles(usr)
	cond = "name in (" 
	for role in roles:
		if role != roles[0] : cond += " ,"
		cond += "'" +role + "'"
	cond += ")"
	cond += " and role_name ='Coupon User' order by modified"
	
	sales_manager_roles = frappe.db.sql("""select role_name from `tabRole`  where {cond}""".format(cond=cond),as_dict = 1) 
	
	if  sales_manager_roles:
			return 1
	
	return 0
def check_user_password(user, pwd, doctype='User', fieldname='password', delete_tracker_cache=True):
	'''Checks if user and password are correct, else raises frappe.AuthenticationError'''
	username =frappe.db.sql("""select u.name from tabUser u where u.username='{0}'""".format(user))
	
	auth = frappe.db.sql("""select `name`, `password` from `__Auth`
		where `doctype`=%(doctype)s and `name`=%(name)s and `fieldname`=%(fieldname)s and `encrypted`=0""",
		{'doctype': doctype, 'name': username, 'fieldname': fieldname}, as_dict=True)

	if not auth or not passlibctx.verify(pwd, auth[0].password):
		frappe.throw(_('Incorrect User or Password'))	
	return auth[0].name




	
   