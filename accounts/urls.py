from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("users/", views.user_list, name="user_list"),
    path("users/add/", views.user_create, name="user_create"),
    path("2fa/setup/", views.two_factor_setup, name="two_factor_setup"),
    path("2fa/disable/", views.two_factor_disable, name="two_factor_disable"),
    path("2fa/verify/", views.two_factor_verify, name="two_factor_verify"),
]
