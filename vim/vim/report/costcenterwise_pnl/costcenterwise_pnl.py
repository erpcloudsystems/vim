# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.utils import flt

from erpnext.accounts.report.financial_statements import (
	get_accounts,set_gl_entries_by_account,get_appropriate_currency,filter_accounts,accumulate_values_into_parents,calculate_values,
	get_filtered_list_for_consolidated_report,filter_out_zero_value_rows,add_total_row,
	get_period_list,
)


def execute(filters=None):
	period_list = get_period_list(
		filters.from_fiscal_year,
		filters.to_fiscal_year,
		filters.period_start_date,
		filters.period_end_date,
		filters.filter_based_on,
		filters.periodicity,
		company=filters.company,
	)
	prdl=period_list

	income = get_data(
		filters.company,
		"Income",
		"Credit",
		period_list,
		filters=filters,
		accumulated_values=filters.accumulated_values,
		ignore_closing_entries=True,
		ignore_accumulated_values_for_fy=True,
	)
	
	expense = get_data(
		filters.company,
		"Expense",
		"Debit",
		period_list,
		filters=filters,
		accumulated_values=filters.accumulated_values,
		ignore_closing_entries=True,
		ignore_accumulated_values_for_fy=True,
	)
	
	net_profit_loss = get_net_profit_loss(
		income, expense, period_list, filters.company,filters, filters.presentation_currency
	)
	col=[] 
	for i in income:
		if i.get('account')=='Total Income (Credit)':
			col=i
	##
	total_income_data=frappe.db.sql("""select (sum(credit)-sum(debit)) as 'total_income',group_concat(g.account) from `tabGL Entry` g 
	inner join `tabAccount` a on g.account=a.name  where is_cancelled=0 and account_type="Income Account" """,as_dict=1)
	if total_income_data:
		total_income=total_income_data[0]['total_income']
		
		for j in period_list:
			for i in income:
				if i.get('account_type')!='Income Account' and i.get('is_group')==0:
					if i.get(j.key) !=0:
						if total_income==None:
							perce=round(0.00,2)
						else:
							perce=(i.get(j.key)/total_income)*100
					else:
						perce=round(0.00,2)
					i[j.key+'_percent']=str(abs(round(perce,2)))+'%'
			for i in expense:
				if i.get('is_group')==0:
					
					if col.get(j.key) !=0:
						if total_income==None:
							perce=round(0.00,2)
						else:
							perce=(i.get(j.key)/total_income)*100
						
					else:
						perce=round(0.00,2)
					i[j.key+'_percent']=str((round(perce,2)))+'%'
					

	##end
	data = []
	data.extend(income or [])
	data.extend(expense or [])
	if net_profit_loss:
	###str
		# for j in period_list:
		# 	total_exp_net_profit=0
		# 	total_inc_net_profit=0
		# 	for i in income:
		# 		if i.get('account_type')!='Income Account' and i.get('is_group')==0:
					
		# 			if total_income_data[0]['total_income'] !=0 or total_income_data[0]['total_income'] !=None:
		# 				if  total_income_data[0]['total_income'] !=None:
		# 					perce=(i.get(j.key)/total_income_data[0]['total_income'])*100
		# 				else:
		# 					perce=round(0.00,2)	

		# 			else:
		# 				perce=round(0.00,2)
		# 			total_inc_net_profit+=abs(round(perce,2))
		# 	for i in expense:
		# 		if i.get('is_group')==0:
		# 			if total_income_data[0]['total_income'] !=0 or total_income_data[0]['total_income'] !=None:
		# 				if  total_income_data[0]['total_income'] !=None:
		# 					perce=(i.get(j.key)/total_income_data[0]['total_income'])*100
		# 				else:
		# 					perce=round(0.00,2)	
		# 			else:
		# 				perce=round(0.00,2)
		# 			total_exp_net_profit+=(round(perce,2))
			
		# 	total_net_profit=total_inc_net_profit+	total_exp_net_profit
				
		# 	if total_net_profit !=0:
		# 		net_profit_loss[j.key+'_percent']=str((round((100-total_net_profit),2)))+'%'
		# 	else:
		# 		net_profit_loss[j.key+'_percent']=0	
		##
		data.append(net_profit_loss)
		# data.append(net_profit_loss)
	year_start_date = period_list[0]["year_start_date"].strftime("%Y-%m-%d")
	year_end_date = period_list[-1]["year_end_date"].strftime("%Y-%m-%d")
	if filters.cost_center or filters.show_cost_center:
		cond=""
		if filters.cost_center:
			cond="and cost_center in ({0}) ".format( listToString(filters.cost_center))

		sql="""select distinct cost_center,concat(cost_center,"_","per") as percent  from `tabGL Entry`  where is_cancelled=0  and cost_center!="" and cost_center is not null
				and posting_date between "{0}" and "{1}"	{2}  """.format(year_start_date,year_end_date,cond)
		additional =frappe.db.sql(sql,as_dict=1)
	else:
		additional=[]

	columns = get_columns(
		filters.periodicity, period_list,additional, filters.accumulated_values, filters.company
	)

	chart = get_chart_data(filters, columns, income, expense, net_profit_loss)

	currency = filters.presentation_currency or frappe.get_cached_value(
		"Company", filters.company, "default_currency"
	)
	report_summary = get_report_summary(
		period_list, filters.periodicity, income, expense, net_profit_loss, currency, filters
	)
	# exp=0
	# proft=0
	# for idx, e in enumerate(data):
	# 	frappe.errprint(e)
	# 	if "account_name" in e:
	# 		frappe.errprint(e.account_name)
			# account_name': 'Total Expense (Debit)'
		# 	if e.account=="Total Expense (Debit)":
		# 		exp=idx
		# 	if e.account=="Total Income (Credit)":
		# 		proft=idx
			
	# frappe.errprint([exp,proft])
	return columns, data, None, chart, report_summary

