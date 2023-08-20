
{% include 'VIM/public/js/hijri.js' %}

frappe.ui.form.on('Customer', {
    refresh:function(frm){
        
        frm.trigger("generate_fullname")
        if(frm.doc.__islocal==1){
            frm.trigger("nationality")
            frm.trigger("city")
            frm.trigger("update_family_grid")
        }
       
    },
    load:function(frm){
       
        //  frm.trigger("update_family_grid")
       
    },
    setup: function (frm, cdt, cdn) {
		cur_frm.add_fetch('district',  'city', 'district_name');
    },
    city:function(frm){
            
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "City",
					
					fieldname: ['district_name'],
					filters: { name: cur_frm.doc.city?cur_frm.doc.city:'' },
				},
				callback: function (r, rt) {
					console.log(r.message)
                        cur_frm.set_value('district', r.message.district_name ? r.message.district_name : undefined);

                    
					
					
				}
			});
		
    },
    first_name:function(frm){
        console.log("frstname")
        frm.trigger("generate_fullname")
    },
    middle_name:function(frm){
        frm.trigger("generate_fullname")
    },
    last_name:function(frm){
        frm.trigger("generate_fullname")
    },
    mobile_no:function(frm){
        console.log("mobile_no")
        frm.trigger("update_family_grid")
        
    },
    email_id:function(frm){
        console.log("email_id")
        frm.trigger("update_family_grid")
        
    },
    preferred_communication:function(frm){
        console.log("preferred_communication")
        frm.trigger("update_family_grid")
        
    },
    validate:function(frm){
       
        var data_cust=frm.doc.customer_family_detail
        
        for (var i=0; i<data_cust.length; i++) {
            console.log(data_cust[i]["adult"],data_cust[i]["first_name"])
            if(data_cust[i]["adult"]==1 && (data_cust[i]["first_name"]==undefined ||  data_cust[i]["first_name"]=='' || data_cust[i]["last_name"]==undefined || data_cust[i]["last_name"]=='') ) {
            frappe.throw("Enter First Name & Last name in Family Details for ("+data_cust[i]["relation"]+")")
            
            validated=false;
            return false;
          }
        }
        if (frm.is_new()) {
			if(!cur_frm.doc.temporary_mobile_no || cur_frm.doc.temporary_mobile_no.length == 0){
                frappe.throw("Please Enter Mobile number(Internal Use)")
            }
            else{
   
        cur_frm.doc.mobile_no = cur_frm.doc.temporary_mobile_no ;
            }
		}
        // frappe.call({
        //     method: "frappe.client.get_value",
        //     args: {
        //         doctype: "Customer",
        //         fieldname: ['name','email_id'],
        //         filters: { email_id: frm.doc.email_id },
        //     },
        //     callback: function (r, rt) {
                
        //         console.log(r.message,"message")
        //             if(r.message["name"]!=frm.doc.name && frm.doc.email_id==r.message["email_id"])
        //             {
        //                 frappe.validated=false;
        //                 frappe.throw("Duplicate Email Id")
        //             }

                
                
                
        //     }
        // });
        // if(!cur_frm.doc.mobile_no || cur_frm.doc.mobile_no == '' ){
        //     frappe.throw("Mobile Number is mandatory")
        // }
    },
    nationality:function(frm){
        frappe.call({
            method: "frappe.client.get_value",
            args: {
                doctype: "Country",
                
                fieldname: ['code'],
                filters: { name: frm.doc.nationality },
            },
            callback: function (r, rt) {
                
                console.log(r.message)
                    cur_frm.set_value('country_code', r.message["code"]);

                
                
                
            }
        });
    },
    generate_fullname:function(frm){
        //cur_frm.set_value("customer_name",undefined)
        if(!cur_frm.doc.customer_name){
            if(cur_frm.doc.first_name && cur_frm.doc.last_name){
                if(cur_frm.doc.middle_name){
                    cur_frm.set_value("customer_name",cur_frm.doc.first_name.toUpperCase()+' '+
                    cur_frm.doc.middle_name.toUpperCase()+' '+
                    cur_frm.doc.last_name.toUpperCase())
    
                }else{
                    cur_frm.set_value("customer_name",cur_frm.doc.first_name.toUpperCase()+' '+
                    cur_frm.doc.last_name.toUpperCase())
    
                }
                if(frm.doc.__islocal==1){
                    frm.trigger("generate_family_grid")
                }
                
            }

        }
       
        
    },
    generate_personame:function(frm, child){
        
        frappe.model.set_value(child.doctype, child.name, "person_name", undefined)
        if(child.first_name && child.last_name){
            if(child.middle_name){
                frappe.model.set_value(child.doctype, child.name, "person_name",child.first_name.toUpperCase()+' '+
                child.middle_name.toUpperCase()+' '+
                child.last_name.toUpperCase())

            }else{
                frappe.model.set_value(child.doctype, child.name, "person_name",child.first_name.toUpperCase()+' '+
                child.last_name.toUpperCase())

            }
        }
        
    },
    generate_family_grid:function(frm){
        //cur_frm.set_value("customer_name",undefined)
       
            if(!frm.doc.customer_family_detail)
            {
            //     cur_frm.get_field("customer_family_detail").grid.grid_rows[0].remove();
            console.log(cur_frm.doc.first_name,cur_frm.doc.middle_name,cur_frm.doc.last_name)
            var row = cur_frm.fields_dict["customer_family_detail"].grid.add_new_row()
            frappe.model.set_value(row.doctype, row.name, "first_name", cur_frm.doc.first_name)
            frappe.model.set_value(row.doctype, row.name, "middle_name", cur_frm.doc.middle_name)
            frappe.model.set_value(row.doctype, row.name, "last_name", cur_frm.doc.last_name)
            frappe.model.set_value(row.doctype, row.name, "relation", 'self')
            frappe.model.set_value(row.doctype, row.name, "adult", 1)
            frappe.model.set_value(row.doctype, row.name, "person_name", cur_frm.doc.customer_name.toUpperCase())
            frappe.model.set_value(row.doctype, row.name, "phone_no", cur_frm.doc.mobile_no)
            frappe.model.set_value(row.doctype, row.name, "email_id", cur_frm.doc.email_id)
            frappe.model.set_value(row.doctype, row.name, "preferred_communication", cur_frm.doc.preferred_communication)
            
                                
            cur_frm.refresh_field('customer_family_detail')
            
           }
        
          
            

        
       
        
    },
    update_family_grid:function(frm){
        
        var details=frm.doc.customer_family_detail;
        if (details){
            for(var i=0;i<details.length;i++){
                if(details[i]["relation"]=='self'){
                    
                    
                    frappe.model.set_value(details[i]["doctype"],details[i]["name"],"phone_no",cur_frm.doc.mobile_no)
                    frappe.model.set_value(details[i]["doctype"],details[i]["name"],"email_id",cur_frm.doc.email_id)
                    frappe.model.set_value(details[i]["doctype"],details[i]["name"],"preferred_communication",cur_frm.doc.preferred_communication)
                }
            }
            cur_frm.refresh_field('customer_family_detail')
        }


   }
   
});
frappe.ui.form.on('Customer Family Detail', {
    dob:function(frm,cdt,cdn){
        var row = frappe.get_doc(cdt, cdn);
        var details=frm.doc.customer_family_detail;
        if (details){
            for(var i=0;i<details.length;i++){
                if(details[i]["person_name"]==row.person_name && details[i]["dob"]==row.dob && details[i]["name"]!=row.name){
                    console.log(details[i]["person_name"],row.person_name,details[i]["dob"],row.dob)
                    frappe.model.set_value(row.doctype,row.name,"dob","")

                    frappe.throw("Duplicate Family Details Found for ("+row.person_name+") with same date")
                }
            }
        }

        if(row.dob > frappe.datetime.nowdate())
        {
            frappe.model.set_value(row.doctype,row.name,"dob","")
            frappe.throw("DOB can not be greater than current date")

        }
        var gregorianDate =moment(row.dob).format("DD-MM-YYYY")
		var date = HijriJS.toHijri(gregorianDate, "-");
		console.log(gregorianDate,date,date.toFormat("dd-mm-yyyyN"),'daa')
        if (gregorianDate){
            frappe.model.set_value(row.doctype,row.name,"hijri_dob",date.toFormat("dd-mm-yyyyN"))
            
        }
    },
    favourite_colour:function(frm,cdt,cdn){
        var child = locals[cdt][cdn]
        frappe.db.get_value("Color", child.favourite_colour ,"color", (r)=> {
       
        frappe.model.set_value(cdt, cdn, "colour", r.color)
        })
    },
    first_name:function(frm,cdt,cdn){
        var child = locals[cdt][cdn]
        frm.events.generate_personame(frm, child);
    },
    middle_name:function(frm,cdt,cdn){
        var child = locals[cdt][cdn]
        frm.events.generate_personame(frm, child);
    },
    last_name:function(frm,cdt,cdn){
        var child = locals[cdt][cdn]
        frm.events.generate_personame(frm, child);
    },
    child_name:function(frm,cdt,cdn){
        var child = locals[cdt][cdn]
        frappe.model.set_value(child.doctype, child.name, "person_name",child.child_name.toUpperCase())
    },
   
    child:function(frm,cdt,cdn){
        var row = locals[cdt][cdn]
        console.log(row,'sdf')
        if(row.child)
       { if(row.adult){
            frappe.model.set_value(row.doctype, row.name , "adult", 0);
            // frm.refresh_field("adult")        
        }}

    },
    adult:function(frm,cdt,cdn){
        var row = locals[cdt][cdn]
        if(row.adult)
        {if(row.child){
            frappe.model.set_value(row.doctype, row.name , "child", 0);   
                    
        }}
    }   

});


