from django import forms
from .models import SiteSettings


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        exclude = ['id']
        widgets = {
            'business_address': forms.Textarea(attrs={'rows': 3}),
            'default_payment_terms': forms.Textarea(attrs={'rows': 3}),
            'business_tagline': forms.TextInput(),
        }
