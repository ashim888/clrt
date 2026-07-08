import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from .models import Client, Contract, ClientContact, ClientInteraction, ContractTemplate, ContractDocument
from .forms import ClientForm, ContractForm, ClientContactForm, ClientInteractionForm, ContractTemplateForm
from dashboard.decorators import requires_feature
from django.utils import timezone

def _can_edit(user):
    return user.is_admin() or user.is_accounts()


_CONTRACT_PLACEHOLDERS = [
    "[Client Name]",
    "[Contact Person]",
    "[Contract Title]",
    "[Contract Value]",
    "[Start Date]",
    "[End Date]",
    "[Billing Cycle]",
    "[Payment Terms]",
    "[Your Company Name]",
    "[Your Company Address]",
]


_CLIENT_SORT = {"name": "organization_name", "status": "status", "billed": "total_billed", "created": "created_at"}

@login_required
def client_list(request):
    q = request.GET.get("q", "")
    status = request.GET.get("status", "")
    tag = request.GET.get("tag", "")
    sort = request.GET.get("sort", "name")
    order = request.GET.get("order", "asc")
    clients = Client.objects.prefetch_related("contacts", "tags").annotate(
        total_billed=Sum("invoices__amount"),
        total_paid=Sum("invoices__amount", filter=Q(invoices__status="paid")),
    )
    if q:
        clients = clients.filter(
            Q(organization_name__icontains=q)
            | Q(email__icontains=q)
            | Q(phone__icontains=q)
            | Q(industry__icontains=q)
        )
    if status:
        clients = clients.filter(status=status)
    if tag:
        clients = clients.filter(tags__pk=tag)
    sort_field = _CLIENT_SORT.get(sort, "organization_name")
    clients = clients.order_by(f"{'-' if order == 'desc' else ''}{sort_field}")
    paginator = Paginator(clients, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    from dashboard.models import Tag
    return render(request, "clients/client_list.html", {
        "clients": page_obj,
        "page_obj": page_obj,
        "q": q,
        "status": status,
        "tag": tag,
        "sort": sort,
        "order": order,
        "status_choices": Client.STATUS_CHOICES,
        "all_tags": Tag.objects.all(),
    })


@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    contracts = client.contracts.prefetch_related("documents").all()
    contacts = client.contacts.all()
    interactions = client.interactions.select_related("created_by").all()

    from billing.models import Payment
    from datetime import date as _date
    import json as _json

    invoices = list(client.invoices.all())
    total_billed = sum(inv.final_amount for inv in invoices)
    all_payments = list(Payment.objects.filter(invoice__client=client))
    total_paid_actual = sum(p.amount_paid for p in all_payments)
    total_overdue = sum(inv.final_amount for inv in invoices if inv.status == "overdue")
    total_pending = sum(inv.final_amount for inv in invoices if inv.status in ("pending", "overdue"))
    financial = {
        "total_billed": total_billed,
        "total_paid": total_paid_actual,
        "total_pending": total_pending,
        "total_overdue": total_overdue,
        "outstanding": total_billed - total_paid_actual,
    }

    # Build last-12-months chart data
    today = timezone.now().date()
    chart_months = []
    for i in range(11, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        chart_months.append(_date(y, m, 1))

    billed_by_month = {}
    for inv in invoices:
        key = inv.generated_date.replace(day=1)
        billed_by_month[key] = float(billed_by_month.get(key, 0)) + float(inv.final_amount)

    paid_by_month = {}
    for p in all_payments:
        key = p.payment_date.replace(day=1)
        paid_by_month[key] = float(paid_by_month.get(key, 0)) + float(p.amount_paid)

    chart_data = {
        "labels": [m.strftime("%b %Y") for m in chart_months],
        "billed": [round(billed_by_month.get(m, 0), 2) for m in chart_months],
        "paid": [round(paid_by_month.get(m, 0), 2) for m in chart_months],
    }

    lead_activities = None
    if client.linked_lead_id:
        lead_activities = (
            client.linked_lead.activities
            .select_related("created_by")
            .order_by("-created_at")
        )
    from dashboard.models import AuditLog, QuickNote
    from dashboard.activity import get_events_for
    audit_logs = AuditLog.objects.filter(model_name="Client", object_id=pk).select_related("user")[:20]
    quick_notes = QuickNote.objects.filter(client_id=pk).select_related("user")
    return render(request, "clients/client_detail.html", {
        "client": client,
        "contracts": contracts,
        "contacts": contacts,
        "interactions": interactions,
        "financial": financial,
        "chart_data": _json.dumps(chart_data),
        "lead_activities": lead_activities,
        "audit_logs": audit_logs,
        "quick_notes": quick_notes,
        "timeline_events": get_events_for(client),
    })


@login_required
def client_create(request):
    if not _can_edit(request.user):
        messages.error(request, "Access denied.")
        return redirect("clients:client_list")
    form = ClientForm(request.POST or None)
    if form.is_valid():
        client = form.save()
        messages.success(request, f"Client \"{client.organization_name}\" created.")
        from dashboard.audit import log_audit
        log_audit(request.user, 'created', client)
        from dashboard.activity import log_event
        log_event(client, 'created', actor=request.user, description=f"Client created by {request.user.get_full_name() or request.user.username}")
        return redirect("clients:client_detail", pk=client.pk)
    from dashboard.models import Tag
    return render(request, "clients/client_form.html", {
        "form": form, "title": "Add Client",
        "all_tags": Tag.objects.all(), "selected_tags": [],
    })


@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if not _can_edit(request.user):
        messages.error(request, "Access denied.")
        return redirect("clients:client_detail", pk=pk)
    form = ClientForm(request.POST or None, instance=client)
    if form.is_valid():
        from dashboard.audit import log_audit, model_changes
        old = Client.objects.get(pk=pk)
        form.save()
        client.refresh_from_db()
        diff = model_changes(old, client, ["organization_name", "phone", "email", "industry", "status", "website", "address", "notes"])
        if diff:
            log_audit(request.user, 'updated', client, diff)
        from dashboard.activity import log_event
        log_event(client, 'edited', actor=request.user, description=f"Client updated by {request.user.get_full_name() or request.user.username}", metadata=diff or {})
        messages.success(request, "Client updated.")
        return redirect("clients:client_detail", pk=pk)
    from dashboard.models import Tag
    return render(request, "clients/client_form.html", {
        "form": form, "title": "Edit Client", "client": client,
        "all_tags": Tag.objects.all(), "selected_tags": client.tags.all(),
    })


@login_required
def client_check_duplicate(request):
    org = request.GET.get("org", "").strip()
    email = request.GET.get("email", "").strip()
    exclude_pk = request.GET.get("pk")
    if not org and not email:
        return JsonResponse({"duplicates": []})
    qs = Client.objects
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    matches = []
    if org:
        for c in qs.filter(organization_name__iexact=org)[:3]:
            matches.append({"pk": c.pk, "org": c.organization_name, "status": c.get_status_display()})
    if email and not matches:
        for c in qs.filter(email__iexact=email)[:3]:
            matches.append({"pk": c.pk, "org": c.organization_name, "status": c.get_status_display()})
    return JsonResponse({"duplicates": matches})


@login_required
def client_export_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="clients.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "Organization", "Status", "Industry", "Email", "Phone", "Website", "Since",
        "Total Billed (Rs)", "Collected (Rs)",
    ])
    clients = Client.objects.annotate(
        total_billed=Sum("invoices__amount"),
        total_paid=Sum("invoices__amount", filter=Q(invoices__status="paid")),
    ).order_by("organization_name")
    for c in clients:
        writer.writerow([
            c.organization_name,
            c.get_status_display(),
            c.industry,
            c.email,
            c.phone,
            c.website,
            c.created_at.strftime("%Y-%m-%d"),
            c.total_billed or 0,
            c.total_paid or 0,
        ])
    return response


