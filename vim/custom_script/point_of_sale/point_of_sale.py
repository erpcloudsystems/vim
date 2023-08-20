
from __future__ import unicode_literals
from ast import If
import frappe
from collections import OrderedDict
from frappe import _
from frappe.utils.nestedset import get_root_of
from frappe.model.document import Document
from datetime import date,timedelta,time
from erpnext.accounts.doctype.pos_profile.pos_profile import get_item_groups 
from erpnext.accounts.doctype.pos_invoice.pos_invoice import get_stock_availability
from erpnext.accounts.doctype.pos_profile.pos_profile import get_item_groups  as si_get_item_groups
from erpnext.accounts.doctype.pricing_rule.pricing_rule import remove_pricing_rule_for_item  ,get_serial_no_for_item,update_args_for_pricing_rule,apply_price_discount_rule
from frappe.utils import cstr, encode
from cryptography.fernet import Fernet, InvalidToken
from passlib.hash import pbkdf2_sha256, mysql41
from passlib.registry import register_crypt_handler
from passlib.context import CryptContext
from pymysql.constants.ER import DATA_TOO_LONG
from psycopg2.errorcodes import STRING_DATA_RIGHT_TRUNCATION
from frappe.utils import cint, flt, get_link_to_form, getdate, today, fmt_money
from frappe.contacts.doctype.contact.contact import get_contact_name
import json
import copy
import re
from erpnext.e_commerce.shopping_cart.cart import  _get_cart_quotation


from six import string_types
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
@frappe.whitelist()
def get_pos_items(start, page_length, price_list, item_group, pos_profile, search_value=""):
	data = dict()
	result = []

	allow_negative_stock = frappe.db.get_single_value('Stock Settings', 'allow_negative_stock')
	warehouse, hide_unavailable_items = frappe.db.get_value('POS Profile', pos_profile, ['warehouse', 'hide_unavailable_items'])

	if not frappe.db.exists('Item Group', item_group):
		item_group = get_root_of('Item Group')

	if search_value:
		data = search_serial_or_batch_or_barcode_number(search_value)

	item_code = data.get("item_code") if data.get("item_code") else search_value
	serial_no = data.get("serial_no") if data.get("serial_no") else ""
	batch_no = data.get("batch_no") if data.get("batch_no") else ""
	barcode = data.get("barcode") if data.get("barcode") else ""
	bundle_item=frappe.db.get_value("Product Bundle", {"new_item_code":item_code},["name"])
	if data:
		item_info = frappe.db.get_value(
			"Item", data.get("item_code"),
			["name as item_code", "item_name", "description", "stock_uom", "image as item_image", "is_stock_item","minimum_sales_quantity","maximum_sales_quantity"]
		, as_dict=1)
		item_info.setdefault('serial_no', serial_no)
		item_info.setdefault('batch_no', batch_no)
		item_info.setdefault('barcode', barcode)
		item_info.setdefault('bundle_item',bundle_item)
		return { 'items': [item_info] }

	condition = get_conditions(item_code, serial_no, batch_no, barcode)
	condition += get_item_group_condition(pos_profile)

	lft, rgt = frappe.db.get_value('Item Group', item_group, ['lft', 'rgt'])

	bin_join_selection, bin_join_condition = "", ""
	if hide_unavailable_items:
		bin_join_selection = ", `tabBin` bin  "
		bin_join_condition = "AND bin.warehouse = %(warehouse)s AND bin.item_code = item.name AND bin.actual_qty > 0"
	items_data = frappe.db.sql("""
		SELECT
			item.name AS item_code,
			item.item_name,
			item.description,
			item.stock_uom,
			item.image AS item_image,
			item.is_stock_item,
			item.minimum_sales_quantity,
			item.maximum_sales_quantity,
			warehouse_reorder_level
		FROM
			`tabItem` item left outer join `tabItem Reorder` reorder on reorder.parent= item.name and 
			reorder.warehouse=%(warehouse)s {bin_join_selection}
		WHERE
			item.disabled = 0
		   and  item.allowed_hrs=0 and item.non_sharable_slot=0 
		--	AND item.is_stock_item = 1
			AND item.has_variants = 0
			AND item.is_sales_item = 1
			AND item.is_fixed_asset = 0
			AND item.item_group in (SELECT name FROM `tabItem Group` WHERE lft >= {lft} AND rgt <= {rgt})
			AND {condition}
			{bin_join_condition}
		ORDER BY
			item.item_name asc
		LIMIT
			{start}, {page_length}"""
		.format(
			start=start,
			page_length=page_length,
			lft=lft,
			rgt=rgt,
			condition=condition,
			bin_join_selection=bin_join_selection,
			bin_join_condition=bin_join_condition
		), {'warehouse': warehouse}, as_dict=1)

	if items_data:
		items = [d.item_code for d in items_data]
		item_prices_data = frappe.get_all("Item Price",
			fields = ["item_code", "price_list_rate", "currency"],
			filters = {'price_list': price_list, 'item_code': ['in', items]})

		item_prices = {}
		for d in item_prices_data:
			item_prices[d.item_code] = d
			
		item_bundles_data = frappe.get_all("Product Bundle",
			fields = ["name","new_item_code"],
			filters = {'new_item_code': ['in', items]})
		
		item_bundles = {}
		for d in item_bundles_data:
			item_bundles[d.new_item_code] = d
		
		for item in items_data:
			item_code = item.item_code
			item_price = item_prices.get(item_code) or {}
			item_bundle=item_bundles.get(item_code) or {}
			if allow_negative_stock:
				item_stock_qty = get_stock_availability(item_code, warehouse)
				#item_stock_qty = frappe.db.sql("""select ifnull(sum(actual_qty), 0) from `tabBin` where item_code = %s""", item_code)[0][0]
			else:
				item_stock_qty = get_stock_availability(item_code, warehouse)

			row = {}
			row.update(item)
			row.update({
				'price_list_rate': item_price.get('price_list_rate'),
				'currency': item_price.get('currency'),
				'actual_qty': item_stock_qty,
				'bundle_item':item_bundle.get('name')
			})
			result.append(row)

	res = {
		'items': result
	}
	
	return res

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs

