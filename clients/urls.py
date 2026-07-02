from django.urls import path
from . import views

app_name = "clients"

urlpatterns = [
    path("", views.client_list, name="client_list"),
    path("add/", views.client_create, name="client_create"),
    path("<int:pk>/", views.client_detail, name="client_detail"),
    path("<int:pk>/edit/", views.client_edit, name="client_edit"),
    path("export/", views.client_export_csv, name="client_export_csv"),
    path("check-duplicate/", views.client_check_duplicate, name="client_check_duplicate"),
    path("interactions/<int:pk>/mark-done/", views.client_interaction_mark_done, name="client_interaction_mark_done"),
    # Contacts
    path("<int:client_pk>/contacts/add/", views.client_contact_add, name="client_contact_add"),
    path("contacts/<int:pk>/edit/", views.client_contact_edit, name="client_contact_edit"),
    path("contacts/<int:pk>/delete/", views.client_contact_delete, name="client_contact_delete"),
    # Interactions
    path("<int:client_pk>/interactions/add/", views.client_interaction_add, name="client_interaction_add"),
    path("interactions/<int:pk>/edit/", views.client_interaction_edit, name="client_interaction_edit"),
    path("interactions/<int:pk>/delete/", views.client_interaction_delete, name="client_interaction_delete"),
    # Contracts
    path("<int:client_pk>/contracts/add/", views.contract_create, name="contract_create"),
    path("contracts/<int:pk>/", views.contract_detail, name="contract_detail"),
    path("contracts/<int:pk>/edit/", views.contract_edit, name="contract_edit"),
    # Contract Templates
    path("contract-templates/", views.contract_template_list, name="contract_template_list"),
    path("contract-templates/add/", views.contract_template_create, name="contract_template_create"),
    path("contract-templates/<int:pk>/edit/", views.contract_template_edit, name="contract_template_edit"),
    path("contract-templates/<int:pk>/delete/", views.contract_template_delete, name="contract_template_delete"),
    path("contract-templates/<int:pk>/json/", views.contract_template_json, name="contract_template_json"),
]
