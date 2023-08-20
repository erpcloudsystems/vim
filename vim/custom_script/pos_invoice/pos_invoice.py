
from __future__ import unicode_literals
import frappe,erpnext,json
from collections import OrderedDict
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt,to_timedelta, add_months, cint, nowdate, getdate, today, date_diff, month_diff, add_days, get_last_day, get_datetime,datetime
from erpnext.assets.doctype.asset.depreciation \
	import get_disposal_account_and_cost_center, get_depreciation_accounts
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_checks_for_pl_and_bs_accounts
import time
from erpnext.stock.doctype.serial_no.serial_no import get_pos_reserved_serial_nos, get_serial_nos
from erpnext.accounts.doctype.pos_invoice.pos_invoice import POSInvoice

class CustomPOSInvoice(POSInvoice):
	def validate_non_stock_items(self):
		pass
	def validate_stock_availablility(self):
		if self.is_return:
			return

		allow_negative_stock = frappe.db.get_single_value('Stock Settings', 'allow_negative_stock')
		for d in self.get('items'):
			is_stock_item = frappe.db.get_value('Item', d.item_code, ['is_stock_item'])
			if is_stock_item==1:
				if d.serial_no:
					self.validate_pos_reserved_serial_nos(d)
					self.validate_delivered_serial_nos(d)
				else:
					if allow_negative_stock:
						return

					available_stock = get_stock_availability(d.item_code, d.warehouse)
					item_code, warehouse, qty = frappe.bold(d.item_code), frappe.bold(d.warehouse), frappe.bold(d.qty)
					if flt(available_stock) <= 0:
						frappe.throw(_('Row #{}: Item Code: {} is not available under warehouse {}.')
									.format(d.idx, item_code, warehouse), title=_("Item Unavailable"))
					elif flt(available_stock) < flt(d.qty):
						frappe.throw(_('Row #{}: Stock quantity not enough for Item Code: {} under warehouse {}. Available quantity {}.')
									.format(d.idx, item_code, warehouse, available_stock), title=_("Item Unavailable"))
		
	def validate_pos_reserved_serial_nos(self, item):
		serial_nos = get_serial_nos(item.serial_no)
		filters = {"item_code": item.item_code, "warehouse": item.warehouse}
		if item.batch_no:
			filters["batch_no"] = item.batch_no

		reserved_serial_nos = get_pos_reserved_serial_nos(filters)
		invalid_serial_nos = [s for s in serial_nos if s in reserved_serial_nos]

		bold_invalid_serial_nos = frappe.bold(', '.join(invalid_serial_nos))
		if len(invalid_serial_nos) == 1:
			frappe.throw(_("Row #{}: Serial No. {} has already been transacted into another POS Invoice. Please select valid serial no.")
						.format(item.idx, bold_invalid_serial_nos), title=_("Item Unavailable"))
		elif invalid_serial_nos:
			frappe.throw(_("Row #{}: Serial Nos. {} has already been transacted into another POS Invoice. Please select valid serial no.")
						.format(item.idx, bold_invalid_serial_nos), title=_("Item Unavailable"))

	def validate_delivered_serial_nos(self, item):
		serial_nos = get_serial_nos(item.serial_no)
		delivered_serial_nos = frappe.db.get_list('Serial No', {
			'item_code': item.item_code,
			'name': ['in', serial_nos],
			'sales_invoice': ['is', 'set']
		}, pluck='name')

		if delivered_serial_nos:
			bold_delivered_serial_nos = frappe.bold(', '.join(delivered_serial_nos))
			frappe.throw(_("Row #{}: Serial No. {} has already been transacted into another Sales Invoice. Please select valid serial no.")
						.format(item.idx, bold_delivered_serial_nos), title=_("Item Unavailable"))
	
	def before_submit(self):
		
		if not self.customer or not self.customer_name:
			frappe.throw('Customer is mandatory to submit POS')	
	
@frappe.whitelist()
def get_stock_availability(item_code, warehouse):
	bin_qty = frappe.db.sql("""select actual_qty from `tabBin`
		where item_code = %s and warehouse = %s
		limit 1""", (item_code, warehouse), as_dict=1)

	pos_sales_qty = get_pos_reserved_qty(item_code, warehouse)

	bin_qty = bin_qty[0].actual_qty or 0 if bin_qty else 0

	return bin_qty - pos_sales_qty

def get_pos_reserved_qty(item_code, warehouse):
	reserved_qty = frappe.db.sql("""select sum(p_item.qty) as qty
		from `tabPOS Invoice` p, `tabPOS Invoice Item` p_item
		where p.name = p_item.parent
		and ifnull(p.consolidated_invoice, '') = ''
		and p_item.docstatus = 1
		and p_item.item_code = %s
		and p_item.warehouse = %s
		""", (item_code, warehouse), as_dict=1)

	return reserved_qty[0].qty or 0 if reserved_qty else 0
