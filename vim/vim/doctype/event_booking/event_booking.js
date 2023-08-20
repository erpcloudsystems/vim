// Copyright (c) 2021, aavu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Event Booking', {
	// refresh: function(frm) {

	// }
    send_sms:function(frm){
        return frappe.call({
            method: "vim.api.send_renew_sms",
            
            callback(res) {
                
               
            }
        });
    }
});
