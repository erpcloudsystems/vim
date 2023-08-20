from __future__ import unicode_literals
import frappe
from frappe import _
from frappe import utils

@frappe.whitelist()
def before_update_after_submit (self,method):
    
    grand_total=0;net_total=0;
    for trans in self.pos_transactions:
        doc=frappe.get_doc("POS Invoice",trans.pos_invoice)
        grand_total+=doc.grand_total
        net_total+=doc.net_total
    if grand_total!=self.grand_total or net_total!=self.net_total:
        logerror(status = "Error", resp ="Invalid Closing Total" + self.name,method="POS Closing")
        
@frappe.whitelist()
def on_submit (self,method):
    
    grand_total=0;net_total=0;
    for trans in self.pos_transactions:
        doc=frappe.get_doc("POS Invoice",trans.pos_invoice)
        grand_total+=doc.grand_total
        net_total+=doc.net_total
    if grand_total!=self.grand_total or net_total!=self.net_total:
        logerror(status = "Error", resp ="Invalid Closing Total("+self.name+"), Calculated Total: "+str(grand_total)+"Closing Total: "+str(self.grand_total) ,method="POS Closing")
def logerror(status = None, resp = None,method=None):
    new_log=frappe.new_doc("Error Log")
    new_log.method=method
    new_log.error=resp
    new_log.insert()
    new_log.save()