import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from .models import Client, Contract, ClientContact, ClientInteraction
from .forms import ClientForm, ContractForm, ClientContactForm, ClientInteractionForm


def _can_edit(user):
    return user.is_admin() or user.is_accounts()


@login_required
def client_list(request):
    q = request.GET.get("q", "")
    status = request.GET.get("status", "")
    clients = Client.objects.prefetch_related("contacts").annotate(
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
    return render(request, "clients/client_list.html", {
        "clients": clients,
        "q": q,
        "status": status,
        "status_choices": Client.STATUS_CHOICES,
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
    return render(request, "clients/client_detail.html", {
        "client": client,
        "contracts": contracts,
        "contacts": contacts,
        "interactions": interactions,
        "financial": financial,
        "lead_activities": lead_activities,
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
        return redirect("clients:client_detail", pk=client.pk)
    return render(request, "clients/client_form.html", {"form": form, "title": "Add Client"})


@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if not _can_edit(request.user):
        messages.error(request, "Access denied.")
        return redirect("clients:client_detail", pk=pk)
    form = ClientForm(request.POST or None, instance=client)
    if form.is_valid():
        form.save()
        messages.success(request, "Client updated.")
        return redirect("clients:client_detail", pk=pk)
    return render(request, "clients/client_form.html", {"form": form, "title": "Edit Client", "client": client})


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
    return render(request, "clients/contract_form.html", {"form": form, "client": client, "title": "Add Contract"})


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