@frappe.whitelist()
def validate(self,method):
	seleceted_packed_items=self.get("seleceted_packed_items")
	if seleceted_packed_items:
		for row in seleceted_packed_items:
			if row.packed_quantity and row.combo_qty:
				row.quantity=float(row.packed_quantity) * float(row.combo_qty)
	items=self.get("items")
	if items:
			for row in items:
					if not row.income_account:
						income_account=frappe.get_value("Company",self.company,["default_income_account"])
						row.income_account=income_account

@frappe.whitelist()
def on_submit(self,method):
	for item in self.items:
		if frappe.db.exists('BOM',{"item":item.item_code}):
			bom_doc = frappe.get_doc("BOM",{"item":item.item_code})
			for itm in bom_doc.items:
				
				if frappe.db.exists("Item",{"item_code":itm.item_code}):
					itm = frappe.get_doc("Item",{"item_code":itm.item_code})
				# frappe.errprint([itm.item_code,itm.reusable_item])
				# if itm  and itm.reusable_item:
				# 	# result_list.append(item.item_code)
				# 	if frappe.db.exists('Asset',{"item_code":itm.item_code}):
				# 		asset =	 frappe.get_doc('Asset', {'item_code': itm.item_code})
				# 		# frappe.errprint([ asset.compute_depreciation, asset.frequency])
				# 		if asset.compute_depreciation and asset.frequency == "Based on Usage" :
				# 			make_depreciation_schedule(self,asset)
				# 			asset.used_count = asset.used_count + 1
				# 			asset.save()
				# 			make_depreciation_entry(asset.name)
	from erpnext.accounts.doctype.pricing_rule.utils import update_coupon_code_count
	if self.applied_coupen:
			coupon_list = frappe.get_all('Coupon Code', filters={'coupon_code': self.applied_coupen.upper()})
			if not coupon_list:
				frappe.throw(_("Please enter a valid coupon code"))
			coupon_name = coupon_list[0].name	
			update_coupon_code_count(coupon_name,'used')
	
	# if frappe.db.exists('Coupon Code',{"coupon_code":self.couponcode}):
	# 		frappe.db.sql("""update `tabCoupon Code` set `used`= used+1 where coupon_code='{0}'""".format(self.couponcode))
	# 		frappe.db.commit()
			
	# from frappe.core.doctype.sms_settings.sms_settings import send_sms
	# from frappe.utils import cstr
	# recv_list=['966582980633']
	# frappe.errprint(['Invoice "' + self.name + '" has been created! ' + frappe.utils.get_url() + '/test-page?' + self.name , 'Anup'])
	# send_sms(recv_list, cstr('Invoice "' + self.name + '"" has been created! ' + frappe.utils.get_url() + '/test-page?' + self.name))


def on_cancel(self,method):
	for item in self.items:
		if frappe.db.exists('BOM',{"item":item.item_code}):
			bom_doc = frappe.get_doc("BOM",{"item":item.item_code})
			for itm in bom_doc.items:
				itm = frappe.get_doc("Item",{"item_code":itm.item_code})
				if itm  and itm.reusable_item:
					# result_list.append(item.item_code)
					if frappe.db.exists('Asset',{"item_code":itm.item_code}):
						asset =	 frappe.get_doc('Asset', {'item_code': itm.item_code})
						asset.used_count = asset.used_count - 1
						asset.save()
						if frappe.db.exists('Invoice Schedule', {'pos_invoice': self.name}):
							invoice_schedule =	 frappe.get_doc('Invoice Schedule', {'pos_invoice': self.name})
							journal_entry = invoice_schedule.journal_entry
							invoice_schedule.cancel()
							invoice_schedule.delete()
							if journal_entry :
								je = frappe.get_doc("Journal Entry", journal_entry)
								je.cancel()
	event="select name from `tabEvent Booking` where reference_name='POS Invoice' and reference_id='{0}'".format(self.name)
	event_exist=frappe.db.sql(event,as_dict=True)
	if event_exist:
		doc=frappe.get_doc('Event Booking',event_exist[0]["name"])
		if doc:
			doc.delete()

def make_depreciation_schedule(self,asset):
		# if 'Manual' not in [d.depreciation_method for d in asset.finance_books]:
			# asset.schedules = []

		# if self.get("schedules") or not self.available_for_use_date:
		# 	return

		# for d in asset.get('finance_books'):
		# 	asset.validate_asset_finance_books(d)

		# value_after_depreciation = (flt(asset.gross_purchase_amount) -
		# 	flt(asset.opening_accumulated_depreciation))

			# d.value_after_depreciation = value_after_depreciation

		# number_of_pending_depreciations = cint(asset.maximum_usage_count) - \
		# 	cint(asset.used_count)

		# depreciation_amount = get_depreciation_amount(asset, value_after_depreciation)
		depreciation_amount = flt(asset.gross_purchase_amount)/flt(asset.maximum_usage_count)
		accumulated_depreciation_amount = depreciation_amount * (asset.used_count+1)
		schedule_date = self.posting_date

		asset.append("invoice_schedule", {
			"schedule_date": schedule_date,
			"depreciation_amount": depreciation_amount,
			"accumulated_depreciation_amount":accumulated_depreciation_amount,
			"pos_invoice": self.name,
		})

