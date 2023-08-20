// Copyright (c) 2022, aavu and contributors
// For license information, please see license.txt

frappe.ui.form.on('CopyandPay Settings', {
	refresh: function(frm) {
        //frm.trigger("on_payment")
	},
    // on_payment: function(frm) {
    //     frappe.call({
    //         method: "vim.vim.doctype.copyandpay_payment.copyandpay_payment.request",
            
    //         callback: function (r, rt) {
               
    //             if(r && r.message){
    //                 console.log(r.message.id,"message",r.message)
    //                 var checkoutId=r.message.id;
    //                 <script src="https://eu-test.oppwa.com/v1/paymentWidgets.js?checkoutId="{...checkoutId}></script>
                    
    //             }
    //         }
    //     });
    // }
});
