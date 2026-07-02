from django import forms
from .models import Service, ServiceCategory


class ServiceCategoryForm(forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ['name', 'order']


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'category', 'description', 'unit', 'default_price', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }
