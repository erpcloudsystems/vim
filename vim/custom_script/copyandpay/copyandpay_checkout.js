    
$(document).ready(function(){
    console.log("fhdhdfh")
	(function(e){
		var options = {
			"key": "{{ api_key }}",
			"amount": cint({{ amount }} * 100), // 2000 paise = INR 20
			"name": "{{ title }}",
			"description": "{{ description }}",
			"subscription_id": "{{ subscription_id }}",
			"handler": function (response){
				copyandpay.make_payment_log(response, options, "{{ reference_doctype }}", "{{ reference_docname }}", "{{ token }}","{{ checkout }}");
			},
			"prefill": {
				"name": "{{ payer_name }}",
				"email": "{{ payer_email }}",
				"order_id": "{{ order_id }}"
			},
			"notes": {{ frappe.form_dict|json }}
		};

		var rzp = new CopyandPay(options);
		rzp.open();
		//	e.preventDefault();
	})();
})


frappe.provide('copyandpay');

copyandpay.make_payment_log = function(response, options, doctype, docname, token,checkout){
	$('.copyandpay-loading').addClass('hidden');
	$('.copyandpay-confirming').removeClass('hidden');
    
    
	frappe.call({
		method:"vim/custom_script/copyandpay/copyandpay_checkout.make_payment",
		freeze:true,
		headers: {"X-Requested-With": "XMLHttpRequest"},
		args: {
			"copyandpay_payment_id": response.copyandpay_payment_id,
			"options": options,
			"reference_doctype": doctype,
			"reference_docname": docname,
			"token": token,
            "checkoutid":checkout
		},
		callback: function(r){
			if (r.message && r.message.status == 200) {
				window.location.href = r.message.redirect_to
			}
			else if (r.message && ([401,400,500].indexOf(r.message.status) > -1)) {
				window.location.href = r.message.redirect_to
			}
		}
	})
}
