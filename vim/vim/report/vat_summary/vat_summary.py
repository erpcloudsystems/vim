# Copyright (c) 2013, avu and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json

head_vat_account = "01#VAT Account:Data:240"
head_amount = "02#Amount::200"
head_vat = "03#VAT::200"
head_total_incl_vat = "04#Total including VAT::200"
empty_dict = {head_vat_account : None, head_amount : None, head_vat : None, head_total_incl_vat : None}
# vat_payable = 0

def execute(filters=None):
	if not filters: filters = {}
	data = []
	vat_payable = 0
	query_cond = ""
	
	if filters.get('company'):
		query_cond += " and `company` = '{}' ".format(filters.get('company'))

	if filters.get('from_date') and filters.get('to_date'):
		query_cond += " and (`posting_date` between '{0}' and '{1}') ".format(filters.get('from_date'),filters.get('to_date'))

	# if filters.get('cost_center'):
	# 	query_cond += " and ifnull(`cost_center`, 1) = ifnull({}, ifnull(`cost_center`, 1)) ".format(json.dumps(filters.get('cost_center')))
	
	vat_summ_data = []

	# ============================ Sales Vat Section =========================================
	# frappe.errprint("sales data")
	sal_data = sales_vat_query(0, query_cond, filters)
	if sal_data :
		vat_summ_data = create_header(sal_data, vat_summ_data, "<b>Sales VAT</b>" )
	else:
		vat_summ_data = if_no_data("<b>Sales VAT</b>", vat_summ_data)
	# pur_vat.append(emp_dict)
	# frappe.errprint(vat_summ_data)
	# frappe.errprint(vat_payable)
	
	# frappe.errprint("sales return data")
	return_sal_data = sales_vat_query(1, query_cond, filters)
	if return_sal_data:
		vat_summ_data = create_header(return_sal_data, vat_summ_data, "<b>Sales Return VAT</b>")
	else:
		vat_summ_data = if_no_data("<b>Sales Return VAT</b>", vat_summ_data)

	# frappe.errprint(vat_summ_data)
	# frappe.errprint(vat_payable)

	

	# ============================ Sales Vat Section END =========================================

	# ============================ Purchase Vat Section =========================================
	# frappe.errprint("purchase data")
	pur_data = purchase_vat_query(0, query_cond, filters)
	if pur_data:
		vat_summ_data = create_header(pur_data, vat_summ_data, "<b>Purchase VAT</b>")
	else:
		vat_summ_data = if_no_data("<b>Purchase VAT</b>", vat_summ_data)
	
	# frappe.errprint(vat_summ_data)
	# frappe.errprint(vat_payable)

	# frappe.errprint("purchase return data")
	return_pur_data = purchase_vat_query(1, query_cond, filters)
	if return_pur_data:
		vat_summ_data = create_header(return_pur_data, vat_summ_data, "<b>Purchase Return VAT</b>")
	else:
		vat_summ_data = if_no_data("<b>Purchase Return VAT</b>", vat_summ_data)

	# frappe.errprint(vat_summ_data)
	# frappe.errprint(vat_payable)
	# ============================ Purchase Vat Section END =========================================

	# ============================ Journal Entry Section =============================================
	# frappe.errprint("journal credit data")
	jv_cr_data = jv_cre_vat_query(query_cond, filters)
	vat_summ_data = create_jv_header(jv_cr_data, vat_summ_data, "Credit")
	vat_summ_data.append(empty_dict)

	# frappe.errprint("journal debit data")
	jv_db_data = jv_deb_vat_query(query_cond, filters)
	vat_summ_data = create_jv_header(jv_db_data, vat_summ_data, "Debit")
	vat_summ_data.append(empty_dict)
	# ============================ Journal Entry Section END =========================================

	# ======================== TOTAL SECTION ==================================================
	# frappe.errprint("sales total")
	sal_total = sales_vat_query(None, query_cond, filters)
	if sal_total:
		vat_summ_data, vat_payable = create_header(sal_total, vat_summ_data, "<b>Sales VAT</b>", True)
		# frappe.errprint("data_test"+str(data))

	else:
		vat_summ_data = if_no_data("<b>Sales VAT</b>", vat_summ_data, True)
	# vat_summ_data.append(emp_dict)

	# frappe.errprint("purchase total")
	pur_total = purchase_vat_query(None, query_cond, filters)
	if pur_total:
		vat_summ_data, pur_vat_payable = create_header(pur_total, vat_summ_data, "<b>Purchase VAT</b>",True)
		vat_payable = vat_payable - pur_vat_payable
	else:
		vat_summ_data = if_no_data("<b>Purchase VAT</b>", vat_summ_data, True)

	jv_total = jv_total_query(query_cond, filters)
	if jv_total:
		vat_summ_data, vat_payable = create_jv_total(jv_total, vat_summ_data, vat_payable)
		# vat_summ_data = create_jv_header()
	else:
		vat_summ_data = if_no_data("<b>Journal VAT</b>", vat_summ_data, True)
	# ======================== TOTAL SECTION ==================================================
	# frappe.errprint("vat_pay	"+str(vat_payable))
	
	vat_summ_data.append({head_vat_account : "<b>VAT Payable</b>", head_amount : format(vat_payable,".2f"), head_vat : None, head_total_incl_vat : None})
	columns = get_columns(vat_summ_data)
	data = get_values_list(vat_summ_data)
	return columns, data

