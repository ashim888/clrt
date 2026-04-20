from django.contrib import admin
from .models import Lead, Activity

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ["organization_name", "contact_person", "status", "assigned_to", "created_at"]
    list_filter = ["status", "assigned_to"]
    search_fields = ["organization_name", "contact_person", "phone"]

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ["lead", "type", "next_follow_up_date", "created_by", "created_at"]
    list_filter = ["type"]
