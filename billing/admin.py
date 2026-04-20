from django.contrib import admin
from .models import Invoice, Payment

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "client", "amount", "due_date", "status"]
    list_filter = ["status"]
    search_fields = ["invoice_number", "client__organization_name"]

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["invoice", "amount_paid", "payment_date", "payment_mode"]
