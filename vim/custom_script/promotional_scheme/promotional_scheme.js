frappe.ui.form.on('Promotional Scheme', {
   
})
frappe.ui.form.on('Promotional Scheme Price Discount', {
    min_amount: function (frm, cdt, cdn) {
        var child = locals[cdt][cdn]
        frappe.model.set_value(cdt, cdn, 'min_amt', child.min_amount)
          
       
    },
    max_amount: function (frm, cdt, cdn) {
        var child = locals[cdt][cdn]
        frappe.model.set_value(cdt, cdn, 'max_amt', child.max_amount)
          
       
    },
})
frappe.ui.form.on('Promotional Scheme Product Discount', {
    min_amount: function (frm, cdt, cdn) {
        var child = locals[cdt][cdn]
        frappe.model.set_value(cdt, cdn, 'min_amt', child.min_amount)
          
       
    },
    max_amount: function (frm, cdt, cdn) {
        var child = locals[cdt][cdn]
        frappe.model.set_value(cdt, cdn, 'max_amt', child.max_amount)
          
       
    },
})