from django import forms
from .models import Lead, Activity
from accounts.models import User
from dashboard.models import Tag


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ["organization_name", "contact_person", "phone", "email", "source", "deal_value", "status", "lost_reason", "assigned_to", "tags", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "lost_reason": forms.TextInput(attrs={"placeholder": "Price, competitor, timing…"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = User.objects.filter(is_active=True)


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ["type", "notes", "next_follow_up_date", "attachment"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "next_follow_up_date": forms.DateInput(attrs={"type": "date"}),
        }
