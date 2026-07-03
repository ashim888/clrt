from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User
from core.mixins import TailwindFormMixin


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Username", "class": "input"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Password", "class": "input"}))


class UserCreateForm(TailwindFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "role", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_tailwind()


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "role", "is_active"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "input"}),
            "last_name": forms.TextInput(attrs={"class": "input"}),
            "email": forms.EmailInput(attrs={"class": "input"}),
            "role": forms.Select(attrs={"class": "input"}),
        }


class AdminSetPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "new-password"}),
        min_length=8,
    )
    new_password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "new-password"}),
    )

    def clean(self):
        cd = super().clean()
        p1, p2 = cd.get("new_password1"), cd.get("new_password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cd


class SelfPasswordChangeForm(forms.Form):
    current_password = forms.CharField(
        label="Current password",
        widget=forms.PasswordInput(attrs={"class": "input"}),
    )
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "new-password"}),
        min_length=8,
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "new-password"}),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        pw = self.cleaned_data.get("current_password")
        if not self.user.check_password(pw):
            raise forms.ValidationError("Current password is incorrect.")
        return pw

    def clean(self):
        cd = super().clean()
        p1, p2 = cd.get("new_password1"), cd.get("new_password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("New passwords do not match.")
        return cd
