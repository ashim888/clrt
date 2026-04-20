from django import forms
from .models import Client, Contract
from core.mixins import TailwindFormMixin


class ClientForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Client
        fields = ["organization_name", "phone", "email", "address"]
        widgets = {"address": forms.Textarea(attrs={"rows": 2})}

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
