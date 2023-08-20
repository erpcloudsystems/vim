import frappe
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
@frappe.whitelist()
def get_booking_renewal_body(url):
	so_no = url.split('?')[1]
	so_doc=frappe.get_doc("Sales Order",so_no)
	si_doc=frappe.new_doc("Sales Invoice")
	si_doc=make_sales_invoice(so_no,si_doc,True)
	invoice=''
	if frappe.db.exists("Sales Invoice",{"extended_order_no":so_doc.name}):
			invoice=	frappe.db.get_value("Sales Invoice",{"extended_order_no":so_doc.name},"name")
			
	so_detils=[]
	so_detils.append({
		"so_no":so_doc.name,
		"event":so_doc.event_name,
		"city":so_doc.city,
		"branch":so_doc.branch,
		"no_of_entries":so_doc.no_of_entries,
		"select_slot":so_doc.select_slot,
		"invoice":invoice
		
	})
	if not si_doc.items or len(si_doc.items)==0:
		
		return [so_detils," Booking renewed"]
	else:
		so_detils.append({"invoice":''})
		return [so_detils]
	
@frappe.whitelist()
def create_sales_invoice(sales_order):
	sales_order=str(sales_order.strip())
	if frappe.db.exists("Sales Order",sales_order.strip()):
		so_doc=frappe.get_doc("Sales Order",sales_order)
		
		so_detils=[]
		
		message=""
		si_doc=frappe.new_doc("Sales Invoice")
		si_doc=make_sales_invoice(sales_order,si_doc,True)
		if si_doc.items:
			si_doc.extended_order_no=so_doc.name
			si_doc.save()
			si_doc.submit()
			so_detils.append({
			"so_no":so_doc.name,
			"event":so_doc.event_name,
			"city":so_doc.city,
			"branch":so_doc.branch,
			"no_of_entries":so_doc.no_of_entries,
			"select_slot":so_doc.select_slot,
			"invoice":si_doc.name
		
		})
			
			message="Your Booking renewed"
		else:
			message="Booking renewal processed"
	return [so_detils,message]
