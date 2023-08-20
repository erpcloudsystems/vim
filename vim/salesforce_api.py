from genericpath import exists
from nis import cat
from pickle import TRUE
import frappe, sys
from datetime import datetime


def create_customer(clist):
	res = []
	try:
		log_doc = setLog(endpoint= "vim.salesforce_api.create_customer", req_body= clist)
		for cust in clist["data"]:
			dup_doc = validate_duplicate("Customer", sfid= cust["salesForceID"])
			if dup_doc:
				res.append({
					"salesforceID": cust["salesForceID"],
					"ErpCode": dup_doc[0].name
				})
				continue

			new_cust = frappe.new_doc("Customer")
			new_cust.first_name = cust["firstName"].replace("'", "''")
			new_cust.last_name = cust["lastName"].replace("'", "''")
			new_cust.email_id = cust["email"]
			new_cust.temporary_mobile_no = cust["mobileno"]
			new_cust.mobile_no = cust["mobileno"]
			new_cust.salesforce_synced = True,
			new_cust.salesforceid = cust["salesForceID"]
			new_cust.city = cust["city"]
			new_cust.customer_group = "Jeddah"
			new_cust.territory = "Saudi Arabia"
			new_cust.insert()
			frappe.db.commit()
			
			res.append({
				"salesforceID": new_cust.salesforceid,
				"ErpCode": new_cust.name
			})

		setLog(doc_name= log_doc, status= "Success", response= res)
		return{
			"status": "success",
			"succeeded_records": res
		}
	except Exception as ex:
		setLog(doc_name= log_doc, status= "Error", response= res, error= str(ex))
		return{
			"status": "error",
			"message": ex,
			"succeeded_records": res
		}

def create_contact(clist):
	res = []
	try:
		log_doc = setLog(endpoint= "vim.salesforce_api.create_contact", req_body= clist)
		for cust in clist["data"]:
			dup_doc = validate_duplicate("Family", cust= cust["AccERPcode"], sfid= cust["SalesforceId"])
			if dup_doc:	
				res.append({
					"salesforceID": cust["SalesforceId"],
					"ErpCode": dup_doc[0]["name"]
				})
				continue

			cust_doc = frappe.get_doc("Customer", cust["AccERPcode"])
			cust_doc.append("customer_family_detail", {
				"first_name" : cust["firstName"],
				"last_name" : cust["LastName"],
				"email_id" : cust["Email"],
				"phone_no" : cust["mobileno"],
				"relation" : cust["relation"],
				"child" : cust["isChild"],
				"adult" : not cust["isChild"],
				"salesforce_synced" : True,
				"salesforceid" : cust["SalesforceId"]
			})
			cust_doc.save()
			frappe.db.commit()

			fam_acc_res = frappe.db.get_list('Customer Family Detail', 
			filters = {'parent': cust["AccERPcode"], 'salesforceid' : cust["SalesforceId"]}
			)
			res.append({
					"salesforceID": cust["SalesforceId"],
					"ErpCode": fam_acc_res[0]["name"]
				})

		setLog(doc_name= log_doc, status= "Success", response= res)
		return{
			"status": "success",
			"succeeded_records": res
		}
	except Exception as ex:
		setLog(doc_name= log_doc, status= "Error", response= res, error= str(ex))
		return{
			"status": "error",
			"message": ex,
			"succeeded_records": res
		}

def validate_duplicate(type = None, sfid = None, cust = None):
	if type == "Customer":
		return frappe.db.get_list("Customer", filters= {"salesforceid": sfid})
	elif type == "Family":
		return frappe.db.get_list('Customer Family Detail', filters = {'parent': cust, 'salesforceid' : sfid})

def setLog(endpoint = None, req_body = None, doc_name = None, status = None, response = None, error = None):
	if doc_name:
		frappe.db.set_value("Salesforce Sync Logs", doc_name,{
			"status": status,
			"response_body": str(response),
			"sync_time": frappe.utils.now(),
			"error_message": error
		}, update_modified=False)
		frappe.db.commit()
	else:
		doc = frappe.new_doc('Salesforce Sync Logs')
		doc.api_endpoint = endpoint
		doc.in_out = "Incoming"
		doc.request_body = str(req_body)
		doc.insert()
		frappe.db.commit()
		return doc.name
