from __future__ import unicode_literals
import frappe
from frappe import _
from frappe import utils
# from erpnext.erpnext.assets.doctype.asset.asset import *
@frappe.whitelist()
def get_rate(item_code,uom,item_group=None,price_list= "Standard Buying"):
	price_list_rate=0	
	uom_conversion_factor = frappe.db.sql("""select	C.conversion_factor
		from `tabUOM Conversion Detail` C
		inner join `tabItem` I on C.parent = I.name and C.uom = '%s'
		where I.item_code = '%s'""" %( uom,item_code))

	uom_conversion_factor = uom_conversion_factor[0][0] if uom_conversion_factor else 1
	today = frappe.utils.nowdate()
	# price = frappe.get_all("Item Price", fields=["price_list_rate", "uom","currency","valid_from","valid_upto"],
	# or_filters=[["valid_upto", '>=',today],["valid_upto","=", ""],["valid_upto","=", None]],
	# filters={"price_list": price_list, "item_code": item_code, "valid_from": ['<=',today]}
	# )
	# or_price = frappe.get_all("Item Price", pluck="name",
	# 	or_filters={"valid_upto": ['>=',today],"valid_upto": ["is","null"]})
	# 
	price_querry = """select price_list_rate,uom,currency,valid_from,valid_upto from `tabItem Price` where 
	price_list = '{0}' and  item_code = '{1}' and valid_from <= '{2}' and  (valid_upto >= '{2}' or valid_upto is null )  
	""".format(price_list,item_code,today)
	#frappe.errprint(price_querry)
	price = frappe.db.sql(price_querry,as_dict = True)
	# price = frappe.get_all("Item Price", fields=["price_list_rate", "uom","currency","valid_from","valid_upto"],
	# filters={"price_list": price_list, "item_code": item_code, "valid_from": ['<=',today],"name" : ["in" , or_price] })
	#frappe.errprint(price)

	price_conv =1
	if price : 
		if  not  price[0]["uom"]   or price[0]["uom"] != uom:
			price_conv=   frappe.db.sql("""select	C.conversion_factor
			from `tabUOM Conversion Detail` C
			inner join `tabItem` I on C.parent = I.name and C.uom = '%s'
			where I.name = '%s'""" %( price[0]["uom"],item_code))
			
			price_conv = price_conv[0][0] if price_conv else 1
		price_list_rate= price[0]['price_list_rate'] * uom_conversion_factor/price_conv
	return price_list_rate