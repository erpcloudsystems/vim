from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
class CustomPaymentEntry(PaymentEntry):
	def validate_transaction_reference(self):
		pass