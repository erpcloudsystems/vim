DELIMITER //
DROP VIEW IF EXISTS `VATReport_GLEntry_Base`//
CREATE VIEW `VATReport_GLEntry_Base`AS select `TGL`.`posting_date` AS `posting_date`,`TGL`.`name` AS `name`,
`TGL`.`cost_center` AS `cost_center_GL`,`TC`.`customer_name` AS `customer_name`,`TC`.`name` AS `customer_name_master`,
case when `TSI`.`tax_id` is null then `TC`.`tax_id` else `TSI`.`tax_id` end AS `Customer_VATNo`,
`TS`.`supplier_name` AS `supplier_name`,case when `TPI`.`tax_id` is null then `TS`.`tax_id` else `TPI`.`tax_id` end 
AS `supplier_vat_number`,`TGL`.`docstatus` AS `docstatus`
,if(`TGL`.`voucher_type` = 'Sales Invoice' and `TSI`.`is_return` = 1,'Sales Invoice Return',
if(`TGL`.`voucher_type` = 'Purchase Invoice' and `TPI`.`is_return` = 1,'Purchase Invoice Return',`TGL`.`voucher_type`))
AS `sub_voucher_type`,`TGL`.`voucher_type` AS `voucher_type`,`TGL`.`voucher_no` AS `voucher_no`,`TGL`.`company` AS `company`,
`TGL`.`is_advance` AS `is_advance`,`TGL`.`account` AS `account`,`TGL`.`debit` AS `debit`,`TGL`.`credit` AS `credit`
,if(`TGL`.`voucher_type` = 'Purchase Invoice',ifnull((select sum(`PII`.`base_amount`) AS `amount`
from ( `tabPurchase Invoice Item` `PII` join  `tabItem Tax Template Detail` `ITTD` 
on(`PII`.`item_tax_template` = `ITTD`.`parent`)) where `PII`.`parent` = `TPI`.`name` and `ITTD`.`tax_type` = `TGL`.`account`)
,`TPI`.`net_total`) * if(`TPI`.`is_return` = 1,-1,1),if(`TGL`.`voucher_type` = 'Sales Invoice',
ifnull((select sum(`SII`.`base_amount`) AS `amount`
from ( `tabSales Invoice Item` `SII` 
join  `tabItem Tax Template Detail` `ITTD` on(`SII`.`item_tax_template` = `ITTD`.`parent`))
where `SII`.`parent` = `TSI`.`name` and `ITTD`.`tax_type` = `TGL`.`account`),`TSI`.`net_total`) * if(`TSI`.`is_return` = 1,-1,1)
,if(`TGL`.`voucher_type` = 'Journal Entry',`JE`.`total_debit`,0))) AS `Amount`
,case when `TGL`.`debit` = 0 then -1 * `TGL`.`credit` else `TGL`.`debit` end AS `VAT_Amount` 
from ((((((( `tabGL Entry` `TGL` 
left join  `tabSales Invoice` `TSI` on(`TGL`.`voucher_no` = `TSI`.`name` and `TSI`.docstatus=1)) 
left join  `tabPurchase Invoice` `TPI` on(`TGL`.`voucher_no` = `TPI`.`name` and `TPI`.docstatus=1)) 
left join  `tabJournal Entry` `JE` on(`TGL`.`voucher_no` = `JE`.`name` and `JE`.docstatus=1)) 
left join  `tabJournal Entry Account` `JEA`
on(`JE`.`name` = `JEA`.`parent` and `TGL`.`account` = `JEA`.`account` and `TGL`.`debit` = `JEA`.`debit` 
and `TGL`.`credit` = `JEA`.`credit`)) 
left join  `tabPayment Entry Deduction` `PED` on(`TGL`.`voucher_no` = `PED`.`parent` 
and `TGL`.`account` = `PED`.`account`)) 
left join  `tabCustomer` `TC` on(`TSI`.`customer` = `TC`.`name`)) 
left join  `tabSupplier` `TS` on(`TPI`.`supplier` = `TS`.`name`))
where `TGL`.`docstatus` = 1 and `TGL`.`is_cancelled` = 0 and (`TGL`.`account` like '%VAT%' or `TGL`.`account` 
like '%ضريبة القيمة المضافة%')//
DELIMITER ;
