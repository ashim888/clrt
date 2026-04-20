from django.urls import path
from . import views

app_name = "billing"

urlpatterns = [
    path("", views.invoice_list, name="invoice_list"),
    path("add/", views.invoice_create, name="invoice_create"),
    path("<int:pk>/", views.invoice_detail, name="invoice_detail"),
    path("<int:pk>/edit/", views.invoice_edit, name="invoice_edit"),
    path("mark-overdue/", views.mark_overdue, name="mark_overdue"),
    path("<int:invoice_pk>/payment/add/", views.payment_add, name="payment_add"),
]
