from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("profile/change-password/", views.user_change_own_password, name="change_password"),
    path("users/", views.user_list, name="user_list"),
    path("users/add/", views.user_create, name="user_create"),
    path("users/<int:pk>/", views.user_detail, name="user_detail"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:pk>/set-password/", views.user_set_password, name="user_set_password"),
    path("users/<int:pk>/toggle-active/", views.user_toggle_active, name="user_toggle_active"),
    path("2fa/setup/", views.two_factor_setup, name="two_factor_setup"),
    path("2fa/disable/", views.two_factor_disable, name="two_factor_disable"),
    path("2fa/verify/", views.two_factor_verify, name="two_factor_verify"),
]
