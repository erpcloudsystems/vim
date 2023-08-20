DELIMITER //
DROP PROCEDURE IF EXISTS VAT_Report;
CREATE PROCEDURE `VAT_Report`(p_company varchar(250),p_from_date date, p_to_date date,p_grouping_for_vat_report varchar(250))
BEGIN
	select 
    `VB`.`posting_date` AS `01#Posting Date:Date:100`, 'Credit' AS `02#Type::80`,
    `VB`.`sub_voucher_type` AS `03#Voucher Sub Type:Data:100`,`VB`.`voucher_type` AS `04#Voucher Type::100`,
    `VB`.`voucher_no` AS `05#Voucher No:Dynamic Link/voucher_type:150`,
    `VB`.`company` AS `06#Company`,`VB`.`account` AS `07#Account:Link/Account:100`,
    `VB`.`customer_name` AS `08#Customer Name:Data:200`,
    `VB`.`Customer_VATNo` AS `09#Customer VAT No:Data:150`,
    `VB`.`supplier_name` AS `10#Supplier Name:Data:200`,
    -- ifnull(`VB`.supplier_vat_number,`VB`.actual_supplier_vat_no) 
    -- case 
    -- when ifnull(`VB`.supplier_vat_number,'')='' then `VB`.actual_supplier_vat_no
   -- else 
    `VB`.supplier_vat_number -- end
    AS `10#Supplier VAT No:Data:150`,
    if(`VB`.`credit` = 0,0,`VB`.`Amount`) AS '11#Credit Amount:Currency:150',
    cast(`VB`.`credit` as decimal(18,2)) AS '12#Credit VAT:Currency:130',
    if(`VB`.`debit` = 0,0,`VB`.`Amount`) AS '13#Debit Amount:Currency:180',
    cast(`VB`.`debit` as decimal(18,2)) AS '14#Debit VAT:Currency:130'
 from `VATReport_GLEntry_Base` `VB` where `VB`.`credit` > 0 
 and `VB`.`posting_date` >= p_from_date and `VB`.`posting_date` <= p_to_date
 -- and ifnull(`VB`.`grouping_for_vat_report`,1) = ifnull(p_grouping_for_vat_report,ifnull(`VB`.`grouping_for_vat_report`,1))
 and ifnull(`VB`.`company`,1) = ifnull(p_company,ifnull(`VB`.`company`,1))
 
 union 
 
 select 
  `VB`.`posting_date` AS `posting_date`,'Debit' AS `Type`,
  `VB`.`sub_voucher_type` AS `sub_voucher_type`,`VB`.`voucher_type` AS `voucher_type`,
  `VB`.`voucher_no` AS `voucher_no`,`VB`.`company` AS `company`,
  `VB`.`account` AS `account`,`VB`.`customer_name` AS `07#Customer Name::200`,
  `VB`.`Customer_VATNo` AS `08#Customer VAT No::150`,
  `VB`.`supplier_name` AS `supplier_name`,
  `VB`.supplier_vat_number AS `supplier_vat_number`,
  if(`VB`.`credit` = 0,0,`VB`.`Amount`) AS `credit`,
  cast(`VB`.`credit` as decimal(18,2)) AS `VAT`,
  if(`VB`.`debit` = 0,0,`VB`.`Amount`) AS `debit`,
  cast(`VB`.`debit` as decimal(18,2)) AS `VAT` 
 from `VATReport_GLEntry_Base` `VB` where `VB`.`debit` > 0
 and `VB`.`posting_date` >= p_from_date and  `VB`.`posting_date` <= p_to_date
 -- and ifnull(`VB`.`grouping_for_vat_report`,1) = ifnull(p_grouping_for_vat_report,ifnull(`VB`.`grouping_for_vat_report`,1))
 and ifnull(`VB`.`company`,1) = ifnull(p_company,ifnull(`VB`.`company`,1));

END//


DELIMITER ;
