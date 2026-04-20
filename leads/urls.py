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
    path("<int:pk>/convert/", views.convert_to_client, name="convert_to_client"),
]
