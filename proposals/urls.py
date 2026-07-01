from django.urls import path
from . import views

app_name = "proposals"

urlpatterns = [
    path("", views.quote_list, name="quote_list"),
    path("add/", views.quote_create, name="quote_create"),
    path("<int:pk>/", views.quote_detail, name="quote_detail"),
    path("<int:pk>/edit/", views.quote_edit, name="quote_edit"),
    path("<int:pk>/status/", views.quote_update_status, name="quote_update_status"),
    path("<int:pk>/print/", views.quote_print, name="quote_print"),
]
