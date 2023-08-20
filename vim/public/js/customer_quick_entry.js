frappe.provide('frappe.ui.form');

frappe.ui.form.CustomerQuickEntryForm = frappe.ui.form.QuickEntryForm.extend({
	init: function(doctype, after_insert) {
		this.skip_redirect_on_error = true;
        
        // this.set_df_property("mobile_no", "reqd", 1);
		this._super(doctype, after_insert);
        
		
	},

	render_dialog: function() {
		// this.mandatory = this.get_variant_fields()
        //this.mandatory.concat(this.get_variant_fields());
        this.mandatory = this.get_variant_fields();
       
        
		if(this.doc){
			if( /^-?\d+$/.test(this.doc.customer_name) && this.doc.customer_name.length === 10){
				this.doc.phone_no = this.doc.customer_name;
				this.doc.mobile_no = this.doc.customer_name;
                
			}
		}
		this._super();
       
        this.dialog.fields_dict.mobile_no.df.reqd=1
	},

	get_variant_fields: function() {
        const table_fields = [
            {
				label: __("Is Child"),
				fieldname: "child",
				fieldtype: "Check",
				in_list_view: 0,
			},
            {
				label: __("First Name"),
				fieldname: "first_name",
				fieldtype: "Data",
				in_list_view: 1,
			},
			
			{
				label: __("Last Name"),
				fieldname: "last_name",
				fieldtype: "Data",
				in_list_view: 1,
			},
			
		{
			label: __("Relation"),
			fieldname: "relation",
			fieldtype: "Link",
			options:"Family Relation",
            in_list_view: 1,
		},
		{
			label: __("DOB"),
			fieldname: "dob",
			fieldtype: "Date",
            in_list_view: 1,
		},
		{
			label: __(" Favourite Colour"),
			fieldname: "favourite_colour",
			fieldtype: "Link",
			options:"Color",
            in_list_view: 0,
		},
		{
			label: __("ChildGender"),
			fieldname: "gender",
			fieldtype: "Select",
			options:["Girl","Boy"],
            in_list_view: 0,
		},
		{
			fieldtype: "Column Break"
		},
        {
            label: __("Is Adult"),
            fieldname: "adult",
            fieldtype: "Check",
            in_list_view: 0,
        },
		{
			label: __("Middle Name"),
			fieldname: "middle_name",
			fieldtype: "Data",
			in_list_view: 1,
		},
		// {
		// 	label: __("Person Name"),
		// 	fieldname: "person_name",
		// 	fieldtype: "Data",
        //     in_list_view: 1,
		// },
		{
			label: __("Eid"),
			fieldname: "email_id",
			fieldtype: "Data",
            in_list_view: 1,
		},
		{
			label: __("Eid"),
			fieldname: "eid",
			fieldtype: "Data",
            in_list_view: 1,
		},
		{
			label: __("Phone"),
			fieldname: "phone_no",
			fieldtype: "Data",
            in_list_view: 1
		},
        {
			label: __("Preferred Communication"),
			fieldname: "preferred_communication",
			fieldtype: "Link",
            options:"Preferred Communication",
            in_list_view: 0,
		},
		{
			label: __("School Name if child"),
			fieldname: "school_name",
			fieldtype: "Data",
            in_list_view: 0,
		},
        {
			label: __("Favourite Charactor"),
			fieldname: "favourite_charactor",
			fieldtype: "Link",
			options:"Characters",
            in_list_view: 0,
		},
		{
			label: __("Mobile Number"),
			fieldname: "mobile_no",
			fieldtype: "Data",
            reqd:1
		}
		];
		// var variant_fields = [{
        //     label: __("Full Name"),
		// 	fieldname: "customer_name",
		// 	fieldtype: "Data"
            

        // },
		var variant_fields = [{
            label: __("First Name"),
			fieldname: "first_name",
			fieldtype: "Data",
            reqd:1
			
            

        },
		{
            label: __("Last Name"),
			fieldname: "last_name",
			fieldtype: "Data",
			
        },
		
		{
			fieldtype: "Column Break"
		},
		{
            label: __("Middle Name"),
			fieldname: "middle_name",
			fieldtype: "Data"
            

        },
        {
            label: __("Full Name"),
			fieldname: "customer_name",
			fieldtype: "Data",
			reqd:1
            

        },
		// {
		// 	    label: __("Full Name"),
		// 		fieldname: "customer_name",
		// 		fieldtype: "Data"
				
	
		// 	},
		// {
		// 	fieldtype: "Section Break",
		// 	label: __("Primary Contact Details"),
		// 	collapsible: 1
		// },
		
		
        
		{
			fieldtype: "Column Break"
		},
		
		
		
		{
			fieldtype: "Section Break",
			label: __("Customer Profile"),
			collapsible: 0
		},
		{
            label: __("Nationality"),
			fieldname: "nationality",
			fieldtype: "Link",
            options:"Country"            

        },
		{
            label: __("Country Code"),
			fieldname: "country_code",
			fieldtype: "Select",
            options:"+966"            

        },
		{
			label: __("Email Id"),
			fieldname: "email_id",
			fieldtype: "Data"
		},
       
		{
            label: __("used at registration time"),
			fieldname: "branch",
			fieldtype: "Link",
            options:"Dimension Branch"
            

        },
		
		{
			fieldtype: "Column Break"
		},
		{
            label: __("City"),
			fieldname: "city",
			fieldtype: "Link",
            options:"City"  ,
			
		  

        },
        {
			label: __("Mobile Number"),
			fieldname: "mobile_no",
			fieldtype: "Data",
            reqd:1
		},
		{
			label: __("Preferred Communication"),
			fieldname: "preferred_communication",
			fieldtype: "Link",
            options:"Preferred Communication",
            in_list_view: 0,
		},
        {
            label: __("Channel used at registration time"),
			fieldname: "channel_used_at_registration_time",
			fieldtype: "Select",
			options:['Walk In','Online Registration']
            

        },
        // {
		// 	fieldtype: "Section Break",
		// 	label: __("Family Profile"),
		// 	collapsible: 1
		// },
        
        // {
            
        //     fieldname: "customer_family_detail",
		// 			fieldtype: "Table",
		// 			label: "Family Details",
		// 			cannot_add_rows: false,
		// 			in_place_edit: false,
		// 			reqd: 1,
		// 			data: [],
		// 			fields: table_fields
            
        // }
		
        
		
	];

		return variant_fields;
	},
})
