frappe.ui.form.on('Purchase Invoice', {
    supplier : function(frm){
            frm.doc.items = [] 
            cur_frm.add_child("items");
            cur_frm.refresh_fields();
    }
});
cur_frm.cscript.onload = function(frm) {
    cur_frm.set_query("item_code", "items", function(frm,cdt,cdn) {
                return {
                    query: "vim.custom_script.common_functions.item_query",
                    filters: {'supplier': cur_frm.doc.supplier,'is_purchase_item': 1}
    
                };
            });
}