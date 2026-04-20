from django.urls import path
from . import views

app_name = "clients"

urlpatterns = [
    path("", views.client_list, name="client_list"),
    path("add/", views.client_create, name="client_create"),
    path("<int:pk>/", views.client_detail, name="client_detail"),
    path("<int:pk>/edit/", views.client_edit, name="client_edit"),
    path("<int:client_pk>/contracts/add/", views.contract_create, name="contract_create"),
    path("contracts/<int:pk>/", views.contract_detail, name="contract_detail"),
    path("contracts/<int:pk>/edit/", views.contract_edit, name="contract_edit"),
]
