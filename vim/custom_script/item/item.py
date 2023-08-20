import frappe
from erpnext.stock.doctype.item.item import Item
class CustomItem(Item):
	def add_default_uom_in_conversion_factor_table(self):
		uom_conv_list = [d.uom for d in self.get("uoms")]
		if self.stock_uom not in uom_conv_list:
			ch = self.append('uoms', {})
			ch.uom = self.stock_uom
			ch.conversion_factor = 1

@frappe.whitelist()
def validate(doc, method) :
	doc.salesforce_synced = 0