from django.contrib import admin
from .models import PaymentRequest, MpesaTransaction


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'phone_number', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'phone_number', 'checkout_request_id')


@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ('mpesa_transaction_id', 'payment_request', 'amount', 'result_code', 'created_at')
    search_fields = ('mpesa_transaction_id',)
