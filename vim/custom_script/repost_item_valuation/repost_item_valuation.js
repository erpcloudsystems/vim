frappe.ui.form.on('Repost Item Valuation', {
    refresh : function(frm) {
        frm.add_custom_button(__("Repost valuation Process"), function() {
            frappe.call({
                method: "nauru.custom_script.repost_item_valuation.repost_item_valuation.run_repost_entries",
                callback: function() {
                    frappe.msgprint("Done")
                }
        });
        });
    }

});