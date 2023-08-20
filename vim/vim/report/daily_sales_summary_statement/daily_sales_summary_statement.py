# Copyright (c) 2013, aavu and contributors
# For license information, please see license.txt

# import frappe

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns, data = [], []
	columns=get_columns()
	conditions = get_conditions(filters)
	data=get_pos_invoice_data(conditions,filters)
	return columns, data

def get_conditions(filters):
	conditions = ""
	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and parent.posting_date BETWEEN %(from_date)s and %(to_date)s"
	return conditions

def get_columns():
	return[
		_("Venue Name") + ":data:130", 
		_("Date") + ":date:130", 
		_("Total Sales (SAR)") + ":Float:130",
		_("Total Entries") + ":Float:130",
		_("Total Parties") + ":Float:130",
		_("Total School Trip") + ":Float:130"
	]

def get_pos_invoice_data(conditions,filters):
	str=frappe.db.sql("""select distinct pos.warehouse,DATE_FORMAT(parent.posting_date,'%%d-%%m-%%Y'),sum(parent.net_total) as net_total,ifnull(sum(trip.trip_count),0) as trip_count,ifnull(sum(i.non_sharable_slot),0) non_sharable_slot,
    (ifnull(sum(s_trip.s_trip_count),0) + ifnull(sum(zizo.zizo_count),0) +ifnull(sum(xtreme.xtreme_count),0) + ifnull(sum(dodi.dodi_count),0)) total,
    ifnull(sum(s_trip.s_trip_count),0) s_trip_count,ifnull(sum(zizo.zizo_count),0) zizo_count,ifnull(sum(xtreme.xtreme_count),0) xtreme_count,ifnull(sum(dodi.dodi_count),0) dodi_count
    from `tabPOS Invoice` as parent
        
    left JOIN(select item.parent,item.item_code,case when (sum(item.qty) + sum(ifnull(invp_itm.qty,0))) > 0 then 1 else 0 end non_sharable_slot from `tabPOS Invoice` inv
    inner join `tabPOS Invoice Item` as item on item.parent = inv.name
    left outer join `tabPOS Invoice` invp on invp.return_against = item.parent
    left outer join `tabPOS Invoice Item` invp_itm on invp_itm.parent = invp.name and invp_itm.item_code = item.item_code
    join `tabItem` as it on it.name=item.item_code
    where it.non_sharable_slot=1 and inv.is_return <> 1  and item.item_code not in 
    (select name from `tabItem` where non_sharable_slot=1 and (stock_uom="School Trip" or stock_uom="Zizo Trip"
    or stock_uom="Xtreme Trip" or stock_uom="Dodi Trip" )) group by item.parent) i on parent.name=i.parent

    left JOIN(select item.parent, sum(item.qty) trip_count from `tabPOS Invoice Item` as item 
    where item.uom="Ticket" group by item.parent) trip on trip.parent=parent.name 

    left JOIN(select item.parent, case when (sum(item.qty)  + sum(ifnull(invp_itm.qty,0))) > 0 then 1 else 0 end s_trip_count from `tabPOS Invoice` inv
    inner join `tabPOS Invoice Item` as item on item.parent = inv.name
    left outer join `tabPOS Invoice` invp on invp.return_against = item.parent
    left outer join `tabPOS Invoice Item` invp_itm on invp_itm.parent = invp.name and invp_itm.item_code = item.item_code
    where item.uom="School Trip"and inv.is_return <> 1  group by item.parent) s_trip on s_trip.parent=parent.name 

    left JOIN(select item.parent, case when (sum(item.qty)  + sum(ifnull(invp_itm.qty,0))) > 0 then 1 else 0 end zizo_count from `tabPOS Invoice` inv
    inner join `tabPOS Invoice Item` as item on item.parent = inv.name
    left outer join `tabPOS Invoice` invp on invp.return_against = item.parent
    left outer join `tabPOS Invoice Item` invp_itm on invp_itm.parent = invp.name and invp_itm.item_code = item.item_code
    where item.uom="Zizo Trip"and inv.is_return <> 1  group by item.parent) zizo on zizo.parent=parent.name 

    left JOIN(select item.parent, case when (sum(item.qty)  + sum(ifnull(invp_itm.qty,0))) > 0 then 1 else 0 end xtreme_count from `tabPOS Invoice` inv
    inner join `tabPOS Invoice Item` as item on item.parent = inv.name
    left outer join `tabPOS Invoice` invp on invp.return_against = item.parent
    left outer join `tabPOS Invoice Item` invp_itm on invp_itm.parent = invp.name and invp_itm.item_code = item.item_code
    where item.uom="Xtreme Trip"and inv.is_return <> 1  group by item.parent) xtreme on xtreme.parent=parent.name 

    left JOIN(select item.parent, case when (sum(item.qty)  + sum(ifnull(invp_itm.qty,0))) > 0 then 1 else 0 end dodi_count from `tabPOS Invoice` inv
    inner join `tabPOS Invoice Item` as item on item.parent = inv.name
    left outer join `tabPOS Invoice` invp on invp.return_against = item.parent
    left outer join `tabPOS Invoice Item` invp_itm on invp_itm.parent = invp.name and invp_itm.item_code = item.item_code
    where item.uom="Dodi Trip"and inv.is_return <> 1  group by item.parent) dodi on dodi.parent=parent.name 

    left join `tabPOS Profile` as pos on pos.name=parent.pos_profile
    where parent.docstatus = 1 {0} group by  parent.posting_date ,pos.warehouse""".format(conditions), filters, as_list=1)

	return str


