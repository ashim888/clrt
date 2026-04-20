from django import forms
from .models import Invoice, Payment
from clients.models import Client, Contract
from core.mixins import TailwindFormMixin
import uuid


class InvoiceForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["client", "contract", "invoice_number", "amount", "due_date", "description"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        client_pk = kwargs.pop("client_pk", None)
        super().__init__(*args, **kwargs)
        if client_pk:
            self.fields["contract"].queryset = Contract.objects.filter(client_id=client_pk)
        if not self.instance.pk:
            self.fields["invoice_number"].initial = f"INV-{uuid.uuid4().hex[:8].upper()}"
        self.apply_tailwind()


class PaymentForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["amount_paid", "payment_date", "payment_mode", "reference", "notes"]
        widgets = {
            "payment_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_tailwind()
