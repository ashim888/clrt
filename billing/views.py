from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Invoice, Payment, RecurringInvoice
from .forms import InvoiceForm, PaymentForm, RecurringInvoiceForm
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
    from dashboard.models import SiteSettings
    cfg = SiteSettings.load()
    return render(request, "billing/invoice_detail.html", {
        "invoice": invoice,
        "payments": payments,
        "paid_total": paid_total,
        "balance": invoice.amount - paid_total,
        "razorpay_enabled": cfg.razorpay_enabled and bool(cfg.razorpay_key_id),
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
def invoice_aging(request):
    from django.utils import timezone
    today = timezone.now().date()
    invoices = (
        Invoice.objects
        .filter(status__in=["pending", "overdue"])
        .select_related("client")
        .order_by("due_date")
    )
    buckets = [
        {"key": "current", "label": "Current", "subtitle": "not yet due", "color": "green", "items": []},
        {"key": "1_30",    "label": "1–30 days", "subtitle": "overdue",  "color": "amber", "items": []},
        {"key": "31_60",   "label": "31–60 days","subtitle": "overdue",  "color": "orange","items": []},
        {"key": "61_90",   "label": "61–90 days","subtitle": "overdue",  "color": "red",   "items": []},
        {"key": "90_plus", "label": "90+ days",  "subtitle": "overdue",  "color": "rose",  "items": []},
    ]
    for inv in invoices:
        days = (today - inv.due_date).days
        inv._days_overdue = max(days, 0)
        if days <= 0:
            buckets[0]["items"].append(inv)
        elif days <= 30:
            buckets[1]["items"].append(inv)
        elif days <= 60:
            buckets[2]["items"].append(inv)
        elif days <= 90:
            buckets[3]["items"].append(inv)
        else:
            buckets[4]["items"].append(inv)
    for b in buckets:
        b["total"] = sum(float(i.amount) for i in b["items"])
        b["count"] = len(b["items"])
    grand_total = sum(b["total"] for b in buckets)
    return render(request, "billing/invoice_aging.html", {
        "buckets": buckets,
        "grand_total": grand_total,
        "today": today,
    })


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
def recurring_invoice_list(request):
    schedules = RecurringInvoice.objects.select_related("client").order_by("is_active", "next_date")
    return render(request, "billing/recurring_list.html", {"schedules": schedules})


@login_required
def recurring_invoice_create(request):
    if not (request.user.is_admin() or request.user.is_accounts()):
        messages.error(request, "Access denied.")
        return redirect("billing:recurring_list")
    form = RecurringInvoiceForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Recurring invoice schedule created.")
        return redirect("billing:recurring_list")
    return render(request, "billing/recurring_form.html", {"form": form, "title": "New Recurring Schedule"})


@login_required
def recurring_invoice_edit(request, pk):
    schedule = get_object_or_404(RecurringInvoice, pk=pk)
    if not (request.user.is_admin() or request.user.is_accounts()):
        messages.error(request, "Access denied.")
        return redirect("billing:recurring_list")
    form = RecurringInvoiceForm(request.POST or None, instance=schedule)
    if form.is_valid():
        form.save()
        messages.success(request, "Schedule updated.")
        return redirect("billing:recurring_list")
    return render(request, "billing/recurring_form.html", {"form": form, "title": "Edit Schedule", "schedule": schedule})


@login_required
@require_POST
def recurring_invoice_toggle(request, pk):
    schedule = get_object_or_404(RecurringInvoice, pk=pk)
    if not (request.user.is_admin() or request.user.is_accounts()):
        messages.error(request, "Access denied.")
        return redirect("billing:recurring_list")
    schedule.is_active = not schedule.is_active
    schedule.save(update_fields=["is_active"])
    messages.success(request, f"Schedule {'activated' if schedule.is_active else 'paused'}.")
    return redirect("billing:recurring_list")


@login_required
@require_POST
def razorpay_create_order(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    from dashboard.models import SiteSettings
    cfg = SiteSettings.load()
    if not cfg.razorpay_enabled or not cfg.razorpay_key_id or not cfg.razorpay_key_secret:
        return JsonResponse({"error": "Payment gateway not configured."}, status=400)
    import razorpay
    client = razorpay.Client(auth=(cfg.razorpay_key_id, cfg.razorpay_key_secret))
    amount_paise = int(float(invoice.amount) * 100)
    order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "receipt": invoice.invoice_number,
        "notes": {"invoice_id": str(invoice.pk)},
    })
    return JsonResponse({
        "order_id": order["id"],
        "amount": amount_paise,
        "currency": "INR",
        "key_id": cfg.razorpay_key_id,
        "invoice_number": invoice.invoice_number,
        "invoice_pk": invoice.pk,
        "client_name": invoice.client.organization_name,
        "client_email": invoice.client.email,
        "client_phone": invoice.client.phone,
    })


@require_POST
def razorpay_verify_payment(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    from dashboard.models import SiteSettings
    cfg = SiteSettings.load()
    if not cfg.razorpay_enabled:
        return JsonResponse({"error": "Not enabled."}, status=400)
    import razorpay
    rp_client = razorpay.Client(auth=(cfg.razorpay_key_id, cfg.razorpay_key_secret))
    params = {
        "razorpay_order_id": request.POST.get("razorpay_order_id", ""),
        "razorpay_payment_id": request.POST.get("razorpay_payment_id", ""),
        "razorpay_signature": request.POST.get("razorpay_signature", ""),
    }
    try:
        rp_client.utility.verify_payment_signature(params)
    except Exception:
        return JsonResponse({"error": "Signature mismatch — payment not verified."}, status=400)
    from django.utils import timezone
    Payment.objects.create(
        invoice=invoice,
        amount_paid=invoice.amount,
        payment_date=timezone.now().date(),
        payment_mode="online",
        reference=params["razorpay_payment_id"],
        notes=f"Paid via Razorpay. Order: {params['razorpay_order_id']}",
    )
    invoice.status = "paid"
    invoice.save(update_fields=["status"])
    return JsonResponse({"ok": True, "redirect": f"/billing/{invoice.pk}/"})


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
