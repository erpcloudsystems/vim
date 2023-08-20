frappe.ui.form.on('Material Request', {
    refresh:function(frm){
        if(cur_frm.doc.__islocal){
            var item=cur_frm.doc.items
        for (var i=0;i<item.length;i++){
        if(cur_frm.doc.material_request_type=="Purchase" || cur_frm.doc.material_request_type=="Material Issue" ||
        cur_frm.doc.material_request_type=="Manufacture" || cur_frm.doc.material_request_type=="Customer Provided" ||
        cur_frm.doc.material_request_type=="Borrow Transfer"){
            item[i].from_warehouse=undefined
            cur_frm.doc.set_from_warehouse=undefined
        }
        // if(cur_frm.doc.material_request_type=="Purchase"){
        //     item[i].from_warehouse=undefined
        // }
    }
        }
    },
    material_request_type:function(frm){
        
        console.log("working")
        var item=cur_frm.doc.items
        for (var i=0;i<item.length;i++){
        if(cur_frm.doc.material_request_type=="Purchase" || cur_frm.doc.material_request_type=="Material Issue" ||
        cur_frm.doc.material_request_type=="Manufacture" || cur_frm.doc.material_request_type=="Customer Provided" ||
        cur_frm.doc.material_request_type=="Borrow Transfer"){
            item[i].from_warehouse=undefined
            cur_frm.doc.set_from_warehouse=undefined
        }
        // if(cur_frm.doc.material_request_type=="Purchase"){
        //     item[i].from_warehouse=undefined
        // }
    }
       
    },
    
})