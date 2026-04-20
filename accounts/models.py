from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("sales", "Sales/Marketing"),
        ("accounts", "Accounts"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="sales")

    def is_admin(self):
        return self.role == "admin" or self.is_superuser

    def is_sales(self):
        return self.role == "sales"

    def is_accounts(self):
        return self.role == "accounts"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
