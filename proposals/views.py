from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Quote, QuoteLineItem
from leads.models import Lead
from clients.models import Client
from dashboard.decorators import requires_feature


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


_QUOTE_SORT = {"date": "created_at", "status": "status", "title": "title", "valid": "valid_until"}

@requires_feature('has_proposals')
def quote_list(request):
    q = request.GET.get("q", "")
    status = request.GET.get("status", "")
    sort = request.GET.get("sort", "date")
    order = request.GET.get("order", "desc")
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
    sort_field = _QUOTE_SORT.get(sort, "created_at")
    quotes = quotes.order_by(f"{'-' if order == 'desc' else ''}{sort_field}")
    paginator = Paginator(quotes, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "proposals/quote_list.html", {
        "quotes": page_obj,
        "page_obj": page_obj,
        "q": q,
        "status": status,
        "sort": sort,
        "order": order,
        "status_choices": Quote.STATUS_CHOICES,
    })


@requires_feature('has_proposals')
def quote_detail(request, pk):
    quote = get_object_or_404(Quote, pk=pk)
    return render(request, "proposals/quote_detail.html", {"quote": quote})


@requires_feature('has_proposals')
def quote_create(request):
    from dashboard.models import SiteSettings
    cfg = SiteSettings.load()
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
        try:
            discount_percent = float(request.POST.get("discount_percent") or 0)
        except ValueError:
            discount_percent = 0.0
        try:
            tax_rate = float(request.POST.get("tax_rate") or cfg.default_tax_rate)
        except ValueError:
            tax_rate = float(cfg.default_tax_rate)
        max_discount = float(cfg.max_discount_percent)
        if max_discount > 0 and discount_percent > max_discount:
            messages.error(request, f"Discount cannot exceed {max_discount}% (configured in Settings).")
            return render(request, "proposals/quote_form.html", {
                "leads": leads, "clients": clients,
                "status_choices": Quote.STATUS_CHOICES, "title": "New Quotation",
            })
        if not title or not valid_until:
            messages.error(request, "Title and valid until date are required.")
        else:
            quote = Quote(
                title=title, valid_until=valid_until, status=status,
                notes=notes, terms=terms, created_by=request.user,
                discount_percent=discount_percent, tax_rate=tax_rate,
            )
            if lead_id:
                quote.lead_id = int(lead_id)
            elif client_id:
                quote.client_id = int(client_id)
            quote.save()
            _save_line_items(quote, request.POST)
            messages.success(request, f"Quotation {quote.quote_number} created.")
            return redirect("proposals:quote_detail", pk=quote.pk)
    return render(request, "proposals/quote_form.html", {
        "leads": leads,
        "clients": clients,
        "status_choices": Quote.STATUS_CHOICES,
        "title": "New Quotation",
    })


@requires_feature('has_proposals')
def quote_edit(request, pk):
    quote = get_object_or_404(Quote, pk=pk)
    leads = Lead.objects.order_by("organization_name")
    clients = Client.objects.order_by("organization_name")
    if request.method == "POST":
        from dashboard.models import SiteSettings
        cfg = SiteSettings.load()
        try:
            discount_percent = float(request.POST.get("discount_percent") or 0)
        except ValueError:
            discount_percent = 0.0
        try:
            tax_rate = float(request.POST.get("tax_rate") or 0)
        except ValueError:
            tax_rate = 0.0
        max_discount = float(cfg.max_discount_percent)
        if max_discount > 0 and discount_percent > max_discount:
            messages.error(request, f"Discount cannot exceed {max_discount}% (configured in Settings).")
            return render(request, "proposals/quote_form.html", {
                "quote": quote, "leads": leads, "clients": clients,
                "status_choices": Quote.STATUS_CHOICES, "title": f"Edit Quotation {quote.quote_number}",
                "editing": True,
            })
        quote.title = request.POST.get("title", "").strip()
        quote.valid_until = request.POST.get("valid_until", "")
        quote.status = request.POST.get("status", "draft")
        quote.notes = request.POST.get("notes", "").strip()
        quote.terms = request.POST.get("terms", "").strip()
        quote.discount_percent = discount_percent
        quote.tax_rate = tax_rate
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
        messages.success(request, "Quotation updated.")
        return redirect("proposals:quote_detail", pk=quote.pk)
    return render(request, "proposals/quote_form.html", {
        "quote": quote,
        "leads": leads,
        "clients": clients,
        "status_choices": Quote.STATUS_CHOICES,
        "title": f"Edit Quotation {quote.quote_number}",
        "editing": True,
    })


@requires_feature('has_proposals')
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


@requires_feature('has_proposals')
def quote_print(request, pk):
    quote = get_object_or_404(Quote, pk=pk)
    from dashboard.models import SiteSettings
    cfg = SiteSettings.load()
    return render(request, "proposals/quote_print.html", {"quote": quote, "cfg": cfg})