@frappe.whitelist()
def make_depreciation_entry(asset_name, date=None):
	frappe.has_permission('Journal Entry', throw=True)

	if not date:
		date = today()

	asset = frappe.get_doc("Asset", asset_name)
	fixed_asset_account, accumulated_depreciation_account, depreciation_expense_account = \
		get_depreciation_accounts(asset)

	depreciation_cost_center, depreciation_series = frappe.get_cached_value('Company',  asset.company,
		["depreciation_cost_center", "series_for_depreciation_entry"])

	depreciation_cost_center = asset.cost_center or depreciation_cost_center

	accounting_dimensions = get_checks_for_pl_and_bs_accounts()

	for d in asset.get("invoice_schedule"):
		if not d.journal_entry and getdate(d.schedule_date) <= getdate(date):
			je = frappe.new_doc("Journal Entry")
			je.voucher_type = "Depreciation Entry"
			je.naming_series = depreciation_series
			je.posting_date = d.schedule_date
			je.company = asset.company
			# je.finance_book = d.finance_book
			je.remark = "Depreciation Entry against {0} worth {1}".format(asset_name, d.depreciation_amount)

			credit_entry = {
				"account": accumulated_depreciation_account,
				"credit_in_account_currency": d.depreciation_amount,
				"reference_type": "Asset",
				"reference_name": asset.name,
				"cost_center": ""
			}

			debit_entry = {
				"account": depreciation_expense_account,
				"debit_in_account_currency": d.depreciation_amount,
				"reference_type": "Asset",
				"reference_name": asset.name,
				"cost_center": depreciation_cost_center
			}

			for dimension in accounting_dimensions:
				if (asset.get(dimension['fieldname']) or dimension.get('mandatory_for_bs')):
					credit_entry.update({
						dimension['fieldname']: asset.get(dimension['fieldname']) or dimension.get('default_dimension')
					})

				if (asset.get(dimension['fieldname']) or dimension.get('mandatory_for_pl')):
					debit_entry.update({
						dimension['fieldname']: asset.get(dimension['fieldname']) or dimension.get('default_dimension')
					})

			je.append("accounts", credit_entry)

			je.append("accounts", debit_entry)

			je.flags.ignore_permissions = True
			je.save()
			if not je.meta.get_workflow():
				je.submit()

			d.db_set("journal_entry", je.name)

			# idx = cint(d.finance_book_id)
			# finance_books = asset.get('finance_books')[idx - 1]
			# finance_books.value_after_depreciation -= d.depreciation_amount
			# finance_books.db_update()

	asset.set_status()

	# return asset


# @erpnext.allow_regional
# def get_depreciation_amount(asset, depreciable_value):
# 	depreciation_left = flt(asset.maximum_usage_count) - flt(asset.number_of_depreciations_booked)

# 	if row.depreciation_method in ("Straight Line", "Manual"):
# 		depreciation_amount = (flt(row.value_after_depreciation) -
# 			flt(row.expected_value_after_useful_life)) / depreciation_left
# 	else:
# 		depreciation_amount = flt(depreciable_value * (flt(row.rate_of_depreciation) / 100))

# 	return depreciation_amount

@frappe.whitelist()
def get_item(doc):
	doc=json.loads(doc)
	end_time=''
	for i in doc.get('items'):
		item_doc=frappe.get_doc('Item',i.get('item_code'))
		if item_doc.allowed_hrs>0 and item_doc.non_sharable_slot==1:
			alowed_seconds = int(item_doc.allowed_hrs * 60 * 60)
			min, sec = divmod(alowed_seconds, 60)
			hour, min = divmod(min, 60)
			alowed_seconds= "%d:%02d:%02d" % (hour, min, sec)
			start_time=i.get('item_start_time')
			end_time=to_timedelta(start_time)+to_timedelta(alowed_seconds)
		elif item_doc.allowed_hrs>0 and item_doc.non_sharable_slot==0:
			alowed_seconds = int(item_doc.allowed_hrs * 60 * 60)
			min, sec = divmod(alowed_seconds, 60)
			hour, min = divmod(min, 60)
			alowed_seconds= "%d:%02d:%02d" % (hour, min, sec)
			start_time=doc.get('actual_entry_time')
			end_time=to_timedelta(start_time)+to_timedelta(alowed_seconds)
			frappe.errprint(str(end_time))
	return str(end_time)
