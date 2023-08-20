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

@frappe.whitelist()
def before_save(self,method):
	if self.is_pos:
			
			#self.allocate_advances_automatically =1
			for d in self.get("items"):
				if d.sales_order_no:
					d.sales_order=d.sales_order_no
			self.set_advances()
			self.calculate_taxes_and_totals()
			

		
def set_advances(self):
		"""Returns list of advances against Account, Party, Reference"""

		res = self.get_advance_entries()

		self.set("advances", [])
		advance_allocated = 0
		for d in res:
			if d.against_order:
				allocated_amount = flt(d.amount)
			else:
				if self.get('party_account_currency') == self.company_currency:
					amount = self.get('base_rounded_total') or self.base_grand_total
				else:
					amount = self.get('rounded_total') or self.grand_total

				allocated_amount = min(amount - advance_allocated, d.amount)
			advance_allocated += flt(allocated_amount)

			self.append("advances", {
				"doctype": self.doctype + " Advance",
				"reference_type": d.reference_type,
				"reference_name": d.reference_name,
				"reference_row": d.reference_row,
				"remarks": d.remarks,
				"advance_amount": flt(d.amount),
				"allocated_amount": allocated_amount
			})
			self.total_advance=allocated_amount
			
def get_advance_entries(self, include_unallocated=True):
		if self.doctype == "Sales Invoice":
			party_account = self.debit_to
			party_type = "Customer"
			party = self.customer
			amount_field = "credit_in_account_currency"
			order_field = "sales_order"
			order_doctype = "Sales Order"		

		order_list = list(set([d.get(order_field)
			for d in self.get("items") if d.get(order_field)]))

		

		payment_entries = get_advance_payment_entries(party_type, party, party_account,
			order_doctype, order_list, include_unallocated)

		res =  payment_entries

		return res
def get_advance_payment_entries(party_type, party, party_account, order_doctype,
		order_list=None, include_unallocated=True, against_all_orders=False, limit=None):
	party_account_field = "paid_from" if party_type == "Customer" else "paid_to"
	currency_field = "paid_from_account_currency" if party_type == "Customer" else "paid_to_account_currency"
	payment_type = "Receive" if party_type == "Customer" else "Pay"
	payment_entries_against_order, unallocated_payment_entries = [], []
	limit_cond = "limit %s" % limit if limit else ""

	if order_list or against_all_orders:
		if order_list:
			reference_condition = " and t2.reference_name in ({0})" \
				.format(', '.join(['%s'] * len(order_list)))
		else:
			reference_condition = ""
			order_list = []

		payment_entries_against_order = frappe.db.sql("""
			select
				"Payment Entry" as reference_type, t1.name as reference_name,
				t1.remarks, t2.allocated_amount as amount, t2.name as reference_row,
				t2.reference_name as against_order, t1.posting_date,
				t1.{0} as currency
			from `tabPayment Entry` t1, `tabPayment Entry Reference` t2
			where
				t1.name = t2.parent and t1.{1} = %s and t1.payment_type = %s
				and t1.party_type = %s and t1.party = %s and t1.docstatus = 1
				and t2.reference_doctype = %s {2}
			order by t1.posting_date {3}
		""".format(currency_field, party_account_field, reference_condition, limit_cond),
													  [party_account, payment_type, party_type, party,
													   order_doctype] + order_list, as_dict=1)

	if include_unallocated:
		unallocated_payment_entries = frappe.db.sql("""
				select "Payment Entry" as reference_type, name as reference_name,
				remarks, unallocated_amount as amount
				from `tabPayment Entry`
				where
					{0} = %s and party_type = %s and party = %s and payment_type = %s
					and docstatus = 1 and unallocated_amount > 0
				order by posting_date {1}
			""".format(party_account_field, limit_cond), (party_account, party_type, party, payment_type), as_dict=1)

	return list(payment_entries_against_order) + list(unallocated_payment_entries)

def calculate_outstanding_amount(self):
		
			# NOTE:
		# write_off_amount is only for POS Invoice
		# total_advance is only for non POS Invoice
		if self.doc.doctype == "Sales Invoice":
			self.calculate_paid_amount()

		if self.doc.is_return and self.doc.return_against and not self.doc.get('is_pos') or \
			self.is_internal_invoice(): return

		self.doc.round_floats_in(self.doc, ["grand_total", "total_advance", "write_off_amount"])
		self._set_in_company_currency(self.doc, ['write_off_amount'])
		total_allocated_amount = sum([flt(adv.allocated_amount, adv.precision("allocated_amount"))
				for adv in self.doc.get("advances")])
		self.doc.total_advance=total_allocated_amount
		frappe.errprint([self.doc.get("advances"),"self.total_advance"])
		if self.doc.doctype in ["Sales Invoice", "Purchase Invoice"]:
			grand_total = self.doc.rounded_total or self.doc.grand_total
			if self.doc.party_account_currency == self.doc.currency:
				total_amount_to_pay = flt(grand_total - self.doc.total_advance
					- flt(self.doc.write_off_amount), self.doc.precision("grand_total"))
			else:
				total_amount_to_pay = flt(flt(grand_total *
					self.doc.conversion_rate, self.doc.precision("grand_total")) - self.doc.total_advance
						- flt(self.doc.base_write_off_amount), self.doc.precision("grand_total"))

			self.doc.round_floats_in(self.doc, ["paid_amount"])
			change_amount = 0

			if self.doc.doctype == "Sales Invoice" and not self.doc.get('is_return'):
				self.calculate_write_off_amount()
				self.calculate_change_amount()
				change_amount = self.doc.change_amount \
					if self.doc.party_account_currency == self.doc.currency else self.doc.base_change_amount

			paid_amount = self.doc.paid_amount \
				if self.doc.party_account_currency == self.doc.currency else self.doc.base_paid_amount

			self.doc.outstanding_amount = flt(total_amount_to_pay - flt(paid_amount) + flt(change_amount),
				self.doc.precision("outstanding_amount"))

			if self.doc.doctype == 'Sales Invoice' and self.doc.get('is_pos') and self.doc.get('is_return'):
					self.update_paid_amount_for_return(total_amount_to_pay)
			frappe.errprint([self.doc.total_advance,total_amount_to_pay,paid_amount,change_amount,"posso",self.doc.outstanding_amount])