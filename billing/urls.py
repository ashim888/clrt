from django.urls import path
from . import views

app_name = "billing"

urlpatterns = [
    path("", views.invoice_list, name="invoice_list"),
    path("add/", views.invoice_create, name="invoice_create"),
    path("<int:pk>/", views.invoice_detail, name="invoice_detail"),
    path("<int:pk>/edit/", views.invoice_edit, name="invoice_edit"),
    path("aging/", views.invoice_aging, name="invoice_aging"),
    path("mark-overdue/", views.mark_overdue, name="mark_overdue"),
    path("recurring/", views.recurring_invoice_list, name="recurring_list"),
    path("recurring/add/", views.recurring_invoice_create, name="recurring_create"),
    path("recurring/<int:pk>/edit/", views.recurring_invoice_edit, name="recurring_edit"),
    path("recurring/<int:pk>/toggle/", views.recurring_invoice_toggle, name="recurring_toggle"),
    path("<int:invoice_pk>/payment/add/", views.payment_add, name="payment_add"),
    path("<int:pk>/print/", views.invoice_print, name="invoice_print"),
]
