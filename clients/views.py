from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Client, Contract
from .forms import ClientForm, ContractForm


@login_required
def client_list(request):
    q = request.GET.get("q", "")
    clients = Client.objects.all()
    if q:
        clients = clients.filter(
            Q(organization_name__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q)
        )
    return render(request, "clients/client_list.html", {"clients": clients, "q": q})


@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    contracts = client.contracts.all()
    return render(request, "clients/client_detail.html", {"client": client, "contracts": contracts})


@login_required
def client_create(request):
    if not (request.user.is_admin() or request.user.is_accounts()):
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
    if not (request.user.is_admin() or request.user.is_accounts()):
        messages.error(request, "Access denied.")
        return redirect("clients:client_detail", pk=pk)
    form = ClientForm(request.POST or None, instance=client)
    if form.is_valid():
        form.save()
        messages.success(request, "Client updated.")
        return redirect("clients:client_detail", pk=pk)
    return render(request, "clients/client_form.html", {"form": form, "title": "Edit Client", "client": client})


@login_required
def contract_create(request, client_pk):
    client = get_object_or_404(Client, pk=client_pk)
    if not (request.user.is_admin() or request.user.is_accounts()):
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
    if not (request.user.is_admin() or request.user.is_accounts()):
        messages.error(request, "Access denied.")
        return redirect("clients:contract_detail", pk=pk)
    form = ContractForm(request.POST or None, request.FILES or None, instance=contract)
    if form.is_valid():
        form.save()
        messages.success(request, "Contract updated.")
        return redirect("clients:contract_detail", pk=pk)
    return render(request, "clients/contract_form.html", {"form": form, "title": "Edit Contract", "contract": contract})