def purchase_vat_query(is_return, query_cond, filters):
	grp_by = ""
	if is_return is not None:
		grp_by = " group by `PTC`.`account_head` with rollup"
	else:
		grp_by = " group by `TPI`.`is_return` with rollup"

	cost_center_filter = ""
	if filters.get('cost_center'):
		cost_center_filter = " and ifnull(`PTC`.`cost_center`, ifnull(`TPI`.`cost_center`,1)) = ifnull({}, ifnull(`PTC`.`cost_center`, ifnull(`TPI`.`cost_center`,1))) ".format(json.dumps(filters.get('cost_center')))

	query = """select ifnull(`PTC`.`account_head`,'Total') AS `account_head`,
				Round(sum(ifnull(PII.amount,`TPI`.`net_total`)),2) as 'net_total', 
				Round(sum(ifnull(`PTC`.`base_tax_amount`, 0)),2) as 'tax_amount',
				Round(sum(ifnull(PII.amount,`TPI`.`net_total`)) + sum(ifnull(`PTC`.`base_tax_amount`, 0)),2) as 'grand_total',
				
				`TPI`.`is_return` AS `is_return`
				from `tabPurchase Taxes and Charges` `PTC`
				left join `tabPurchase Invoice` `TPI` on `TPI`.`name` = `PTC`.`parent`
				left join (select sum(`PII`.`base_amount`) AS `amount`,`PII`.parent,ITTD.tax_type
							from `tabPurchase Invoice Item` `PII`
										left join `tabItem Tax Template Detail` `ITTD` on `PII`.`item_tax_template` = `ITTD`.`parent`
							group by `PII`.`parent`,`ITTD`.`tax_type`) `PII` on `PII`.`parent` = `TPI`.`name`
							and PII.tax_type <=> PTC.account_head
				left join (select  
						name 
						from `tabSupplier`) `S` on `S`.`name` = `TPI`.`supplier`
				where `TPI`.`docstatus` = 1 and `PTC`.rate > 0
				and (`PTC`.`account_head` like '%VAT%' or `PTC`.`account_head` like '%ضريبة القيمة المضافة%')
				and case when {1} is not null then `is_return` = {1} else 1=1 end 
				{0} {3} {2} """.format(query_cond, json.dumps(is_return), grp_by, cost_center_filter)


	# query = """select Ifnull(`Purchase Exclusive VAT`, 'Total') AS `01#VAT Account`,
	# 		ROUND(IFNULL(sum(`Amount`), 0), 2) as `02#Amount`,
	# 		ROUND(IFNULL(sum(`VAT`), 0), 2) AS `03#VAT`,
	# 		ROUND(IFNULL(sum(`Total including VAT`), 0), 2) AS `04#Total including VAT`,
	# 		case when `Group VAT` is not null then
	# 		`is_return` 
	# 		else 'Total' end
	# 		as `05#is_return`, `Group VAT` as `06#Group VAT`
	# 	from `Purchase_Exclusive_VAT_New`
	# 	WHERE case when {1} is not null then `is_return` = {1} else 1=1 end {0}
	# 	{2} """.format(query_cond, json.dumps(is_return), grp_by)
	# frappe.errprint(query)
	return frappe.db.sql(query, as_dict=1)

