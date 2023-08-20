# Copyright (c) 2022, aavu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class UPDATEPOSCLOSINGENTRY(Document):
	pass


########################################UPDATE###############################
# insert into   `tabUPDATE POS CLOSING ENTRY Child`(name,parent,parentfield,parenttype,closing_entry,grand_total,net_total,change_amount)
# select rand(), 'UPCLS00001','closing_detail','UPDATE POS CLOSING ENTRY',ce.name,POS_grand_Total,POSNET_TOTAL,der.change_amount from `tabPOS Closing Entry` ce 
#  inner join (select  sum(POS.grand_total) POS_grand_Total,sum(POS.net_total) POSNET_TOTAL,c.parent,sum(POS.change_amount) change_amount from `tabPOS Invoice` POS Inner join 
# `tabPOS Invoice Reference`c on POS.name=c.pos_invoice group by c.parent ) der on der.parent=ce.name
# where ce.docstatus=1  and ce.status='Submitted'   and POS_grand_Total<>ce.grand_total ;




# create VIEW closingPayment as 
# select ip.name reco_name,ce.name closing,type,mode_of_payment,sum(ip.amount) amount from `tabPOS Closing Entry` ce inner join `tabPOS Invoice Reference` ir on ir.parent=ce.name 
# inner join `tabSales Invoice Payment`  ip
# on ip.parent=ir.pos_invoice
#  where ce.name in( select closing_entry from  `tabUPDATE POS CLOSING ENTRY Child`)group by ce.name,type,mode_of_payment;
 




#  create VIEW closingTaxes as 
# select  account_head,ce.name closing,sum(ip.tax_amount) amount from `tabPOS Closing Entry` ce inner join `tabPOS Invoice Reference` ir on ir.parent=ce.name 
# inner join `tabSales Taxes and Charges`  ip
# on ip.parent=ir.pos_invoice
#  where ce.name in( select closing_entry from  `tabUPDATE POS CLOSING ENTRY Child`)group by ce.name,account_head;

# create view closing_payment_change as                      
#  select u.change_amount,c.parent,c.name,c.mode_of_payment from `tabUPDATE POS CLOSING ENTRY Child` u inner join `tabPOS Closing Entry Detail` c
#  on c.parent=u.closing_entry and u.change_amount>0 inner join  `tabMode of Payment` M on  c.mode_of_payment = M.mode_of_payment and M.type='Cash';
                        


@frappe.whitelist()	
def update_pos_closing_entry(doc_no):
    error=''
    try:
        doc_list=frappe.db.sql(""" select * from `tabUPDATE POS CLOSING ENTRY Child` where is_updated=0 and parent='{0}'  """.format(doc_no),as_dict=True)
        for cls in doc_list:
            frappe.db.sql("""update `tabPOS Closing Entry` set net_total={0},grand_total={1},change_amount={2}  where name='{3}'""".format(cls.net_total,cls.grand_total,cls.change_amount,cls.closing_entry))
            
            frappe.db.sql("""update `tabPOS Closing Entry Detail` CLS, closingPayment CLV set     CLS.expected_amount=CLV.amount  , CLS.difference= CLV.amount-CLS.closing_amount
                        where  CLS.parent = CLV.closing and  CLS.mode_of_payment=CLV.mode_of_payment
                        and  CLS.parent ='{0}'""".format(cls.closing_entry))
            
            frappe.db.sql("""update `tabPOS Closing Entry Detail` CLS, closing_payment_change CLV set     CLS.change_amount=CLV.change_amount    
                        where  CLS.parent = CLV.parent and  CLS.mode_of_payment=CLV.mode_of_payment and CLS.name=CLV.name
                        and  CLS.parent ='{0}'  """.format(cls.closing_entry))
            frappe.db.sql(""" update `tabPOS Closing Entry Taxes` CLS, closingTaxes CLV SET     CLS.amount=CLV.amount  
                        WHERE  CLS.parent = CLV.closing and  CLS.account_head=CLV.account_head
                        AND  CLS.parent ='{0}'""".format(cls.closing_entry))
            frappe.db.sql("""update `tabUPDATE POS CLOSING ENTRY Child` set is_updated=1 where name='{0}'""".format(cls.name))
            frappe.db.commit()
    except Exception as e:						
						error=error + str(e)												
						frappe.throw(error)