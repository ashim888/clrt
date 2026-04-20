from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import LoginForm, UserCreateForm
from .models import User


class LoginView(auth_views.LoginView):
    form_class = LoginForm
    template_name = "accounts/login.html"


class LogoutView(auth_views.LogoutView):
    pass


@login_required
def profile(request):
    return render(request, "accounts/profile.html", {"user": request.user})


@login_required
def user_list(request):
    if not request.user.is_admin():
        messages.error(request, "Access denied.")
        return redirect("/")
    users = User.objects.all().order_by("username")
    return render(request, "accounts/user_list.html", {"users": users})


@login_required
def user_create(request):
    if not request.user.is_admin():
        messages.error(request, "Access denied.")
        return redirect("/")
    form = UserCreateForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "User created successfully.")
        return redirect("accounts:user_list")
    return render(request, "accounts/user_form.html", {"form": form, "title": "Add User"})