def sales_vat_query(is_return, query_cond, filters):
	grp_by = ""
	if is_return is not None:
		grp_by = " group by  `STC`.`account_head` with rollup "
	else:
		grp_by = " group by  `TSI`.`is_return` with rollup "

	cost_center_filter = ""
	if filters.get('cost_center'):
		cost_center_filter = " and ifnull(`STC`.`cost_center`, ifnull(`TSI`.`cost_center`,1)) = ifnull({}, ifnull(`STC`.`cost_center`, ifnull(`TSI`.`cost_center`,1))) ".format(json.dumps(filters.get('cost_center')))

	query  = """select ifnull(`STC`.`account_head`,'Total') AS `account_head`,
				Round(sum(ifnull(SII.amount,`TSI`.`net_total`)),2) as 'net_total', 
				Round(sum(ifnull(`STC`.`base_tax_amount`, 0)),2) as 'tax_amount',
				Round(sum(ifnull(SII.amount,`TSI`.`net_total`)) + sum(ifnull(`STC`.`base_tax_amount`, 0)),2) as 'grand_total',
				
				`TSI`.`is_return` AS `is_return`
				from `tabSales Taxes and Charges` `STC`
				left join `tabSales Invoice` `TSI` on `TSI`.`name` = `STC`.`parent`
				left join (select sum(`SII`.`base_amount`) AS `amount`,`SII`.parent,ITTD.tax_type
							from `tabSales Invoice Item` `SII`
										left join `tabItem Tax Template Detail` `ITTD` on `SII`.`item_tax_template` = `ITTD`.`parent`
							group by `SII`.`parent`,`ITTD`.`tax_type`) `SII` on `SII`.`parent` = `TSI`.`name`
							and SII.tax_type <=> STC.account_head
				left join (select 
						name 
						from `tabCustomer`) `C` on `C`.`name` = `TSI`.`customer`
				where `TSI`.`docstatus` = 1 and `STC`.rate > 0
				and (`STC`.`account_head` like '%VAT%' or `STC`.`account_head` like '%ضريبة القيمة المضافة%')
				and case when {0} is not null then `is_return` = {0} else 1=1 end
				{1} {3} {2}""".format(json.dumps(is_return), query_cond, grp_by, cost_center_filter)
	# frappe.errprint(query)
	return frappe.db.sql(query, as_dict=1)

def jv_cre_vat_query(query_cond, filters):
	cost_center_filter = ""
	if filters.get('cost_center'):
		cost_center_filter = " and ifnull(`cost_center`, 1) = ifnull({}, ifnull(`cost_center`, 1)) ".format(json.dumps(filters.get('cost_center')))
	
	query = """SELECT
				`JEA`.`account` AS `account_head`,
				round(ifnull(sum(`JE`.`total_credit` - `JEA`.`credit`),0),2) AS `net_total`,
				round(ifnull(sum(`JEA`.`credit`),0),2) AS `tax_amount`,
				round(ifnull(sum(`JE`.`total_debit`),0),2) AS `grand_total`
			FROM (`tabJournal Entry` `JE`
				JOIN `tabJournal Entry Account` `JEA`
					ON (    `JE`.`name` = `JEA`.`parent`
						AND (   `JEA`.`account` LIKE '%VAT%'
							OR `JEA`.`account` LIKE
									'%ضريبة القيمة المضافة%')))
			WHERE `JE`.`docstatus` = 1 {0} {1} and `JEA`.`credit` != 0 group by `JEA`.account 
            union 
            SELECT
				'Total' AS `account_head`,
				round(ifnull(sum(`JE`.`total_credit` - `JEA`.`credit`),0),2) AS `net_total`,
				round(ifnull(sum(`JEA`.`credit`),0),2) AS `tax_amount`,
				round(ifnull(sum(`JE`.`total_debit`),0),2) AS `grand_total`
			FROM (`tabJournal Entry` `JE`
				JOIN `tabJournal Entry Account` `JEA`
					ON (    `JE`.`name` = `JEA`.`parent`
						AND (   `JEA`.`account` LIKE '%VAT%'
							OR `JEA`.`account` LIKE
									'%ضريبة القيمة المضافة%')))
			WHERE `JE`.`docstatus` = 1 {0} {1} and `JEA`.`credit` != 0 
            """.format(query_cond, cost_center_filter)
	frappe.errprint('1')
	frappe.errprint(query)
	return frappe.db.sql(query, as_dict=1)

def jv_deb_vat_query(query_cond, filters):
	cost_center_filter = ""
	if filters.get('cost_center'):
		cost_center_filter = " and ifnull(`cost_center`, 1) = ifnull({}, ifnull(`cost_center`, 1)) ".format(json.dumps(filters.get('cost_center')))
	query = """SELECT 
				`JEA`.`account` AS `account_head`,
				round(ifnull(sum(`JE`.`total_debit` - `JEA`.`debit`),0),2) AS `net_total`,
				round(ifnull(sum(`JEA`.`debit`),0),2) AS `tax_amount`,
				round(ifnull(sum(`JE`.`total_debit`),0),2) AS `grand_total`				
			FROM (`tabJournal Entry` `JE`
				JOIN `tabJournal Entry Account` `JEA`
					ON (    `JE`.`name` = `JEA`.`parent`
						AND (   `JEA`.`account` LIKE '%VAT%'
							OR `JEA`.`account` LIKE
									'%ضريبة القيمة المضافة%')))
			WHERE `JE`.`docstatus` = 1 {0} {1} and `JEA`.`debit` != 0 group by `JEA`.account  
            union
            SELECT 
				'Total' AS `account_head`,
				round(ifnull(sum(`JE`.`total_debit` - `JEA`.`debit`),0),2) AS `net_total`,
				round(ifnull(sum(`JEA`.`debit`),0),2) AS `tax_amount`,
				round(ifnull(sum(`JE`.`total_debit`),0),2) AS `grand_total`				
			FROM (`tabJournal Entry` `JE`
				JOIN `tabJournal Entry Account` `JEA`
					ON (    `JE`.`name` = `JEA`.`parent`
						AND (   `JEA`.`account` LIKE '%VAT%'
							OR `JEA`.`account` LIKE
									'%ضريبة القيمة المضافة%')))
			WHERE `JE`.`docstatus` = 1 {0} {1} and `JEA`.`debit` != 0
            """.format(query_cond, cost_center_filter)
	frappe.errprint('2')
	frappe.errprint(query)

	return frappe.db.sql(query, as_dict=1)

