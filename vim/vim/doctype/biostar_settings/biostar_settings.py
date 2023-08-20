# Copyright (c) 2023, aavu and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe, requests, json, logging, datetime
from logging.handlers import RotatingFileHandler

class BiostarSettings(Document):
	pass

def setupLogging():
	# logging.basicConfig(level="DEBUG")
	logger = logging.getLogger("Biostar")
	logger.setLevel(logging.DEBUG)
	logger.propagate = False

	debug_handler = RotatingFileHandler("/home/frappe/frappe-bench/logs/biostar_debug.log", maxBytes= (1024 * 1000), backupCount= 5)
	debug_handler.setLevel(logging.DEBUG)
	debug_handler.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	logger.addHandler(debug_handler)

	error_handler = RotatingFileHandler("/home/frappe/frappe-bench/logs/biostar_error.log", maxBytes= (1024 * 1000), backupCount= 5)
	error_handler.setLevel(logging.WARN)
	error_handler.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	logger.addHandler(error_handler)

setupLogging()

headers = {
		'Accept': 'application/json',
		'content-type': 'application/json',
		'bs-session-id':''
	}

@frappe.whitelist(allow_guest=True)
def syn_attendance():
	logger = logging.getLogger("Biostar")
	bio_doc = frappe.get_doc("Biostar Settings")
	user = {
		'User': 
		{
			'login_id': bio_doc.user,
			'password': bio_doc.password
		}
	}
	login_res = requests.post(bio_doc.base_url + '/api/login', headers = headers, data= json.dumps(user), verify= False)
	if str(login_res.status_code).startswith("2"):
		if not login_res.headers.get("bs-session-id"):
			frappe.log_error(title="Biostar", message=str(login_res.json()))
			return login_res.json()
		headers["bs-session-id"] = login_res.headers["bs-session-id"]
		post_data = {
			"Query":{
				"limit": bio_doc.fetch_limit,
				"conditions": [
					{
						"column": "tna_key",
						"operator": 5, 
						"values": [
							0
						]
					}
				],
				"orders": [
					{
						"column": "datetime",
						"descending": False
					}
				]
			}
		}

		if bio_doc.last_synced_hint:
			post_data["Query"]["conditions"].append({
				"column": "hint",
				"operator": 5, 
				"values": [
					bio_doc.last_synced_hint
				]
			})

		event_res = requests.post(bio_doc.base_url + '/api/events/search', headers = headers, data= json.dumps(post_data), verify= False)

		att_logs = event_res.json()["EventCollection"]["rows"]
		logger.info("Attendance Logs {} records found.".format(len(att_logs)))
		# return att_logs
		for att in att_logs:
			logger.info("AttendanceLog [User: {}, Punch: {}, Hint: {}]".format(att["user_id"]["user_id"], att["datetime"], att["hint"]))
			_emp = frappe.db.get_all('Employee', filters={"attendance_device_id": att["user_id"]["user_id"]})
			# _emp = frappe.get_doc("Employee", "HR-EMP-00063")
			if not _emp:
				logger.info("Employee with user_id:{} not found.".format(att["user_id"]["user_id"]))
				update_hintid(bio_doc, att["hint"])
				continue
			try:
				doc = frappe.new_doc("Employee Checkin")
				doc.employee = _emp[0].name
				doc.device_id = att["device_id"]["id"]
				doc.time = datetime.datetime.fromisoformat(att["datetime"].split('.')[0])
				doc.insert()
				frappe.db.commit()
				logger.info("Inserted {}".format(doc.name))
			except frappe.ValidationError as verr:
				logger.info("Duplicate record.")
			
			update_hintid(bio_doc, att["hint"])

def update_hintid(bio_doc, hint_id):
	bio_doc.last_synced_hint = hint_id
	bio_doc.last_synced_datetime = frappe.utils.now()
	bio_doc.save()
	frappe.db.commit()