def get_columns(periodicity, period_list,additional=None, accumulated_values=1, company=None,):
	columns = [
		{
			"fieldname": "account",
			"label": _("Account"),
			"fieldtype": "Link",
			"options": "Account",
			"width": 300,
		}
	]
	if company:
		columns.append(
			{
				"fieldname": "currency",
				"label": _("Currency"),
				"fieldtype": "Link",
				"options": "Currency",
				"hidden": 1,
			}
		)
	for a in additional:
		columns.append(
			{
				"fieldname": a.cost_center,
				"label":  a.cost_center,
				"fieldtype": "Currency",
				"options": "currency",
				"width": 150,
			}
		)
		# columns.append(
		# 	{
		# 		"fieldname": a.percent,
		# 		"label":  "Percent",
		# 		"fieldtype": "Data",
		# 		"width": 150,
		# 	}
		# )

	for period in period_list:
		columns.append(
			{
				"fieldname": period.key,
				"label": period.label,
				"fieldtype": "Currency",
				"options": "currency",
				"width": 150,
			}
		)
		# columns.append(
		# 		{
		# 			"fieldname": period.key+"_percent",
		# 			"label": _("Percentage"),
		# 			"fieldtype": "Data",
				
		# 		}
		# 	)
	if periodicity != "Yearly":
		if not accumulated_values:
			columns.append(
				{"fieldname": "total", "label": _("Total"), "fieldtype": "Currency", "width": 150}
			)

	return columns
def get_data(
	company,
	root_type,
	balance_must_be,
	period_list,
	filters=None,
	accumulated_values=1,
	only_current_fiscal_year=True,
	ignore_closing_entries=False,
	ignore_accumulated_values_for_fy=False,
	total=True,
):

	accounts = get_accounts(company, root_type)
	
	if not accounts:
		return None

	accounts, accounts_by_name, parent_children_map = filter_accounts(accounts)

	company_currency = get_appropriate_currency(company, filters)

	gl_entries_by_account = {}
	for root in frappe.db.sql(
		"""select lft, rgt from tabAccount
			where root_type=%s and ifnull(parent_account, '') = ''""",
		root_type,
		as_dict=1,
	):
		
		set_gl_entries_by_account(
			company,
			period_list[0]["year_start_date"] if only_current_fiscal_year else None,
			period_list[-1]["to_date"],
			root.lft,
			root.rgt,
			filters,
			gl_entries_by_account,
			ignore_closing_entries=ignore_closing_entries,
		)

	calculate_values(
		accounts_by_name,
		gl_entries_by_account,
		period_list,
		accumulated_values,
		ignore_accumulated_values_for_fy,
	)
	accumulate_values_into_parents(accounts, accounts_by_name, period_list)
	out = prepare_data(accounts, balance_must_be, period_list, company_currency)
	out = filter_out_zero_value_rows(out, parent_children_map)

	if out and total:
		custom_add_total_row(out, root_type, balance_must_be, period_list, company_currency)

	

	return out
