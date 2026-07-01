from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Quote, QuoteLineItem
from leads.models import Lead
from clients.models import Client


def _save_line_items(quote, post):
    descriptions = post.getlist("item_description[]")
    quantities = post.getlist("item_quantity[]")
    unit_prices = post.getlist("item_unit_price[]")
    quote.items.all().delete()
    for i, desc in enumerate(descriptions):
        desc = desc.strip()
        if not desc:
            continue
        try:
            qty = float(quantities[i] or 1)
            price = float(unit_prices[i] or 0)
        except (IndexError, ValueError):
            continue
        QuoteLineItem.objects.create(
            quote=quote, description=desc,
            quantity=qty, unit_price=price, order=i,
        )


@login_required
def quote_list(request):
    q = request.GET.get("q", "")
    status = request.GET.get("status", "")
    quotes = Quote.objects.select_related("lead", "client", "created_by")
    if q:
        quotes = quotes.filter(
            Q(title__icontains=q) |
            Q(quote_number__icontains=q) |
            Q(lead__organization_name__icontains=q) |
            Q(client__organization_name__icontains=q)
        )
    if status:
        quotes = quotes.filter(status=status)
    return render(request, "proposals/quote_list.html", {
        "quotes": quotes,
        "q": q,
        "status": status,
        "status_choices": Quote.STATUS_CHOICES,
    })


@login_required
def quote_detail(request, pk):
    quote = get_object_or_404(Quote, pk=pk)
    return render(request, "proposals/quote_detail.html", {"quote": quote})


@login_required
def quote_create(request):
    leads = Lead.objects.exclude(status__in=["won", "lost"]).order_by("organization_name")
    clients = Client.objects.order_by("organization_name")
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        valid_until = request.POST.get("valid_until", "")
        status = request.POST.get("status", "draft")
        notes = request.POST.get("notes", "").strip()
        terms = request.POST.get("terms", "").strip()
        lead_id = request.POST.get("lead_id", "")
        client_id = request.POST.get("client_id", "")
        if not title or not valid_until:
            messages.error(request, "Title and valid until date are required.")
        else:
            quote = Quote(
                title=title, valid_until=valid_until, status=status,
                notes=notes, terms=terms, created_by=request.user,
            )
            if lead_id:
                quote.lead_id = int(lead_id)
            elif client_id:
                quote.client_id = int(client_id)
            quote.save()
            _save_line_items(quote, request.POST)
            messages.success(request, f"Proposal {quote.quote_number} created.")
            return redirect("proposals:quote_detail", pk=quote.pk)
    return render(request, "proposals/quote_form.html", {
        "leads": leads,
        "clients": clients,
        "status_choices": Quote.STATUS_CHOICES,
        "title": "New Proposal",
    })


@login_required
def quote_edit(request, pk):
    quote = get_object_or_404(Quote, pk=pk)
    leads = Lead.objects.order_by("organization_name")
    clients = Client.objects.order_by("organization_name")
    if request.method == "POST":
        quote.title = request.POST.get("title", "").strip()
        quote.valid_until = request.POST.get("valid_until", "")
        quote.status = request.POST.get("status", "draft")
        quote.notes = request.POST.get("notes", "").strip()
        quote.terms = request.POST.get("terms", "").strip()
        lead_id = request.POST.get("lead_id", "")
        client_id = request.POST.get("client_id", "")
        quote.lead = None
        quote.client = None
        if lead_id:
            quote.lead_id = int(lead_id)
        elif client_id:
            quote.client_id = int(client_id)
        quote.save()
        _save_line_items(quote, request.POST)
        messages.success(request, "Proposal updated.")
        return redirect("proposals:quote_detail", pk=quote.pk)
    return render(request, "proposals/quote_form.html", {
        "quote": quote,
        "leads": leads,
        "clients": clients,
        "status_choices": Quote.STATUS_CHOICES,
        "title": f"Edit {quote.quote_number}",
        "editing": True,
    })


@login_required
@require_POST
def quote_update_status(request, pk):
    quote = get_object_or_404(Quote, pk=pk)
    new_status = request.POST.get("status", "")
    valid = [s for s, _ in Quote.STATUS_CHOICES]
    if new_status not in valid:
        return JsonResponse({"error": "Invalid status"}, status=400)
    quote.status = new_status
    quote.save(update_fields=["status"])
    return JsonResponse({"status": new_status, "label": quote.get_status_display()})


@login_required
def quote_print(request, pk):
    quote = get_object_or_404(Quote, pk=pk)
    return render(request, "proposals/quote_print.html", {"quote": quote})