@login_required
@require_POST
def client_interaction_mark_done(request, pk):
    interaction = get_object_or_404(ClientInteraction, pk=pk)
    interaction.follow_up_done = True
    interaction.save(update_fields=["follow_up_done"])
    return JsonResponse({"ok": True})


# ── Client Portal ────────────────────────────────────────────────────────────

def portal_home(request, token):
    """Public token-based client portal — no login required."""
    from dashboard.models import SiteSettings
    client = get_object_or_404(Client, portal_token=token)
    invoices = client.invoices.order_by("-generated_date")
    contracts = client.contracts.all()
    interactions = client.interactions.order_by("-created_at")[:10]
    financial = invoices.aggregate(
        total_billed=Sum("amount"),
        total_paid=Sum("amount", filter=Q(status="paid")),
        total_pending=Sum("amount", filter=Q(status__in=["pending", "overdue"])),
    )
    for k in financial:
        if financial[k] is None:
            financial[k] = 0
    cfg = SiteSettings.load()
    razorpay_configured = cfg.razorpay_enabled and bool(cfg.razorpay_key_id) and bool(cfg.razorpay_key_secret)
    return render(request, "portal/home.html", {
        "client": client,
        "invoices": invoices,
        "contracts": contracts,
        "interactions": interactions,
        "financial": financial,
        "razorpay_configured": razorpay_configured,
        "token": token,
    })


