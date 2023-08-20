import frappe
from frappe.utils.print_format import report_to_pdf
 
def get_context(context):
    print = frappe.get_doc('Print Format', 'new POS with QR Test')
    doc = frappe.get_doc('POS Invoice', frappe.request.url.split('?')[1])
    context.body = frappe.render_template(print.html, {"doc":doc})
    context.log = str(frappe.request.url.split('?')[1])