def prepare_data(accounts, balance_must_be, period_list, company_currency):
	data = []
	year_start_date = period_list[0]["year_start_date"].strftime("%Y-%m-%d")
	year_end_date = period_list[-1]["year_end_date"].strftime("%Y-%m-%d")

	for idx, d in enumerate(accounts):
		# add to output
		has_value = False
		total = 0
		row = frappe._dict(
			{
				"account": _(d.name),
				"parent_account": _(d.parent_account) if d.parent_account else "",
				"indent": flt(d.indent),
				"year_start_date": year_start_date,
				"year_end_date": year_end_date,
				"currency": company_currency,
				"include_in_gross": d.include_in_gross,
				"account_type": d.account_type,
				"is_group": d.is_group,
				"opening_balance": d.get("opening_balance", 0.0) * (1 if balance_must_be == "Debit" else -1),
				"account_name": (
					"%s - %s" % (_(d.account_number), _(d.account_name))
					if d.account_number
					else _(d.account_name)
				),
			}
		)
		
		company=frappe.db.get_value('Account', d.name, "company")
		min_lft, max_rgt = frappe.db.sql(
		"""select min(lft), max(rgt) from `tabAccount`
		where name=%s and company=%s  """,
		(d.name,company),
		)[0]
		sql="""select cost_center,concat(cost_center,"_","per") as percent,sum(debit)-sum(credit) amt from `tabGL Entry`  where is_cancelled=0  and account in (select name from `tabAccount` where  lft >= {3} and rgt <= {4} and company="{5}" )
		and posting_date between "{1}" and "{2}"
			group by cost_center   """.format(d.name,year_start_date,year_end_date,min_lft, max_rgt,company)
		cost =frappe.db.sql(sql,as_dict=1)
		total_income_data=frappe.db.sql("""select (sum(credit)-sum(debit)) as 'total_income',group_concat(g.account) from `tabGL Entry` g 
		inner join `tabAccount` a on g.account=a.name  where is_cancelled=0 and account_type="Income Account" """,as_dict=1)
		total_income=0	
		if total_income_data:
			total_income=total_income_data[0]['total_income']
		for n in cost:
			if d.root_type=='Income':
				row[n.cost_center] =n.amt*-1
				if d.account_type !='Income Account' and not d.is_group:
					
					if total_income==None:
						row[n.percent]=round(0.00,2)
					else:	
						row[n.percent] =str(abs(round(n.amt/total_income*100,2)))+'%'

			else:
				row[n.cost_center] =n.amt
				if d.account_type !='Income Account' and not d.is_group:
					if total_income==None:
						row[n.percent]=round(0.00,2)
					else:	
						row[n.percent] =str(abs(round(n.amt/total_income*100,2)))+'%'
		
			
		for period in period_list:
			if d.get(period.key) and balance_must_be == "Credit":
				# change sign based on Debit or Credit, since calculation is done using (debit - credit)
				d[period.key] *= -1

			row[period.key] = flt(d.get(period.key, 0.0), 3)
			
			if abs(row[period.key]) >= 0.005:
				# ignore zero values
				has_value = True
				total += flt(row[period.key])

		row["has_value"] = has_value
		row["total"] = total
		data.append(row)

	return data

def get_report_summary(
	period_list, periodicity, income, expense, net_profit_loss, currency, filters, consolidated=False
):
	net_income, net_expense, net_profit = 0.0, 0.0, 0.0

	# from consolidated financial statement
	if filters.get("accumulated_in_group_company"):
		period_list = get_filtered_list_for_consolidated_report(filters, period_list)

	for period in period_list:
		key = period if consolidated else period.key
		if income:
			net_income += income[-2].get(key)
		if expense:
			net_expense += expense[-2].get(key)
		if net_profit_loss:
			net_profit += net_profit_loss.get(key)

	if len(period_list) == 1 and periodicity == "Yearly":
		profit_label = _("Profit This Year")
		income_label = _("Total Income This Year")
		expense_label = _("Total Expense This Year")
	else:
		profit_label = _("Net Profit")
		income_label = _("Total Income")
		expense_label = _("Total Expense")

	return [
		{"value": net_income, "label": income_label, "datatype": "Currency", "currency": currency},
		{"type": "separator", "value": "-"},
		{"value": net_expense, "label": expense_label, "datatype": "Currency", "currency": currency},
		{"type": "separator", "value": "=", "color": "blue"},
		{
			"value": net_profit,
			"indicator": "Green" if net_profit > 0 else "Red",
			"label": profit_label,
			"datatype": "Currency",
			"currency": currency,
		},
	]


