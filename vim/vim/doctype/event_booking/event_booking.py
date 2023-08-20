# Copyright (c) 2021, aavu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
class EventBooking(Document):
	pass
@frappe.whitelist()
def get_shows(start, end):
		frappe.errprint([start,end])
		if not frappe.has_permission("Event Booking", "read"):
				raise frappe.PermissionError
		return frappe.db.sql("""select
				name,
				subject,
				timestamp(concat(`date`," ",  `from_time`)) as from_time,
				timestamp(concat(`date`," ",  `to_time`)) as to_time,
				0 as all_day,
				'Private' as event_type ,
				0 as repeat_this_event
		from `tabEvent Booking`
		where `date` between '%(start)s' and '%(end)s' """% {
				"start": start,
				"end": end
		}, as_dict=True)


@frappe.whitelist()
def get_events(doctype, start, end, field_map, filters=None, fields=None):
	# frappe.errprint([field_map])
	field_map = frappe._dict(json.loads(field_map))

	doc_meta = frappe.get_meta(doctype)
	for d in doc_meta.fields:
		if d.fieldtype == "Color":
			field_map.update({
				"color": d.fieldname
			})

	if filters:
		filters = json.loads(filters or '')

	if not fields:
		fields = [field_map.date,field_map.start, field_map.end, field_map.title, 'name']

	if field_map.color:
		fields.append(field_map.color)

	start_date = "ifnull(%s, '0001-01-01 00:00:00')" % field_map.date
	end_date = "ifnull(%s, '2199-12-31 00:00:00')" % field_map.date

	filters += [
		[doctype, start_date, '<=', end],
		[doctype, end_date, '>=', start],
	]
	events = frappe.get_list(doctype, fields=fields, filters=filters)
	import datetime
	for event in events :
		date_as_datetime = datetime.datetime.strptime(str(event['date']), '%Y-%m-%d')
		date_as_string = date_as_datetime.strftime('%Y-%m-%d')
		event['from_time']  = date_as_string +' '+str(event['from_time'] )
		event['to_time']  = date_as_string +' '+str(event['to_time'] )
		# if not event['customer_name'] or event['customer_name'] == '' :

 	# frappe.errprint(events)
	return events