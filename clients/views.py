import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from .models import Client, Contract, ClientContact, ClientInteraction, ContractTemplate
from .forms import ClientForm, ContractForm, ClientContactForm, ClientInteractionForm, ContractTemplateForm


def _can_edit(user):
    return user.is_admin() or user.is_accounts()


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
    contracts = client.contracts.all()
    contacts = client.contacts.all()
    interactions = client.interactions.select_related("created_by").all()

    invoices = client.invoices.all()
    financial = invoices.aggregate(
        total_billed=Sum("amount"),
        total_paid=Sum("amount", filter=Q(status="paid")),
        total_pending=Sum("amount", filter=Q(status="pending")),
        total_overdue=Sum("amount", filter=Q(status="overdue")),
    )
    for key in financial:
        if financial[key] is None:
            financial[key] = 0

    lead_activities = None
    if client.linked_lead_id:
        lead_activities = (
            client.linked_lead.activities
            .select_related("created_by")
            .order_by("-created_at")
        )
    from dashboard.models import AuditLog, QuickNote
    audit_logs = AuditLog.objects.filter(model_name="Client", object_id=pk).select_related("user")[:20]
    quick_notes = QuickNote.objects.filter(client_id=pk).select_related("user")
    return render(request, "clients/client_detail.html", {
        "client": client,
        "contracts": contracts,
        "contacts": contacts,
        "interactions": interactions,
        "financial": financial,
        "lead_activities": lead_activities,
        "audit_logs": audit_logs,
        "quick_notes": quick_notes,
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
    return render(request, "portal/home.html", {
        "client": client,
        "invoices": invoices,
        "contracts": contracts,
        "interactions": interactions,
        "financial": financial,
    })


@login_required
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
def contract_template_list(request):
    templates = ContractTemplate.objects.all()
    return render(request, "clients/contract_template_list.html", {"templates": templates})


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
    return render(request, "clients/contract_template_form.html", {"form": form, "title": "New Contract Template"})


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
    return render(request, "clients/contract_template_form.html", {"form": form, "title": "Edit Template", "tmpl": tmpl})


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
        messages.success(request, "Contract created.")
        return redirect("clients:contract_detail", pk=contract.pk)
    return render(request, "clients/contract_form.html", {
        "form": form, "client": client, "title": "Add Contract",
        "contract_templates": ContractTemplate.objects.all(),
    })


@login_required
def contract_detail(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    return render(request, "clients/contract_detail.html", {"contract": contract})


@login_required
def contract_edit(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if not _can_edit(request.user):
        messages.error(request, "Access denied.")
        return redirect("clients:contract_detail", pk=pk)
    form = ContractForm(request.POST or None, request.FILES or None, instance=contract)
    if form.is_valid():
        form.save()
        messages.success(request, "Contract updated.")
        return redirect("clients:contract_detail", pk=pk)
    return render(request, "clients/contract_form.html", {"form": form, "title": "Edit Contract", "contract": contract})
