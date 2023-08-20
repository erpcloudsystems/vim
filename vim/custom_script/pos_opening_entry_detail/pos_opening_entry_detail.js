
frappe.ui.form.on('POS Opening Entry Detail', {
    setup:function(frm){
        frm.set_query("mode_of_payment", function() {
            return {
                "filters": {
                    "type":'Cash'
                }
            };
        });
    },
})