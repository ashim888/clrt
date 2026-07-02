from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("reports/", views.reports, name="reports"),
    path("search/", views.search, name="search"),
    path("reports/team/", views.team_performance, name="team_performance"),
    path("settings/", views.site_settings_view, name="settings"),
    path("notifications/", views.notification_list, name="notifications"),
    path("notifications/<int:pk>/read/", views.notification_read, name="notification_read"),
    path("notifications/read-all/", views.notifications_read_all, name="notifications_read_all"),
    path("tags/create/", views.tag_create, name="tag_create"),
    path("audit/", views.audit_trail, name="audit_trail"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("calendar/events/", views.calendar_events, name="calendar_events"),
]