def item_group_query(doctype, txt, searchfield, start, page_len, filters):
	item_groups = []
	cond = "1=1"
	pos_profile= filters.get('pos_profile')

	if pos_profile:
		item_groups = get_item_groups_pos(pos_profile)

		if item_groups:
			cond = "name in (%s)"%(', '.join(['%s']*len(item_groups)))
			cond = cond % tuple(item_groups)

	return frappe.db.sql(""" select distinct name from `tabItem Group`
			where {condition} and (name like %(txt)s) order by idx  limit {start}, {page_len}"""
		.format(condition = cond, start=start, page_len= page_len),
			{'txt': '%%%s%%' % txt})

def get_item_group_condition(pos_profile):
	cond = "and 1=1"
	item_groups = get_item_groups_pos(pos_profile)
	if item_groups:
		cond = "and item.item_group in (%s)"%(', '.join(['%s']*len(item_groups)))

	return cond % tuple(item_groups)
def get_item_groups_pos(pos_profile):
	item_groups = []
	pos_profile = frappe.get_cached_doc('POS Profile', pos_profile)

	if pos_profile.get('item_groups'):
		# Get items based on the item groups defined in the POS profile
		for data in pos_profile.get('item_groups'):
			item_groups.extend(["%s" % frappe.db.escape(d.name) for d in get_child_nodes('Item Group', data.item_group)])

	return list(set(item_groups))
def get_child_nodes(group_type, root):
	lft, rgt = frappe.db.get_value(group_type, root, ["lft", "rgt"])
	
	return frappe.db.sql(""" Select name, lft, rgt from `tab{tab}` where
			lft = {lft} and rgt = {rgt} order by lft""".format(tab=group_type, lft=lft, rgt=rgt), as_dict=1)

@frappe.whitelist()
def get_past_order_list(search_term, status,pos_profile, limit=20):
	fields = ['name', 'grand_total', 'currency', 'customer', 'posting_time', 'posting_date']
	invoice_list = []

	if search_term and status:
		invoices_by_customer = frappe.db.get_all('POS Invoice', filters={
			'customer': ['like', '%{}%'.format(search_term)],
			'status': status,
			'pos_profile':pos_profile,
			'owner':frappe.session.user
		}, fields=fields)
		invoices_by_name = frappe.db.get_all('POS Invoice', filters={
			'name': ['like', '%{}%'.format(search_term)],
			'status': status,
			'pos_profile':pos_profile,
			'owner':frappe.session.user
		}, fields=fields)

		invoice_list = invoices_by_customer + invoices_by_name
	elif status:
		invoice_list = frappe.db.get_all('POS Invoice', filters={
			'status': status,
			'pos_profile':pos_profile,
			'owner':frappe.session.user
		}, fields=fields)

	return invoice_list
	
@frappe.whitelist()
def get_slot_list(item_name,is_new, delivery_date):
	slotdetail=""
	result_list = []
	
# 	slotdetail="""select slot_name from `tabSlot List` where parent='{0}'  and
# slot_name not in (select slot_name from `tabPOS Invoice Item` posItem inner join `tabPOS Invoice` pos
#  on posItem.parent=pos.name  where pos.docstatus=1 and  pos.posting_date='{1}' and posItem.item_code='{2}' and ifnull(slot_name,'')!='')""".format(item_name,delivery_date,item_name)
	
	slotdetail="""select slot_name from `tabSlot List` where parent='{0}'  and
	slot_name not in (select slot from `tabEvent Booking`  where  date='{1}'and event_item='{2}' )""".format(item_name,delivery_date,item_name)
	
	
	slotdetail= frappe.db.sql(slotdetail, as_dict=1)	
	
	for slot in slotdetail:
		slotdetail_data = OrderedDict()
		slotdetail_data['slot_name'] = slot.get('slot_name') or ''				
		result_list.append(slotdetail_data)
	
	return {'result_list': result_list}	
