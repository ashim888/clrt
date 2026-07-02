from django import forms
from .models import Client, Contract, ClientContact, ClientInteraction, ContractTemplate
from core.mixins import TailwindFormMixin


class ClientForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Client
        fields = ["organization_name", "phone", "email", "address", "website", "industry", "status", "tags", "notes"]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_tailwind()


class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ["contract_title", "start_date", "end_date", "billing_cycle",
                  "contract_value", "document", "status", "notes"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class ClientContactForm(forms.ModelForm):
    class Meta:
        model = ClientContact
        fields = ["name", "role", "email", "phone", "is_primary"]


class ContractTemplateForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = ContractTemplate
        fields = ["name", "billing_cycle", "default_value", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 6})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_tailwind()


class ClientInteractionForm(forms.ModelForm):
    class Meta:
        model = ClientInteraction
        fields = ["type", "notes", "next_follow_up_date", "attachment"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "next_follow_up_date": forms.DateInput(attrs={"type": "date"}),
        }
