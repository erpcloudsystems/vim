frappe.ui.form.on('Asset', {
    refresh:function(frm){

    },
    frequency : function(frm){
        if(frm.doc.compute_depreciation && frm.doc.frequency=="Based on Months"){
            frm.doc.calculate_depreciation = 1; 
        }
        else{
            frm.doc.calculate_depreciation = 0; 
            frm.doc.allow_monthly_depreciation = 0;
            frm.doc.finance_books = [];
        }
        frm.refresh_fields();
    },
    compute_depreciation : function(frm){
        // console.log("HERE")

        if(!frm.doc.compute_depreciation){
            // console.log("HERE")
            frm.set_value('frequency', "");
            frm.doc.maximum_usage_count = "";
            frm.doc.finance_books = [];
            frm.refresh_fields();
            
        }
    },
    calculate_depreciation : function(frm){
        // console.log("HERE")

        if(!frm.doc.calculate_depreciation){
            // console.log("HERE")
            frm.doc.finance_books = [];
            // frm.set_value('frequency', "");
            // frm.doc.maximum_usage_count = "";
            frm.refresh_fields();
            
        }
    },
    maximum_usage_count : function(frm){
        // console.log(frm.doc.maximum_usage_count)
            if(frm.doc.maximum_usage_count <= 0)
            {
                frappe.msgprint(__("Maximum Usage count should be greater than 0"));
                frm.doc.maximum_usage_count = "";
                frm.refresh_fields();
            }
    },
    // finance_books_on_form_rendered:function(frm,cdt,cdn){
	// 	var grid_row = frm.open_grid_row();
    //     // var grid_row = frm.get_field("finance_books").grid.get_row(row.name); 
    //     grid_row.toggle_display("frequency", grid_row.depreciation_method=="Manual");
    //     frm.refresh_fields();
    // //    console.log("here")
    // },
});

// frm.toggle_reqd('priority', frm.doc.status === 'Open');