@frappe.whitelist()	
def get_payment_entry(sorder):
	result_list = []
	items_data=""
	items_data = frappe.db.sql("""
		SELECT			
			sum(allocated_amount) allocated_amount FROM `tabPayment Entry Reference` 	WHERE docstatus=1 and 
		reference_doctype='Sales Order' and reference_name='{0}'
		""".format(sorder),   as_dict=True)	
	
	return {'result_list': items_data}	

@frappe.whitelist()
def get_combo_items(item):
	data = dict()
	item_code=item
	result = []
	cnt_result = []
	items_data=""
	ditems_data=""
	set_count=""
	dresult=[]
	ditems_data = frappe.db.sql("""
		SELECT			
				`tabProduct Bundle Item`.*,0 packed_quantity,tabItem.thumbnail AS item_image,tabItem.item_name from `tabProduct Bundle` inner join `tabProduct Bundle Item` on
				`tabProduct Bundle`.name=`tabProduct Bundle Item`.parent inner join tabItem on tabItem.name=`tabProduct Bundle Item`.item_code  where `tabProduct Bundle Item`.default_item_in_pos=1 and   `tabProduct Bundle`.new_item_code='{0}'
			order by `tabProduct Bundle Item`.idx
		""".format(item_code),   as_dict=True)
	
	for ditem in ditems_data:
		drow = {}
		drow.update(ditem)
		dresult.append(drow)
	items_data = frappe.db.sql("""
		SELECT			
				`tabProduct Bundle Item`.*,0 packed_quantity,tabItem.thumbnail AS item_image,tabItem.item_name from `tabProduct Bundle` inner join `tabProduct Bundle Item` on
				`tabProduct Bundle`.name=`tabProduct Bundle Item`.parent inner join tabItem on tabItem.name=`tabProduct Bundle Item`.item_code  where `tabProduct Bundle Item`.default_item_in_pos=0 and  
				 `tabProduct Bundle`.new_item_code='{0}' order by `tabProduct Bundle Item`.idx
			
		""".format(item_code),   as_dict=True)
	
	for item in items_data:
		row = {}
		row.update(item)
		result.append(row)
		
	set_count=	"""SELECT			
				count(`tabProduct Bundle Item`.name) cnt, set_no from `tabProduct Bundle` inner join `tabProduct Bundle Item` on
				`tabProduct Bundle`.name=`tabProduct Bundle Item`.parent  where`tabProduct Bundle Item`.default_item_in_pos=0 and   `tabProduct Bundle`.new_item_code='{0}'
		group by set_no  """.format(item_code)
	
	set_count= frappe.db.sql(set_count,   as_dict=True)
	for item in set_count:
		row = {}
		row.update(item)
		cnt_result.append(row)
	res = {
		'items': result,'sets':cnt_result,'ditems': dresult
	}
	
	return res
		
		
	
@frappe.whitelist()
def get_items(sorder):
	data = dict()
	result_list = []
	items_data="";packed_list_data=[]

	items_data = frappe.db.sql("""
		SELECT			
				tabItem.name AS item_code,
			item.item_name,
			item.description,
			item.uom,
	  item.stock_uom,
			item.image AS item_image,
			is_stock_item,
			item.rate,			
			item.actual_qty,
			item.qty,
	  item.price_list_rate,item.base_price_list_rate,item.base_rate,item.base_amount,item.base_net_rate,item.base_net_amount,
	  item.base_rate_with_margin,item.actual_qty,item.valuation_rate,item.conversion_factor,item.net_rate,item.net_amount
		FROM
			`tabSales Order Item` item inner join tabItem on item.item_code=tabItem.item_code
		WHERE
		
			item.parent='{0}'
			
		ORDER BY
			item.name asc
		""".format(sorder),   as_dict=True)	
	if items_data:
		items = [d.item_code for d in items_data]
		item_bundles_data = frappe.get_all("Product Bundle",
				fields = ["name","new_item_code"],
			 filters = {'new_item_code': ['in', items]})
		
		item_bundles = {}
		for d in item_bundles_data:
				item_bundles[d.new_item_code] = d
		for item in items_data:
			item_code = item.item_code            
			item_bundle=item_bundles.get(item_code) or {}
			row = {}
			row.update(item)
			row.update({                
				'bundle_item':item_bundle.get('name')
			})
			
			result_list.append(row)
		packed_item_dta=frappe.get_all("Packed Item",
				fields = ["parent_item","item_code","qty"],
			 filters = {'parent_item': ['in', items],'parent':sorder,'parenttype':'Sales Order'})
		item_bundles_detail = frappe.get_all("Product Bundle Item",
			fields = ["name","parent","item_code","default_item_in_pos","set_no","qty","uom"],
			 filters = {'parent': ['in', items]})
		packed_data = {};packed_data_so = {}
		for p in packed_item_dta:
				for b in item_bundles_detail:
						if b.item_code==p.item_code and b.parent==p.parent_item:
								packed_data[b.item_code] = b
								packed_data_so[p.item_code] = p
		for pitem in packed_item_dta:
				pitem_code = pitem.item_code 
				pitem_qty=pitem.qty 
				pitem_bundle=packed_data.get(pitem_code) or {}				
				prow = {};
				prow.update(pitem)
		
				prow.update({                
				'parent_item':pitem_bundle.get('parent'),
				'item_code':pitem_bundle.get('item_code'),
				'default_item_in_pos':pitem_bundle.get('default_item_in_pos'),
				'set_no':pitem_bundle.get('set_no'),
				'qty':pitem_bundle.get('qty'),
				'uom':pitem_bundle.get('uom'),
				'packed_quantity':pitem_qty

			})
		
				packed_list_data.append(prow)	
	return {'result_list': result_list,
	'packed_list_data':packed_list_data}	
		


