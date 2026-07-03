from django.urls import path
from django.contrib.auth import views as auth_views
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
    path("users/<int:pk>/force-logout/", views.user_force_logout, name="user_force_logout"),
    path("2fa/setup/", views.two_factor_setup, name="two_factor_setup"),
    path("2fa/disable/", views.two_factor_disable, name="two_factor_disable"),
    path("2fa/verify/", views.two_factor_verify, name="two_factor_verify"),
    # ── Password reset flow ──────────────────────────────────────
    path("forgot-password/", auth_views.PasswordResetView.as_view(
        template_name="accounts/password_reset.html",
        email_template_name="accounts/password_reset_email.txt",
        subject_template_name="accounts/password_reset_subject.txt",
        success_url="/accounts/forgot-password/sent/",
    ), name="password_reset"),
    path("forgot-password/sent/", auth_views.PasswordResetDoneView.as_view(
        template_name="accounts/password_reset_done.html",
    ), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="accounts/password_reset_confirm.html",
        success_url="/accounts/reset/done/",
    ), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name="accounts/password_reset_complete.html",
    ), name="password_reset_complete"),
]
