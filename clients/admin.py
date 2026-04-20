from django.contrib import admin
from .models import Client, Contract

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["organization_name", "email", "phone", "created_at"]
    search_fields = ["organization_name", "email"]

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ["contract_title", "client", "start_date", "end_date", "status", "billing_cycle"]
    list_filter = ["status", "billing_cycle"]
