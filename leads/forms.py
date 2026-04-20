from django import forms
from .models import Lead, Activity
from accounts.models import User


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ["organization_name", "contact_person", "phone", "email", "status", "assigned_to", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = User.objects.filter(is_active=True)


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ["type", "notes", "next_follow_up_date"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "next_follow_up_date": forms.DateInput(attrs={"type": "date"}),
        }