@frappe.whitelist()
def search_serial_or_batch_or_barcode_number(search_value):
	# search barcode no
	barcode_data = frappe.db.get_value('Item Barcode', {'barcode': search_value}, ['barcode', 'parent as item_code'], as_dict=True)
	if barcode_data:
		return barcode_data

	# search serial no
	serial_no_data = frappe.db.get_value('Serial No', search_value, ['name as serial_no', 'item_code'], as_dict=True)
	if serial_no_data:
		return serial_no_data

	# search batch no
	batch_no_data = frappe.db.get_value('Batch', search_value, ['name as batch_no', 'item as item_code'], as_dict=True)
	if batch_no_data:
		return batch_no_data

	return {}

def get_conditions(item_code, serial_no, batch_no, barcode):
	if serial_no or batch_no or barcode:
		return "item.name = {0}".format(frappe.db.escape(item_code))

	return make_condition(item_code)

def make_condition(item_code):
	condition = "("
	condition += """item.name like {item_code}
		or item.item_name like {item_code}""".format(item_code = frappe.db.escape('%' + item_code + '%'))
	condition += add_search_fields_condition(item_code)
	condition += ")"

	return condition

def add_search_fields_condition(item_code):
	condition = ''
	search_fields = frappe.get_all('POS Search Fields', fields = ['fieldname'])
	if search_fields:
		for field in search_fields:
			condition += " or item.{0} like {1}".format(field['fieldname'], frappe.db.escape('%' + item_code + '%'))
	return condition

@frappe.whitelist()
def create_event_booking(pos_invoice,event,posting_date,slot,brand,city,branch,department=''):
	import json
	
	if(slot):
		doc = frappe.new_doc('Event Booking')
		doc.subject =str(event)+'-'+str(posting_date)+'-'+str(brand)+'-'+str(city)+'-'+str(branch)+'-'+str(slot)	
		doc.event_item=str(event)
		doc.slot=str(slot)
		doc.date=posting_date
		doc.reference_name="POS Invoice"      
		doc.reference_id=  pos_invoice 
		doc.department=department
		doc.brand=brand
		doc.city=city
		doc.branch=branch
		doc.insert()

@frappe.whitelist()
def update_Item(event):
	import json
	doc =	 frappe.get_doc('Item', {'name': event})
	if doc.reusable_item:
		doc.used_count = doc.used_count+1
		doc.save()


@frappe.whitelist()
def update_POS(pos_invoice,brand,city,branch,slot,event,department=''):
	import json
	
	doc =	 frappe.get_doc('POS Invoice', {'name': pos_invoice})	
	doc.brand = brand
	doc.city = city
	doc.branch = branch
	doc.department = department
	doc.save()
	docslot =	 frappe.get_doc('Slot List', {'slot_name': slot,'parent':event})
	item_name=frappe.db.get_value('Item', event, ['item_name'])
	docitem =	 frappe.get_doc('POS Invoice Item', {'parent': pos_invoice,'item_name':item_name})
	
	docitem.slot_name = slot
	docitem.item_start_time=docslot.start_time
	docitem.save()
	
@frappe.whitelist()
def update_accounting_dimension	(sales_order,pos_invoice):    
	docso =	 frappe.get_doc('Sales Order', {'name': sales_order})    
	doc =	 frappe.get_doc('POS Invoice', {'name': pos_invoice})	
	doc.brand = docso.brand
	doc.city = docso.city
	doc.branch = docso.branch
	doc.department = docso.department
	doc.save()

	for ds in docso.items:
		if ds.is_nonsharable_item:
			docitem =	 frappe.get_doc('POS Invoice Item', {'parent': pos_invoice,'item_code':ds.item_code})	
			if(ds.slot_name):
				docslot =	 frappe.get_doc('Slot List', {'slot_name': ds.slot_name,'parent':ds.item_code})
				docitem.slot_name = ds.slot_name
				docitem.item_start_time=docslot.start_time
				docitem.sales_order=sales_order
				docitem.save()
	docso.pos_status="Executed"
	docso.pos__invoice=pos_invoice
	docso.save()	