def get_net_profit_loss(income, expense, period_list, company,filters, currency=None, consolidated=False):
	total = 0
	net_profit_loss = {
		"account_name": "'" + _("Profit for the year") + "'",
		"account": "'" + _("Profit for the year") + "'",
		"warn_if_negative": True,
		"currency": currency or frappe.get_cached_value("Company", company, "default_currency"),
	}

	has_value = False
	for period in period_list:
		
		key = period if consolidated else period.key
		total_income = flt(income[-2][key], 3) if income else 0
		total_expense = flt(expense[-2][key], 3) if expense else 0
		
		net_profit_loss[key] = total_income - total_expense
		
		if net_profit_loss[key]:
			has_value = True
		
		total += flt(net_profit_loss[key])
		net_profit_loss["total"] = total
	
	if  not filters.cost_center:
		
		# incom = (income[-2])
		# exp = (expense[-2])
		if income!=[]:
			incom = (income[-2])
		else:
			incom={}
		if expense!=[]:
			exp = (expense[-2])
		else:
			exp={}
		
		# del incom['currency']
		# del incom['account_name']
		# del incom['account']

		# del exp['currency']
		# del exp['account_name']
		# del exp['account']
		year_start_date = period_list[0]["year_start_date"].strftime("%Y-%m-%d")
		year_end_date = period_list[-1]["year_end_date"].strftime("%Y-%m-%d")
		sql="""select distinct cost_center,concat(cost_center,"_","per") as percent  from `tabGL Entry`  where is_cancelled=0  and cost_center!="" and cost_center is not null
					and posting_date between "{0}" and "{1}" """.format(year_start_date,year_end_date)
		additional =frappe.db.sql(sql,as_dict=1)
		# if incom:
			
		# 	if net_profit_loss:
		# 		net_profit_loss = net_profit_loss 
		# 	else:
		# 		net_profit_loss= incom	
		# else:
		# 	net_profit_loss = net_profit_loss 
		net_profit_loss =net_profit_loss or incom
		
		for i in additional:
			net_profit_loss.setdefault(i.cost_center, 0.0)
			
			if net_profit_loss['account_name']=="'Profit for the year'":
				
				net_profit_loss[i.cost_center] =incom.get(i.cost_center, 0.0)	- exp.get(i.cost_center, 0.0)	
			else:	
				net_profit_loss[i.cost_center] -= exp.get(i.cost_center, 0.0)
			# frappe.errprint([net_profit_loss[i.cost_center],'net_profit_loss[i.cost_center]'])
			exp[i.cost_center] = exp.get(i.cost_center, 0.0)
			# frappe.errprint([i.cost_center,exp.get(i.cost_center, 0.0),net_profit_loss])
		
		net_profit_loss.update({"account_name": "'" + _("Profit for the year") + "'","total":total,get_year(year_end_date):total})
		

			



	# incom = incom.pop('currency')
	# exp = exp.pop('currency')
	


	



	if has_value:
		return net_profit_loss
def get_year(end_date):
	from datetime import date
	from datetime import datetime


	end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
	yer=end_date.strftime("%Y-%b-%d")
	yer=yer.split("-")
	return (yer[1].lower()+"_"+yer[0])


def get_chart_data(filters, columns, income, expense, net_profit_loss):
	labels = [d.get("label") for d in columns[2:]]

	income_data, expense_data, net_profit = [], [], []

	for p in columns[2:]:
		if income:
			income_data.append(income[-2].get(p.get("fieldname")))
		if expense:
			expense_data.append(expense[-2].get(p.get("fieldname")))
		if net_profit_loss:
			net_profit.append(net_profit_loss.get(p.get("fieldname")))

	datasets = []
	if income_data:
		datasets.append({"name": _("Income"), "values": income_data})
	if expense_data:
		datasets.append({"name": _("Expense"), "values": expense_data})
	if net_profit:
		datasets.append({"name": _("Net Profit/Loss"), "values": net_profit})

	chart = {"data": {"labels": labels, "datasets": datasets}}

	if not filters.accumulated_values:
		chart["type"] = "bar"
	else:
		chart["type"] = "line"

	chart["fieldtype"] = "Currency"

	return chart




def listToString(s):
	return  str(s)[1:-1]


def custom_add_total_row(out, root_type, balance_must_be, period_list, company_currency):
	total_row = {
		"account_name": _("Total {0} ({1})").format(_(root_type), _(balance_must_be)),
		"account": _("Total {0} ({1})").format(_(root_type), _(balance_must_be)),
		"currency": company_currency,
		"opening_balance": 0.0,
	}
	year_start_date = period_list[0]["year_start_date"].strftime("%Y-%m-%d")
	year_end_date = period_list[-1]["year_end_date"].strftime("%Y-%m-%d")
	sql="""select distinct cost_center,concat(cost_center,"_","per") as percent  from `tabGL Entry`  where is_cancelled=0  and cost_center!="" and cost_center is not null
				and posting_date between "{0}" and "{1}" """.format(year_start_date,year_end_date)
	additional =frappe.db.sql(sql,as_dict=1)

	for row in out:
		if not row.get("parent_account"):
			for period in period_list:
				total_row.setdefault(period.key, 0.0)
				total_row[period.key] += row.get(period.key, 0.0)
				row[period.key] = row.get(period.key, 0.0)
			for i in additional:
				total_row.setdefault(i.cost_center, 0.0)
				total_row[i.cost_center] += row.get(i.cost_center, 0.0)
				row[i.cost_center] = row.get(i.cost_center, 0.0)


			total_row.setdefault("total", 0.0)
			total_row["total"] += flt(row["total"])
			total_row["opening_balance"] += row["opening_balance"]
			row["total"] = ""

	if "total" in total_row:
		out.append(total_row)

		# blank row after Total
		out.append({})