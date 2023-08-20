import frappe
import pyqrcode
import io
import base64
import time
from datetime import datetime, timedelta
@frappe.whitelist()
def get_qr(data=""):
	# img = url.svg("myqr.svg", scale = 8)
	# frappe.errprint(data.encode('utf-8'))
	# data = data.encode('utf-8')
	c = pyqrcode.create(data,version=25,encoding = "utf-8")
	s = io.BytesIO()
	c.png(s,scale=6)
	# frappe.errprint(["data",base64.b64encode(s.getvalue())])
	encoded = base64.b64encode(s.getvalue()).decode("ascii")
	# frappe.errprint([encoded])
	# image_as_str = c.png_as_base64_str(scale=5)
	# frappe.errprint([image_as_str])

	# return'<img src="data:image/png;base64,{}">'.format(image_as_str)
	return '<img src="data:image/png;base64,' + encoded + '">'
@frappe.whitelist()
def get_out_time(data=""):
    datetime_object = datetime.strptime(data[1][1], '%d-%m-%Y').date()
    datetime_time = datetime.strptime(data[2][1], '%H:%M:%S').time()
    so_doc=frappe.get_doc("Sales Order",data[0][1])
    item_doc=frappe.get_doc("Item",so_doc.select_event)
    slot_list=item_doc.slot_list
    diff=''
    for slot in slot_list:
        
        if str(slot.slot_name)==str(so_doc.select_slot): 
            if slot.uom:
                is_full_day=frappe.get_value("UOM",slot.uom,'is_full_day')
            if is_full_day:
                return "Full Day"
            else:
                diff=slot.end_time-slot.start_time 
                timeArray = str(diff).split(":");
                HH = int(timeArray[0]);      
                now=datetime.combine(datetime_object, datetime_time) + timedelta(hours=HH)
                return now.strftime("%d-%m-%Y %H:%M:%S")
              