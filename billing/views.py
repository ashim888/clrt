from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from .models import Invoice, Payment
from .forms import InvoiceForm, PaymentForm
from clients.models import Client  # noqa

_INV_SORT = {"date": "generated_date", "due": "due_date", "amount": "amount", "status": "status", "client": "client__organization_name"}

@login_required
def invoice_list(request):
    status = request.GET.get("status", "")
    q = request.GET.get("q", "")
    sort = request.GET.get("sort", "date")
    order = request.GET.get("order", "desc")
    invoices = Invoice.objects.select_related("client", "contract")
    if status:
        invoices = invoices.filter(status=status)
    if q:
        invoices = invoices.filter(
            Q(client__organization_name__icontains=q) | Q(invoice_number__icontains=q)
        )
    sort_field = _INV_SORT.get(sort, "generated_date")
    invoices = invoices.order_by(f"{'-' if order == 'desc' else ''}{sort_field}")
    paginator = Paginator(invoices, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "billing/invoice_list.html", {
        "invoices": page_obj,
        "page_obj": page_obj,
        "status": status,
        "q": q,
        "sort": sort,
        "order": order,
        "status_choices": Invoice.STATUS_CHOICES,
    })


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    payments = invoice.payments.all()
    paid_total = payments.aggregate(t=Sum("amount_paid"))["t"] or 0
    return render(request, "billing/invoice_detail.html", {
        "invoice": invoice,
        "payments": payments,
        "paid_total": paid_total,
        "balance": invoice.amount - paid_total,
    })


@login_required
def invoice_create(request):
    if not (request.user.is_admin() or request.user.is_accounts()):
        messages.error(request, "Access denied.")
        return redirect("billing:invoice_list")
    form = InvoiceForm(request.POST or None)
    if form.is_valid():
        invoice = form.save()
        messages.success(request, f"Invoice {invoice.invoice_number} created.")
        return redirect("billing:invoice_detail", pk=invoice.pk)
    return render(request, "billing/invoice_form.html", {"form": form, "title": "Create Invoice"})


@login_required
def invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if not (request.user.is_admin() or request.user.is_accounts()):
        messages.error(request, "Access denied.")
        return redirect("billing:invoice_detail", pk=pk)
    form = InvoiceForm(request.POST or None, instance=invoice)
    if form.is_valid():
        form.save()
        messages.success(request, "Invoice updated.")
        return redirect("billing:invoice_detail", pk=pk)
    return render(request, "billing/invoice_form.html", {"form": form, "title": "Edit Invoice", "invoice": invoice})


@login_required
def mark_overdue(request):
    from django.utils import timezone
    updated = Invoice.objects.filter(
        status="pending", due_date__lt=timezone.now().date()
    ).update(status="overdue")
    messages.success(request, f"{updated} invoice(s) marked as overdue.")
    return redirect("billing:invoice_list")


@login_required
def invoice_print(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    payments = invoice.payments.all()
    paid_total = payments.aggregate(t=Sum("amount_paid"))["t"] or 0
    return render(request, "billing/invoice_print.html", {
        "invoice": invoice,
        "payments": payments,
        "paid_total": paid_total,
        "balance": invoice.amount - paid_total,
    })


@login_required
def payment_add(request, invoice_pk):
    invoice = get_object_or_404(Invoice, pk=invoice_pk)
    if not (request.user.is_admin() or request.user.is_accounts()):
        messages.error(request, "Access denied.")
        return redirect("billing:invoice_detail", pk=invoice_pk)
    form = PaymentForm(request.POST or None)
    if form.is_valid():
        payment = form.save(commit=False)
        payment.invoice = invoice
        payment.save()
        # Check if invoice is fully paid
        paid_total = invoice.payments.aggregate(t=Sum("amount_paid"))["t"] or 0
        if paid_total >= invoice.amount:
            invoice.status = "paid"
            invoice.save()
        messages.success(request, "Payment recorded.")
        return redirect("billing:invoice_detail", pk=invoice_pk)
    return render(request, "billing/payment_form.html", {"form": form, "invoice": invoice})