@require_POST
def portal_razorpay_create_order(request, token, invoice_pk):
    from dashboard.models import SiteSettings
    from billing.models import Invoice
    client = get_object_or_404(Client, portal_token=token)
    invoice = get_object_or_404(Invoice, pk=invoice_pk, client=client)
    if invoice.status == "paid":
        return JsonResponse({"error": "Invoice already paid."}, status=400)
    cfg = SiteSettings.load()
    if not cfg.razorpay_enabled or not cfg.razorpay_key_id or not cfg.razorpay_key_secret:
        return JsonResponse({"error": "Payment gateway not configured."}, status=400)
    import razorpay
    import logging
    logger = logging.getLogger(__name__)
    rp = razorpay.Client(auth=(cfg.razorpay_key_id, cfg.razorpay_key_secret))
    amount_paise = int(float(invoice.final_amount) * 100)
    try:
        order = rp.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": invoice.invoice_number[:40],
            "notes": {"invoice_id": str(invoice.pk)},
        })
    except razorpay.errors.BadRequestError as e:
        logger.error("Razorpay order creation failed (BadRequest): %s", e)
        return JsonResponse({"error": f"Payment gateway error: {e}"}, status=400)
    except Exception as e:
        logger.exception("Razorpay order creation failed")
        return JsonResponse({"error": "Could not create payment order. Please try again."}, status=500)
    return JsonResponse({
        "order_id": order["id"],
        "amount": amount_paise,
        "currency": "INR",
        "key_id": cfg.razorpay_key_id,
        "invoice_number": invoice.invoice_number,
        "client_name": client.organization_name,
        "client_email": client.email or "",
        "client_phone": client.phone or "",
    })


@require_POST
def portal_razorpay_verify(request, token, invoice_pk):
    from dashboard.models import SiteSettings
    from billing.models import Invoice, Payment
    from django.utils import timezone
    client = get_object_or_404(Client, portal_token=token)
    invoice = get_object_or_404(Invoice, pk=invoice_pk, client=client)
    cfg = SiteSettings.load()
    if not cfg.razorpay_enabled:
        return JsonResponse({"error": "Not enabled."}, status=400)
    import razorpay
    rp = razorpay.Client(auth=(cfg.razorpay_key_id, cfg.razorpay_key_secret))
    params = {
        "razorpay_order_id": request.POST.get("razorpay_order_id", ""),
        "razorpay_payment_id": request.POST.get("razorpay_payment_id", ""),
        "razorpay_signature": request.POST.get("razorpay_signature", ""),
    }
    try:
        rp.utility.verify_payment_signature(params)
    except Exception:
        return JsonResponse({"error": "Signature mismatch — payment not verified."}, status=400)
    Payment.objects.create(
        invoice=invoice,
        amount_paid=invoice.final_amount,
        payment_date=timezone.now().date(),
        payment_mode="online",
        reference=params["razorpay_payment_id"],
        notes=f"Paid via Razorpay (client portal). Order: {params['razorpay_order_id']}",
    )
    invoice.status = "paid"
    invoice.save(update_fields=["status"])
    return JsonResponse({"ok": True, "redirect": f"/clients/portal/{token}/"})


@requires_feature('has_client_portal')
@require_POST
def portal_regenerate_token(request, pk):
    import uuid as _uuid
    client = get_object_or_404(Client, pk=pk)
    if not _can_edit(request.user):
        messages.error(request, "Access denied.")
        return redirect("clients:client_detail", pk=pk)
    client.portal_token = _uuid.uuid4()
    client.save(update_fields=["portal_token"])
    messages.success(request, "Portal link regenerated. The old link is now invalid.")
    return redirect("clients:client_detail", pk=pk)


# ── Contract Templates ───────────────────────────────────────────────────────

