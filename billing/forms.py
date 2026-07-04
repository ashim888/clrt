from django import forms
from .models import Invoice, Payment, RecurringInvoice
from clients.models import Client, Contract
from core.mixins import TailwindFormMixin
import uuid


class InvoiceForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["client", "contract", "invoice_number", "amount", "discount_percent", "tax_rate", "due_date", "description"]
        labels = {
            "amount": "Subtotal Amount",
            "discount_percent": "Discount %",
            "tax_rate": "VAT / Tax %",
        }
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 2}),
            "discount_percent": forms.NumberInput(attrs={"step": "0.01", "min": "0", "max": "100"}),
            "tax_rate": forms.NumberInput(attrs={"step": "0.01", "min": "0", "max": "100"}),
        }

    def __init__(self, *args, **kwargs):
        client_pk = kwargs.pop("client_pk", None)
        super().__init__(*args, **kwargs)
        if client_pk:
            self.fields["contract"].queryset = Contract.objects.filter(client_id=client_pk)
        if not self.instance.pk:
            self.fields["invoice_number"].initial = f"INV-{uuid.uuid4().hex[:8].upper()}"
            # Pre-fill VAT from site settings
            try:
                from dashboard.models import SiteSettings
                cfg = SiteSettings.load()
                self.fields["tax_rate"].initial = cfg.default_tax_rate
            except Exception:
                pass
        self.apply_tailwind()

    def clean_discount_percent(self):
        value = self.cleaned_data.get("discount_percent") or 0
        try:
            from dashboard.models import SiteSettings
            cfg = SiteSettings.load()
            if cfg.max_discount_percent > 0 and value > cfg.max_discount_percent:
                raise forms.ValidationError(
                    f"Discount cannot exceed {cfg.max_discount_percent}% (configured in Settings)."
                )
        except forms.ValidationError:
            raise
        except Exception:
            pass
        return value


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


class RecurringInvoiceForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = RecurringInvoice
        fields = ["client", "description", "amount", "recurrence", "day_of_month", "payment_due_days", "next_date", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
            "next_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_tailwind()
