import frappe
from erpnext.stock.doctype.repost_item_valuation.repost_item_valuation import repost_entries

@frappe.whitelist()
def run_repost_entries():
    repost_entries()