@frappe.whitelist()
def update_customer_branch(customer,pos_profile):
	
	warehouse = frappe.db.get_value('POS Profile', pos_profile, ['warehouse'])
	dimbranch =	 frappe.get_value('Dimension Branch', {'default_warehouse': warehouse})
	
	docso =	 frappe.get_doc('Customer', {'name': customer})
	docso.branch=dimbranch
	#docso.channel_used_at_registration_time='Walk In'

	docso.save()
	
	

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def event_query(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""
		SELECT item.Item_Code,item.item_name
		FROM `tabItem` item
		WHERE (item.allowed_hrs>0 or item.non_sharable_slot=1) 
		AND item.is_stock_item = 1
			AND item.has_variants = 0
			AND item.is_sales_item = 1
			AND item.is_fixed_asset = 0 
			AND ({key} LIKE %(txt)s)
			ORDER BY
			IF(LOCATE(%(_txt)s, name), LOCATE(%(_txt)s, name), 99999),
			name
		LIMIT %(start)s, %(page_len)s
	""".format(**{
			'key': searchfield
		}), {
		'txt': "%{}%".format(txt),
		'_txt': txt.replace("%", ""),
		'start': start,
		'page_len': page_len
	})
	# return frappe.db.sql("""
	# 	SELECT name, lead_name, company_name
	# 	FROM `tabLead`
	# 	WHERE docstatus &lt; 2
	# 		AND ifnull(status, '') != 'Converted'
	# 		AND ({key} LIKE %(txt)s
	# 			OR lead_name LIKE %(txt)s
	# 			OR company_name LIKE %(txt)s)
			
	# 	ORDER BY
	# 		IF(LOCATE(%(_txt)s, name), LOCATE(%(_txt)s, name), 99999),
	# 		name
	# 	LIMIT %(start)s, %(page_len)s
	# """.format(**{
	# 		'key': searchfield
	# 	}), {
	# 	'txt': "%{}%".format(txt),
	# 	'_txt': txt.replace("%", ""),
	# 	'start': start,
	# 	'page_len': page_len
	# })
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def so_query(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""
		SELECT name,customer,pos_status,delivery_date,docstatus
		FROM `tabSales Order` 
		WHERE docstatus = 1
			AND ({key} LIKE %(txt)s)
			ORDER BY
			IF(LOCATE(%(_txt)s, name), LOCATE(%(_txt)s, name), 99999),
			name
		LIMIT %(start)s, %(page_len)s
	""".format(**{
			'key': searchfield
		}), {
		'txt': "%{}%".format(txt),
		'_txt': txt.replace("%", ""),
		'start': start,
		'page_len': page_len
	})
	
@frappe.whitelist()
def get_item_group(pos_profile):	

	item_group_dict = {}
	item_sub_group_dict = {}
	item_groups = frappe.db.sql("""Select `ig`.`name`,`pig`.`idx`
		from `tabItem Group` as `ig`
		inner join `tabPOS Item Group` as `pig`
			on `ig`.`name` = `pig`.`item_group`
		where `pig`.`parent` = '{0}' and parent_item_group='All Item Groups'
		order by `pig`.idx""".format(pos_profile), as_dict=1)

	for data in item_groups:
		item_group_dict[data.name] = [data.lft, data.rgt]
	item_sub_groups = frappe.db.sql("""Select `ig`.`name`,`pig`.`idx`,`ig`.`parent_item_group`
		from `tabItem Group` as `ig`
		inner join `tabPOS Item Group` as `pig`
			on `ig`.`name` = `pig`.`item_group`
		where `pig`.`parent` = '{0}' and parent_item_group!='All Item Groups'
		order by `pig`.idx""".format(pos_profile), as_dict=1)
	
	for data in item_sub_groups:
		item_sub_group_dict[data.name] = [data.lft, data.rgt]
	return {'item_group_dict': item_group_dict,
			 'item_sub_group_dict'  : item_sub_groups}
@frappe.whitelist()
def get_item_sub_group(pos_profile,item_group):	

	item_sub_group_dict = {}
	item_sub_groups = frappe.db.sql("""Select `ig`.`name`
		from `tabItem Group` as `ig`
		inner join `tabPOS Item Group` as `pig`
			on `ig`.`name` = `pig`.`item_group`
		where  parent_item_group='{0}' and `pig`.`parent` = '{1}' order by `pig`.idx
		""".format(item_group,pos_profile), as_dict=1)
	
	for data in item_sub_groups:
		item_sub_group_dict[data.name] = [data.lft, data.rgt]
	return {'item_sub_group_dict'  : item_sub_groups}	

# @frappe.whitelist(allow_guest=True)
# def get_branch_list(brand):

# 	  branch_list = frappe.db.get_list('Dimension Branch',
# 	  fields=['name'],filters={"brand" : brand},
# 	  as_list=True
# 	  )	  
# 	  return {"branch_list":branch_list}

@frappe.whitelist()
def validate_user_permission(appuser,apppassword):
	usr=check_user_password(appuser,apppassword)
	
	roles = frappe.get_roles(usr)
	cond = "name in (" 
	for role in roles:
		if role != roles[0] : cond += " ,"
		cond += "'" +role + "'"
	cond += ")"
	cond += " and role_name ='POS Invoice approval for discount' order by modified"
	
	sales_manager_roles = frappe.db.sql("""select role_name from `tabRole`  where {cond}""".format(cond=cond),as_dict = 1) 
	
	if  sales_manager_roles:
			return 1
	
	return 0
@frappe.whitelist()
def get_return_packed_items(pos_invoice):
	result_list = []
	items_data=""
	items_data = frappe.db.sql("""
		SELECT parent_item, item_code,set_no, sum(packed_quantity) packed_quantity
FROM vimdev.`tabSelected Packed Items` inner join `tabPOS Invoice` on `tabPOS Invoice`.name=`tabSelected Packed Items`.parent   where `tabPOS Invoice`.return_against='{0}'
group by parent_item, item_code,set_no
		""".format(pos_invoice),   as_dict=True)
	
   
	for slot in items_data:
			items_data_detail = OrderedDict()
			items_data_detail['parent_item'] = slot.get('parent_item') or ''	
			items_data_detail['item_code'] = slot.get('item_code') or ''	
			items_data_detail['set_no'] = slot.get('set_no') or ''	
			items_data_detail['packed_quantity'] = slot.get('packed_quantity') or ''

			result_list.append(items_data_detail)
		   
	return {'result_list': items_data}
@frappe.whitelist()
def get_pos_from_rfid(rfid):
	
	return frappe.db.sql("""
		SELECT rfid,`tabCustomer RFID`.sales_order,`tabCustomer RFID`.pos_invoice,`tabCustomer RFID`.customer,`tabPOS Invoice`.creation   from `tabCustomer RFID Child` inner join  `tabCustomer RFID` on `tabCustomer RFID Child`.parent=`tabCustomer RFID`.name 
	inner join `tabPOS Invoice` on `tabPOS Invoice`.name=`tabCustomer RFID`.pos_invoice  where rfid='{0}'

		""".format(rfid),   as_dict=True)
		
@frappe.whitelist()
def decrypt(pwd):
	cipher_suite = Fernet(encode(get_encryption_key()))
	plain_text = cstr(cipher_suite.decrypt(encode(pwd)))
	
	return plain_text
def get_encryption_key():
	from frappe.installer import update_site_config
 
	if 'encryption_key' not in frappe.local.conf:
		encryption_key = Fernet.generate_key()
		update_site_config('encryption_key', encryption_key)
		frappe.local.conf.encryption_key = encryption_key
 
	return frappe.local.conf.encryption_key
def check_user_password(user, pwd, doctype='User', fieldname='password', delete_tracker_cache=True):
	'''Checks if user and password are correct, else raises frappe.AuthenticationError'''
	username =frappe.db.sql("""select u.name from tabUser u where u.username='{0}'""".format(user))
	
	auth = frappe.db.sql("""select `name`, `password` from `__Auth`
		where `doctype`=%(doctype)s and `name`=%(name)s and `fieldname`=%(fieldname)s and `encrypted`=0""",
		{'doctype': doctype, 'name': username, 'fieldname': fieldname}, as_dict=True)

	if not auth or not passlibctx.verify(pwd, auth[0].password):
		frappe.throw(_('Incorrect User or Password'))	
	return auth[0].name
# @frappe.whitelist(allow_guest=True)
# def apply_coupon_code(applied_code):
# 	quotation = True
	
# 	if not applied_code:
# 		frappe.throw(_("Please enter a coupon code eeeeeeeeeeeeeee"))

# 	coupon_list = frappe.get_all('Coupon Code', filters={'coupon_code': applied_code.upper()})
# 	if not coupon_list:
# 		frappe.throw(_("Please enter a valid coupon code"))

# 	coupon_name = coupon_list[0].name

# 	# from erpnext.accounts.doctype.pricing_rule.utils import validate_coupon_code
# 	validate_coupon_code(coupon_name)

# 	return quotation
# def validate_coupon_code(coupon_name):
# 	coupon = frappe.get_doc("Coupon Code", coupon_name)
# 	frappe.errprint([coupon,"coupon"])
# 	if coupon.valid_from:
# 		if coupon.valid_from > getdate(today()):
# 			frappe.throw(_("Sorry, this coupon code's validity has not started"))
# 	elif coupon.valid_upto:
# 		if coupon.valid_upto < getdate(today()):
# 			frappe.throw(_("Sorry, this coupon code's validity has expired"))
# 	elif coupon.used >= coupon.maximum_use:
# 		frappe.throw(_("Sorry, this coupon code is no longer valid"))

@frappe.whitelist()
def apply_pricing_rule(args, doc=None):
	"""
		args = {
			"items": [{"doctype": "", "name": "", "item_code": "", "brand": "", "item_group": ""}, ...],
			"customer": "something",
			"customer_group": "something",
			"territory": "something",
			"supplier": "something",
			"supplier_group": "something",
			"currency": "something",
			"conversion_rate": "something",
			"price_list": "something",
			"plc_conversion_rate": "something",
			"company": "something",
			"transaction_date": "something",
			"campaign": "something",
			"sales_partner": "something",
			"ignore_pricing_rule": "something"
		}
	"""

	if isinstance(args, string_types):
		args = json.loads(args)

	args = frappe._dict(args)

	if not args.transaction_type:
		args.transaction_type = "selling"

	# list of dictionaries
	out = []

	

	item_list = args.get("items")
	args.pop("items")
	
	set_serial_nos_based_on_fifo = frappe.db.get_single_value("Stock Settings",
		"automatically_set_serial_nos_based_on_fifo")

	for item in item_list:
		args_copy = copy.deepcopy(args)
		args_copy.update(item)
		data = get_pricing_rule_for_item(args_copy, item.get('price_list_rate'), doc=doc)
		
		out.append(data)
		
		# if not item.get("serial_no") and set_serial_nos_based_on_fifo and not args.get('is_return'):
		# 	out[0].update(get_serial_no_for_item(args_copy))

	return out
def get_pricing_rule_for_item(args, price_list_rate=0, doc=None, for_validate=False):
	from erpnext.accounts.doctype.pricing_rule.utils import (get_pricing_rules,
			get_applied_pricing_rules, get_pricing_rule_items, get_product_discount_rule)

	if isinstance(doc, string_types):
		doc = json.loads(doc)

	if doc:
		doc = frappe.get_doc(doc)

	if (args.get('is_free_item') or
		args.get("parenttype") == "Material Request"): return {}
	
	item_details = frappe._dict({
		"doctype": args.doctype,
		"has_margin": False,
		"name": args.name,
		"free_item_data": [],
		"parent": args.parent,
		"parenttype": args.parenttype,
		"child_docname": args.get('child_docname')
	})
	
	if args.ignore_pricing_rule or not args.item_code:
		if frappe.db.exists(args.doctype, args.name) and args.get("pricing_rules"):
			item_details = remove_pricing_rule_for_item(args.get("pricing_rules"),
				
				item_details, args.get('item_code'))
		
		return item_details

	update_args_for_pricing_rule(args)

	pricing_rules = (get_applied_pricing_rules(args.get('pricing_rules'))
		if for_validate and args.get("pricing_rules") else get_pricing_rules(args, doc))
	
	if pricing_rules:
		rules = []

		for pricing_rule in pricing_rules:
			if not pricing_rule: continue
			
			coupon_code= doc.couponcode
			#frappe.db.get_value('Coupon Code', {"pricing_rule":pricing_rule.name}, ['coupon_code'])	
			coupon_code_list = frappe.db.get_list('Coupon Code', {"pricing_rule":pricing_rule.name}, pluck = "coupon_code")
			pricing_rule_coupon=frappe.db.get_value('Coupon Code', {"coupon_code":coupon_code}, ['pricing_rule'])	
			if doc.couponcode.upper()==coupon_code.upper() or doc.couponcode.upper() in coupon_code_list or doc.couponcode in coupon_code_list:
				
				if isinstance(pricing_rule, string_types):
					pricing_rule = frappe.get_cached_doc("Pricing Rule", pricing_rule)
					pricing_rule.apply_rule_on_other_items = get_pricing_rule_items(pricing_rule)

					if pricing_rule.get('suggestion'): continue
				
				item_details.validate_applied_rule = pricing_rule.get("validate_applied_rule", 0)
				item_details.price_or_product_discount = pricing_rule.get("price_or_product_discount")

				rules.append(get_pricing_rule_details(args, pricing_rule))

				if pricing_rule.mixed_conditions or pricing_rule.apply_rule_on_other:
					item_details.update({
						'apply_rule_on_other_items': json.dumps(pricing_rule.apply_rule_on_other_items),
						'price_or_product_discount': pricing_rule.price_or_product_discount,
						'apply_rule_on': (frappe.scrub(pricing_rule.apply_rule_on_other)
							if pricing_rule.apply_rule_on_other else frappe.scrub(pricing_rule.get('apply_on')))
					})

				if pricing_rule.coupon_code_based==1 and args.coupon_code==None:
					return item_details
				if pricing_rule.coupon_code_based==1 and pricing_rule.name==pricing_rule_coupon:
					if not pricing_rule.validate_applied_rule:
						if pricing_rule.price_or_product_discount == "Price":
							apply_price_discount_rule(pricing_rule, item_details, args)
						else:
							get_product_discount_rule(pricing_rule, item_details, args, doc)
			
		if not item_details.get("has_margin"):
			item_details.margin_type = None
			item_details.margin_rate_or_amount = 0.0

		item_details.has_pricing_rule = 1

		item_details.pricing_rules = frappe.as_json([d.pricing_rule for d in rules])
		
		if not doc: return item_details

	elif args.get("pricing_rules"):
			
		item_details = remove_pricing_rule_for_item(args.get("pricing_rules"),
			item_details, args.get('item_code'))
	
	return item_details

def get_pricing_rule_details(args, pricing_rule):
	return frappe._dict({
		'pricing_rule': pricing_rule.name,
		'rate_or_discount': pricing_rule.rate_or_discount,
		'margin_type': pricing_rule.margin_type,
		'item_code': args.get("item_code"),
		'child_docname': args.get('child_docname')
		

	})

@frappe.whitelist(allow_guest=True)
def apply_coupon_code(doc,applied_code =None, applied_referral_sales_partner=None,warehouse=None):
	quotation = True
	doc= json.loads(doc)
	doc=frappe._dict(doc)
	if not applied_code:
		frappe.throw(_("Please enter a coupon code"))

	coupon_list = frappe.get_all('Coupon Code', filters={'coupon_code': applied_code.upper()})
	if not coupon_list:
			frappe.throw(_("Please enter a valid coupon code"))
	coupon_name = coupon_list[0].name	
	
	coupendoc=frappe.get_doc('Coupon Code',coupon_name)
	if coupendoc.customer:
		if doc.customer!=coupendoc.customer:
			frappe.throw(_("""Coupon not valid for the customer  '{0}'...,Please enter a valid coupon code""".format(doc.customer)))
			
	pricing_rule_doc=frappe.get_doc("Pricing Rule",coupendoc.pricing_rule)
	if pricing_rule_doc.warehouse and pricing_rule_doc.warehouse!=warehouse:
		frappe.throw(_(" Coupon not valid for warehouse '{0}'".format(warehouse)))	

	item_list=frappe.db.sql("""select * from `tabPricing Rule Item Code` where parent ='{0}'""".format(pricing_rule_doc.name),as_dict =True)
	
	notfound=True
	
	for i in doc["items"]:
			for j in item_list:
				#frappe.errprint([doc,i,j.item_code])
				if i["item_code"]==j.item_code:
					notfound=False
					break
	
	if notfound==True:
			frappe.throw(_(" Coupon not valid for this transaction"))

	
	validate_coupon_code(coupon_name)	
	return quotation
def validate_coupen_item(items,applied_code):
		
	coupon_list = frappe.get_all('Coupon Code', filters={'coupon_code': applied_code.upper()})
	
	if not coupon_list:
		frappe.throw(_("Please enter a valid coupon code"))
	coupon_name = coupon_list[0].name	
	coupendoc=frappe.get_doc('Coupon Code',coupon_name)
	pricing_rule_doc=frappe.get_doc("Pricing Rule",coupendoc.pricing_rule)
	item_list=frappe.db.sql("""select * from `tabPricing Rule Item Code` where parent ='{0}'""".format(pricing_rule_doc.name),as_dict =True)
	
	
	quotation= _get_cart_quotation()
	
	if quotation:
		qdoc = frappe.get_doc("Quotation", quotation.name)
		brdoc=frappe.get_doc("Dimension Branch",{'name':qdoc.branch} )
		
		if pricing_rule_doc.warehouse and brdoc.default_warehouse!=pricing_rule_doc.warehouse:
				frappe.throw(_(" Coupon not valid for warehouse '{0}'".format(brdoc.default_warehouse)))	
				
	notfound=True
	doc= json.loads(items)
	# doc=frappe._dict(doc)
	for i in doc:
			for j in item_list:
				
				if i["name"]==j.item_code:
					notfound=False
					break
		
	if notfound==True:
			frappe.throw(_(" Coupon not valid for this transaction"))
	

def validate_coupon_code(coupon_name):
	coupon = frappe.get_doc("Coupon Code", coupon_name)
	
	if coupon.valid_from:
		if coupon.valid_from > getdate(today()):
			frappe.throw(_("Sorry, this coupon code's validity has not started"))
	if coupon.valid_upto:
		if coupon.valid_upto < getdate(today()):
			
			frappe.throw(_("Sorry, this coupon code's validity has expired"))
	if coupon.used >= coupon.maximum_use:
		frappe.throw(_("Sorry, this coupon code is no longer valid"))
def get_party(user=None):
	if not user:
		user = frappe.session.user

	contact_name = get_contact_name(user)
	party = None

	if contact_name:
		contact = frappe.get_doc('Contact', contact_name)
		if contact.links:
			party_doctype = contact.links[0].link_doctype
			party = contact.links[0].link_name

	if party:
		return frappe.get_doc(party_doctype, party)
