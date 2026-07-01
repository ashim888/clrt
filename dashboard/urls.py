from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("reports/", views.reports, name="reports"),
    path("search/", views.search, name="search"),
    path("reports/team/", views.team_performance, name="team_performance"),
]