def jv_total_query(query_cond, filters):
	cost_center_filter = ""
	if filters.get('cost_center'):
		cost_center_filter = " and ifnull(`cost_center`, 1) = ifnull({}, ifnull(`cost_center`, 1)) ".format(json.dumps(filters.get('cost_center')))
	query = """  SELECT
					ROUND(IFNULL(SUM(`JE`.`total_credit` - `JEA`.`credit`), 0) , 2) AS `net_credit_amount`,
					ROUND(IFNULL(SUM(`JE`.`total_debit` - `JEA`.`debit`), 0) , 2) AS `net_debit_amount`,
					
					ROUND(IFNULL(SUM(`JEA`.`credit`), 0) , 2) AS `credit_vat`,
					ROUND(IFNULL(SUM(`JEA`.`debit`), 0) , 2) AS `debit_vat`,
					
					ROUND(IFNULL(SUM(`JE`.`total_credit`), 0) , 2) AS `credit_including_total`,
					ROUND(IFNULL(SUM(`JE`.`total_debit`), 0) , 2) AS `debit_including_total`
				FROM (`tabJournal Entry` `JE`
							JOIN `tabJournal Entry Account` `JEA`
								ON (    `JE`.`name` = `JEA`.`parent`
									AND (   `JEA`.`account` LIKE '%VAT%'
										OR `JEA`.`account` LIKE
												'%ضريبة القيمة المضافة%')))
				WHERE `JE`.`docstatus` = 1 {0} {1}""".format(query_cond, cost_center_filter)

	# frappe.errprint()
	return frappe.db.sql(query, as_dict=1)

def create_jv_total(jv_total, vat_summ_data, vat_payable):
	net_credit_amount = jv_total[0]['net_credit_amount']
	credit_vat = jv_total[0]['credit_vat']
	credit_including_total = jv_total[0]['credit_including_total']
	net_debit_amount = jv_total[0]['net_debit_amount']
	debit_vat = jv_total[0]['debit_vat']
	debit_including_total = jv_total[0]['debit_including_total']
	bal_vat = credit_vat - debit_vat 
	vat_payable = vat_payable + bal_vat

	vat_summ_data.append({ head_vat_account: "<b>Journal Credit</b>", head_amount: format(net_credit_amount,".2f"), head_vat: format(credit_vat,".2f"), head_total_incl_vat: format(credit_including_total,".2f") })

	vat_summ_data.append({ head_vat_account: "<b>Journal Debit</b>", head_amount: format(net_debit_amount,".2f"), head_vat: format(debit_vat,".2f"), head_total_incl_vat: format(debit_including_total,".2f") })

	vat_summ_data.append({ head_vat_account: "<b>Balance</b>", head_amount: format(net_credit_amount - net_debit_amount,".2f"), head_vat: format(bal_vat,".2f"), head_total_incl_vat: format(credit_including_total - debit_including_total,".2f") })
	vat_summ_data.append(empty_dict)

	return vat_summ_data, vat_payable

def create_jv_header(vat_data, pur_vat, row_header = None, total = False):
	# frappe.errprint(cr_dr)
	if row_header == "Credit":
		pur_vat.append({ head_amount: "<b>AMOUNT</b>", head_total_incl_vat: "<b>Total Including VAT</b>", head_vat: "<b>VAT</b>", head_vat_account: "<b>Journal Credit</b>" })
	else:
		pur_vat.append({ head_amount: "<b>AMOUNT</b>", head_total_incl_vat: "<b>Total Including VAT</b>", head_vat: "<b>VAT</b>", head_vat_account: "<b>Journal Debit</b>" })

	for d in vat_data:
		if total == True:
			if d.get('account_head') == 'Total':
				pur_vat.append({ head_amount: format(d.get('net_total'),".2f"), head_total_incl_vat: format(d.get('grand_total'),".2f"), head_vat: format(d.get('tax_amount'),".2f"), head_vat_account: d.get('account_head') })
		else:
			pur_vat.append({ head_amount: format(d.get('net_total'),".2f"), head_total_incl_vat: format(d.get('grand_total'),".2f"), head_vat: format(d.get('tax_amount'),".2f"), head_vat_account: d.get('account_head') })

	return pur_vat

