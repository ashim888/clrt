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
    path("activity/<int:pk>/toggle-done/", views.activity_toggle_done, name="activity_toggle_done"),
    path("<int:pk>/convert/", views.convert_to_client, name="convert_to_client"),
    path("<int:pk>/status/", views.lead_update_status, name="lead_update_status"),
]
