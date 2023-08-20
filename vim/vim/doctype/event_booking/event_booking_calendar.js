


frappe.views.calendar["Event Booking"] = {
    
	field_map: {
		"date":"date",
		"start": "from_time",
		"end": "to_time",
		"id": "name",
		"title": "customer_name",
		"allDay": "allDay",
		"color":"color"
	},
	style_map: {
		"Public": "success",
		"Private": "info"
	},
	// gantt: true,
	// filters: [
	// 	{
	// 		"fieldtype": "Link",
	// 		"fieldname": "branch",
	// 		"options": "Branch",
	// 		"label": __("Branch")
	// 	}
	// ],
	get_events_method: "vim.vim.doctype.event_booking.event_booking.get_events"
	// get_events_method: "vim.vim.doctype.event_booking.event_booking.get_shows"
}