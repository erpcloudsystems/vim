// Copyright (c) 2021, aavu and contributors
// For license information, please see license.txt
var weekends = []
frappe.ui.form.on('Dimension Branch', {
	refresh: function(frm) {
        if (frm.doc.weekend_days){
            weekends = frm.doc.weekend_days.split(',');
        }
	},
    sunday: function(frm) {
        if(frm.doc.sunday){
           if (!weekends.includes("Sunday"))
           {weekends.push("Sunday");
           frm.doc.weekend_days =  weekends.join(',');
             }
            }
            else
            {
                if (weekends.indexOf("Sunday")>-1)
           {
            weekends.splice(weekends.indexOf("Sunday"), 1);
                frm.doc.weekend_days =  weekends.join(',');
             }

            }
            frm.refresh_fields();
        },
        monday: function(frm) {
            if(frm.doc.monday){
                if (!weekends.includes("Monday"))
                {weekends.push("Monday");
                frm.doc.weekend_days =  weekends.join(',');
                  }
                 }
                 else
                 {
                     if (weekends.indexOf("Monday")>-1)
                {
                 weekends.splice(weekends.indexOf("Monday"), 1);
                     frm.doc.weekend_days =  weekends.join(',');
                  }
     
                 }
                 frm.refresh_fields();
        },
        tuesday: function(frm) {
            if(frm.doc.tuesday){
                if (!weekends.includes("Tuesday"))
                {weekends.push("Tuesday");
                frm.doc.weekend_days =  weekends.join(',');
                  }
                 }
                 else
                 {
                     if (weekends.indexOf("Tuesday")>-1)
                {
                 weekends.splice(weekends.indexOf("Tuesday"), 1);
                     frm.doc.weekend_days =  weekends.join(',');
                  }
     
                 }
                 frm.refresh_fields();
        },
        wednesday: function(frm) {
            if(frm.doc.wednesday){
                if (!weekends.includes("Wednesday"))
                {weekends.push("Wednesday");
                frm.doc.weekend_days =  weekends.join(',');
                  }
                 }
                 else
                 {
                     if (weekends.indexOf("Wednesday")>-1)
                {
                 weekends.splice(weekends.indexOf("Wednesday"), 1);
                     frm.doc.weekend_days =  weekends.join(',');
                  }
     
                 }
                 frm.refresh_fields();
        },
        thursday: function(frm) {
            if(frm.doc.thursday){
                if (!weekends.includes("Thursday"))
                {weekends.push("Thursday");
                frm.doc.weekend_days =  weekends.join(',');
                  }
                 }
                 else
                 {
                     if (weekends.indexOf("Thursday")>-1)
                {
                 weekends.splice(weekends.indexOf("Thursday"), 1);
                     frm.doc.weekend_days =  weekends.join(',');
                  }
     
                 }
                 frm.refresh_fields();
        },
        friday: function(frm) {
            if(frm.doc.friday){
                if (!weekends.includes("Friday"))
                {weekends.push("Friday");
                frm.doc.weekend_days =  weekends.join(',');
                  }
                 }
                 else
                 {
                     if (weekends.indexOf("Friday")>-1)
                {
                 weekends.splice(weekends.indexOf("Friday"), 1);
                     frm.doc.weekend_days =  weekends.join(',');
                  }
     
                 }
                 frm.refresh_fields();
        },
        saturday: function(frm) {
            if(frm.doc.saturday){
                if (!weekends.includes("Saturday"))
                {weekends.push("Saturday");
                frm.doc.weekend_days =  weekends.join(',');
                  }
                 }
                 else
                 {
                     if (weekends.indexOf("Saturday")>-1)
                {
                 weekends.splice(weekends.indexOf("Saturday"), 1);
                     frm.doc.weekend_days =  weekends.join(',');
                  }
     
                 }
                 frm.refresh_fields();
        }
});