def create_header(vat_data, vat_summ_data, row_header= None, total = False):
	# frappe.errprint("vat_ap_test	"+str(vat_payable))
	# frappe.errprint(vat_summ_data)
	# frappe.errprint(vat_data)
	group_vat_name = ""
	# frappe.errprint(total)
	val_grp_vat = ""
	group_vat = ""
	
	for d in vat_data:
		group_vat = d.get('group_vat')
		if group_vat:
			group_vat_name = group_vat

		if total == True:
			# frappe.errprint("totol header")
			# frappe.errprint(total)
			# frappe.errprint("su"+str(d.get('is_return')))
			# frappe.errprint("su"+str(d.get('group_vat')))
			if not (d.get('is_return') is None and d.get('group_vat')):
				# frappe.errprint(d.get('05#is_return'))
				# frappe.errprint(d.get('is_return'))
				# frappe.errprint(d.get('group_vat'))
				if d.get('is_return') is None and d.get('group_vat') is None:
					total_heading = "<b>Balance</b>"
					# frappe.errprint(d.get('tax_amount'))
					vat_payable = d.get('tax_amount')
				elif d.get('is_return') and int(d.get('is_return')) == 1:
					# frappe.errprint("return cond")
					total_heading = row_header + " <b> Return ("+ group_vat_name +")</b>"
				else:
					total_heading = row_header +" <b> ("+ group_vat_name +")</b>"
				
				# frappe.errprint(vat_payable)
				vat_summ_data.append({head_vat_account : total_heading, head_amount : format(d.get('net_total'),".2f"), head_vat : format(d.get('tax_amount'),".2f"), head_total_incl_vat : format(d.get('grand_total'),".2f") })
		else:
			if group_vat is not None:
				total_heading = d.get('account_head')
				if group_vat != val_grp_vat and total == False:
					vat_summ_data.append(empty_dict)
					
					vat_summ_data.append({head_vat_account : row_header + " <b>("+ group_vat +")</b>", head_amount : "<b>AMOUNT</b>", head_vat : "<b>VAT</b>", head_total_incl_vat : "<b>Total Including VAT</b>"})
				
				vat_summ_data.append({head_vat_account : total_heading, head_amount : format(d.get('net_total'),".2f"), head_vat : format(d.get('tax_amount'),".2f"), head_total_incl_vat : format(d.get('grand_total'),".2f") })

			val_grp_vat = group_vat
	vat_summ_data.append(empty_dict)
	if total == True:
		return vat_summ_data, vat_payable
	else:
		return vat_summ_data

def if_no_data(transation_name, vat_summ_data, total = False):
	if total == True:
		vat_summ_data.append({head_vat_account : "<b>"+ transation_name +"</b>", head_amount : format(0,".2f"), head_vat : format(0,".2f"), head_total_incl_vat : format(0,".2f") })
		vat_summ_data.append({head_vat_account : "<b>"+ transation_name +" Return</b>", head_amount : format(0,".2f"), head_vat : format(0,".2f"), head_total_incl_vat : format(0,".2f") })
		vat_summ_data.append({head_vat_account : "<b>Balance</b>", head_amount : format(0,".2f"), head_vat : format(0,".2f"), head_total_incl_vat : format(0,".2f") })
	else:
		vat_summ_data.append({head_vat_account : "<b>"+ transation_name +"</b>", head_amount : "<b>AMOUNT</b>", head_vat : "<b>VAT</b>", head_total_incl_vat : "<b>Total Including VAT</b>"})
		vat_summ_data.append({head_vat_account : "Total", head_amount : format(0,".2f"), head_vat : format(0,".2f"), head_total_incl_vat : format(0,".2f") })
	vat_summ_data.append(empty_dict)
	return vat_summ_data

def get_columns(data):
	column = []
	if len(data)!=0:
		for _key in sorted(data[0].keys()):
			_charidx = _key.find('#') + 1 if _key.find('#') > 0 else 0
			column.append(_key[_charidx:])
	return column

def get_values_list(data):
	rows = []
	if len(data)!=0:
		for idx in range(0,len(data)):
			val = []
			for _key in sorted(data[0].keys()):
				val.append(data[idx][_key])
			rows.append(val)
	return rows