@login_required
def contract_list(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    contracts = Contract.objects.select_related("client").prefetch_related("invoices")
    if q:
        contracts = contracts.filter(
            Q(contract_title__icontains=q) | Q(contract_number__icontains=q) | Q(client__organization_name__icontains=q)
        )
    if status:
        contracts = contracts.filter(status=status)
    return render(request, "clients/contract_list.html", {
        "contracts": contracts,
        "q": q,
        "status_filter": status,
        "status_choices": Contract.STATUS_CHOICES,
    })


@login_required
def contract_template_list(request):
    templates = ContractTemplate.objects.all()
    return render(request, "clients/contract_template_list.html", {"templates": templates})


@login_required
def contract_template_detail(request, pk):
    tmpl = get_object_or_404(ContractTemplate, pk=pk)
    return render(request, "clients/contract_template_detail.html", {
        "tmpl": tmpl,
        "placeholders": _CONTRACT_PLACEHOLDERS,
    })


@login_required
def contract_template_create(request):
    if not _can_edit(request.user):
        messages.error(request, "Access denied.")
        return redirect("clients:contract_template_list")
    form = ContractTemplateForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Template created.")
        return redirect("clients:contract_template_list")
    return render(request, "clients/contract_template_form.html", {
        "form": form, "title": "New Contract Template",
        "placeholders": _CONTRACT_PLACEHOLDERS,
    })


@login_required
def contract_template_edit(request, pk):
    tmpl = get_object_or_404(ContractTemplate, pk=pk)
    if not _can_edit(request.user):
        messages.error(request, "Access denied.")
        return redirect("clients:contract_template_list")
    form = ContractTemplateForm(request.POST or None, instance=tmpl)
    if form.is_valid():
        form.save()
        messages.success(request, "Template updated.")
        return redirect("clients:contract_template_list")
    return render(request, "clients/contract_template_form.html", {
        "form": form, "title": "Edit Template", "tmpl": tmpl,
        "placeholders": _CONTRACT_PLACEHOLDERS,
    })


@login_required
@require_POST
def contract_template_delete(request, pk):
    tmpl = get_object_or_404(ContractTemplate, pk=pk)
    if not _can_edit(request.user):
        messages.error(request, "Access denied.")
        return redirect("clients:contract_template_list")
    tmpl.delete()
    messages.success(request, "Template deleted.")
    return redirect("clients:contract_template_list")


@login_required
def contract_template_json(request, pk):
    tmpl = get_object_or_404(ContractTemplate, pk=pk)
    return JsonResponse({
        "billing_cycle": tmpl.billing_cycle,
        "default_value": str(tmpl.default_value) if tmpl.default_value else "",
        "body": tmpl.body,
        "notes": tmpl.notes,
    })


# ── Client Contacts ─────────────────────────────────────────────────────────

@login_required
def client_contact_add(request, client_pk):
    client = get_object_or_404(Client, pk=client_pk)
    form = ClientContactForm(request.POST or None)
    if form.is_valid():
        contact = form.save(commit=False)
        contact.client = client
        # If marking as primary, unset existing primary
        if contact.is_primary:
            client.contacts.filter(is_primary=True).update(is_primary=False)
        contact.save()
        messages.success(request, f"Contact \"{contact.name}\" added.")
        return redirect("clients:client_detail", pk=client_pk)
    return render(request, "clients/client_contact_form.html", {
        "form": form, "client": client, "title": "Add Contact",
    })


@login_required
def client_contact_edit(request, pk):
    contact = get_object_or_404(ClientContact, pk=pk)
    client = contact.client
    form = ClientContactForm(request.POST or None, instance=contact)
    if form.is_valid():
        updated = form.save(commit=False)
        if updated.is_primary:
            client.contacts.exclude(pk=pk).filter(is_primary=True).update(is_primary=False)
        updated.save()
        messages.success(request, "Contact updated.")
        return redirect("clients:client_detail", pk=client.pk)
    return render(request, "clients/client_contact_form.html", {
        "form": form, "client": client, "title": "Edit Contact", "contact": contact,
    })


@login_required
@require_POST
def client_contact_delete(request, pk):
    contact = get_object_or_404(ClientContact, pk=pk)
    client_pk = contact.client.pk
    contact.delete()
    messages.success(request, "Contact removed.")
    return redirect("clients:client_detail", pk=client_pk)


# ── Client Interactions ──────────────────────────────────────────────────────

@login_required
def client_interaction_add(request, client_pk):
    client = get_object_or_404(Client, pk=client_pk)
    form = ClientInteractionForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        interaction = form.save(commit=False)
        interaction.client = client
        interaction.created_by = request.user
        interaction.save()
        from dashboard.activity import log_event
        log_event(client, 'interaction', actor=request.user,
                  description=f"{interaction.get_type_display()} logged: {interaction.notes[:80] if interaction.notes else '—'}")
        messages.success(request, "Interaction logged.")
        return redirect("clients:client_detail", pk=client_pk)
    return render(request, "clients/client_interaction_form.html", {
        "form": form, "client": client, "title": "Log Interaction",
    })


@login_required
def client_interaction_edit(request, pk):
    interaction = get_object_or_404(ClientInteraction, pk=pk)
    client = interaction.client
    form = ClientInteractionForm(request.POST or None, request.FILES or None, instance=interaction)
    if form.is_valid():
        form.save()
        messages.success(request, "Interaction updated.")
        return redirect("clients:client_detail", pk=client.pk)
    return render(request, "clients/client_interaction_form.html", {
        "form": form, "client": client, "title": "Edit Interaction", "editing": True,
    })


@login_required
@require_POST
def client_interaction_delete(request, pk):
    interaction = get_object_or_404(ClientInteraction, pk=pk)
    client_pk = interaction.client.pk
    interaction.delete()
    messages.success(request, "Interaction deleted.")
    return redirect("clients:client_detail", pk=client_pk)


# ── Contracts ────────────────────────────────────────────────────────────────

@login_required
def contract_create(request, client_pk):
    client = get_object_or_404(Client, pk=client_pk)
    if not _can_edit(request.user):
        messages.error(request, "Access denied.")
        return redirect("clients:client_detail", pk=client_pk)
    form = ContractForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        contract = form.save(commit=False)
        contract.client = client
        contract.save()
        for f in request.FILES.getlist("documents"):
            ContractDocument.objects.create(contract=contract, file=f)
        from dashboard.activity import log_event
        log_event(contract, 'created', actor=request.user,
                  description=f"Contract {contract.contract_number} created")
        log_event(client, 'created', actor=request.user,
                  description=f"Contract {contract.contract_number} ({contract.contract_title}) created")
        messages.success(request, "Contract created.")
        return redirect("clients:contract_detail", pk=contract.pk)
    return render(request, "clients/contract_form.html", {
        "form": form, "client": client, "title": "Add Contract",
        "contract_templates": ContractTemplate.objects.all(),
    })


@login_required
def contract_detail(request, pk):
    from django.utils import timezone
    from dashboard.activity import get_events_for as _get_contract_events

    contract = get_object_or_404(Contract, pk=pk)
    invoices = contract.invoices.order_by("-generated_date")

    # Billing summary
    billed_total = sum(inv.final_amount for inv in invoices)
    paid_total = sum(
        inv.payments.aggregate(t=Sum("amount_paid"))["t"] or 0
        for inv in invoices
    )
    outstanding = billed_total - paid_total
    billed_pct = min(int(billed_total / contract.contract_value * 100), 100) if contract.contract_value else 0

    # Duration progress
    today = timezone.now().date()
    total_days = (contract.end_date - contract.start_date).days or 1
    elapsed_days = (today - contract.start_date).days
    duration_pct = max(0, min(int(elapsed_days / total_days * 100), 100))
    days_remaining = (contract.end_date - today).days

    return render(request, "clients/contract_detail.html", {
        "contract": contract,
        "documents": contract.documents.all(),
        "invoices": invoices,
        "billed_total": billed_total,
        "paid_total": paid_total,
        "outstanding": outstanding,
        "billed_pct": billed_pct,
        "duration_pct": duration_pct,
        "days_remaining": days_remaining,
        "today": today,
        "timeline_events": _get_contract_events(contract),
    })


@login_required
def contract_edit(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if not _can_edit(request.user):
        messages.error(request, "Access denied.")
        return redirect("clients:contract_detail", pk=pk)
    form = ContractForm(request.POST or None, request.FILES or None, instance=contract)
    if form.is_valid():
        form.save()
        for doc_pk in request.POST.getlist("delete_document"):
            ContractDocument.objects.filter(pk=doc_pk, contract=contract).delete()
        for f in request.FILES.getlist("documents"):
            ContractDocument.objects.create(contract=contract, file=f)
        messages.success(request, "Contract updated.")
        return redirect("clients:contract_detail", pk=pk)
    return render(request, "clients/contract_form.html", {
        "form": form, "title": "Edit Contract", "contract": contract,
        "client": contract.client,
        "existing_docs": contract.documents.all(),
        "contract_templates": ContractTemplate.objects.all(),
    })


@login_required
@require_POST
def contract_document_delete(request, pk):
    doc = get_object_or_404(ContractDocument, pk=pk)
    contract_pk = doc.contract_id
    if not _can_edit(request.user):
        messages.error(request, "Access denied.")
        return redirect("clients:contract_detail", pk=contract_pk)
    doc.file.delete(save=False)
    doc.delete()
    messages.success(request, "Document removed.")
    return redirect("clients:contract_detail", pk=contract_pk)


@login_required
@require_POST
def client_bulk_action(request):
    if not _can_edit(request.user):
        return JsonResponse({"error": "Permission denied"}, status=403)
    ids = request.POST.getlist("ids")
    action = request.POST.get("action")
    if not ids or not action:
        return JsonResponse({"error": "Missing ids or action"}, status=400)
    qs = Client.objects.filter(pk__in=ids)
    if action == "delete":
        if not request.user.is_admin():
            return JsonResponse({"error": "Only admins can delete clients"}, status=403)
        qs.delete()
    elif action == "status":
        value = request.POST.get("value")
        valid = [s for s, _ in Client.STATUS_CHOICES]
        if value not in valid:
            return JsonResponse({"error": "Invalid status"}, status=400)
        qs.update(status=value)
    elif action == "tag_add":
        from dashboard.models import Tag
        tag = Tag.objects.filter(pk=request.POST.get("value")).first()
        if not tag:
            return JsonResponse({"error": "Tag not found"}, status=400)
        for client in qs:
            client.tags.add(tag)
    elif action == "tag_remove":
        from dashboard.models import Tag
        tag = Tag.objects.filter(pk=request.POST.get("value")).first()
        if tag:
            for client in qs:
                client.tags.remove(tag)
    else:
        return JsonResponse({"error": "Unknown action"}, status=400)
    return JsonResponse({"ok": True, "count": len(ids)})


@login_required
@require_POST
def client_send_email(request, pk):
    client = get_object_or_404(Client, pk=pk)
    to = request.POST.get("to", "").strip()
    subject = request.POST.get("subject", "").strip()
    body = request.POST.get("body", "").strip()

    if not to or not subject or not body:
        return JsonResponse({"error": "To, subject and body are required."}, status=400)

    from django.core.mail import send_mail
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email(to)
    except ValidationError:
        return JsonResponse({"error": "Invalid email address."}, status=400)

    try:
        send_mail(subject, body, None, [to], fail_silently=False)
    except Exception as e:
        return JsonResponse({"error": f"Failed to send: {e}"}, status=500)

    ClientInteraction.objects.create(
        client=client,
        type="email",
        notes=body,
        email_to=to,
        email_subject=subject,
        created_by=request.user,
    )


# ── E-SIGNATURE ──────────────────────────────────────────────────────────────

def contract_sign(request, token):
    contract = get_object_or_404(Contract, sign_token=token)
    already_signed = bool(contract.signature_at)

    if request.method == "POST" and not already_signed:
        name = request.POST.get("signer_name", "").strip()
        data = request.POST.get("signature_data", "").strip()
        if name and data:
            ip = (
                request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
                or request.META.get("REMOTE_ADDR", "")
            )
            from django.utils import timezone as tz
            contract.signature_name = name
            contract.signature_ip = ip or None
            contract.signature_at = tz.now()
            contract.signature_data = data
            contract.save(update_fields=["signature_name", "signature_ip", "signature_at", "signature_data"])
            from dashboard.activity import log_event
            log_event(contract, 'signed', description=f"Contract signed by {name} (IP: {ip or 'unknown'})")
            log_event(contract.client, 'signed', description=f"Contract {contract.contract_number} signed by {name}")
            return redirect("clients:contract_sign_done", token=token)

    return render(request, "clients/contract_sign.html", {
        "contract": contract,
        "already_signed": already_signed,
    })


def contract_sign_done(request, token):
    contract = get_object_or_404(Contract, sign_token=token)
    return render(request, "clients/contract_sign_done.html", {"contract": contract})
    return JsonResponse({"ok": True})
