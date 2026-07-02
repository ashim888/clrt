from django.urls import path
from . import views

app_name = "leads"

urlpatterns = [
    path("", views.lead_list, name="lead_list"),
    path("add/", views.lead_create, name="lead_create"),
    path("<int:pk>/", views.lead_detail, name="lead_detail"),
    path("<int:pk>/edit/", views.lead_edit, name="lead_edit"),
    path("<int:pk>/delete/", views.lead_delete, name="lead_delete"),
    path("<int:lead_pk>/activity/add/", views.activity_add, name="activity_add"),
    path("activity/<int:pk>/edit/", views.activity_edit, name="activity_edit"),
    path("activity/<int:pk>/delete/", views.activity_delete, name="activity_delete"),
    path("activity/<int:pk>/update-status/", views.activity_update_status, name="activity_update_status"),
    path("<int:pk>/convert/", views.convert_to_client, name="convert_to_client"),
    path("<int:pk>/status/", views.lead_update_status, name="lead_update_status"),
    path("kanban/", views.lead_kanban, name="lead_kanban"),
    path("export/", views.lead_export_csv, name="lead_export_csv"),
    path("bulk/", views.lead_bulk_action, name="lead_bulk_action"),
    path("import/", views.lead_import, name="lead_import"),
    path("check-duplicate/", views.lead_check_duplicate, name="lead_check_duplicate"),
    path("capture/", views.lead_capture, name="lead_capture"),
    path("capture/thanks/", views.lead_capture_thanks, name="lead_capture_thanks"),
]
