import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.contrib.auth import get_user_model
from leads.models import Lead, Activity
from clients.models import Client, Contract, ClientInteraction
from billing.models import Invoice

User = get_user_model()


@login_required
def dashboard(request):
    today = timezone.now().date()
    in_30_days = today + timezone.timedelta(days=30)

    todays_followups = Activity.objects.filter(
        next_follow_up_date=today,
        status__in=["pending", "rescheduled"],
    ).select_related("lead", "created_by")

    overdue_followups = Activity.objects.filter(
        next_follow_up_date__lt=today,
        next_follow_up_date__isnull=False,
        status__in=["pending", "rescheduled"],
    ).select_related("lead").order_by("next_follow_up_date")

    # Client interaction follow-ups
    client_followups_today = ClientInteraction.objects.filter(
        next_follow_up_date=today,
        follow_up_done=False,
    ).select_related("client", "created_by")

    client_followups_overdue = ClientInteraction.objects.filter(
        next_follow_up_date__lt=today,
        next_follow_up_date__isnull=False,
        follow_up_done=False,
    ).select_related("client").order_by("next_follow_up_date")

    expiring_contracts = Contract.objects.filter(
        status="active",
        end_date__gte=today,
        end_date__lte=in_30_days,
    ).select_related("client").order_by("end_date")

    pending_invoices = Invoice.objects.filter(
        status__in=["pending", "overdue"]
    ).select_related("client").order_by("due_date")

    revenue_month = Invoice.objects.filter(
        status="paid",
        generated_date__year=today.year,
        generated_date__month=today.month,
    ).aggregate(t=Sum("amount"))["t"] or 0

    lead_stats = {
        "total": Lead.objects.count(),
        "new": Lead.objects.filter(status="new").count(),
        "won": Lead.objects.filter(status="won").count(),
        "lost": Lead.objects.filter(status="lost").count(),
    }

    return render(request, "dashboard/dashboard.html", {
        "today": today,
        "todays_followups": todays_followups,
        "overdue_followups": overdue_followups,
        "client_followups_today": client_followups_today,
        "client_followups_overdue": client_followups_overdue,
        "expiring_contracts": expiring_contracts,
        "pending_invoices": pending_invoices,
        "revenue_month": revenue_month,
        "lead_stats": lead_stats,
    })


@login_required
def reports(request):
    today = timezone.now().date()
    twelve_months_ago = today.replace(day=1) - timezone.timedelta(days=365)

    # Revenue by month (last 12 months)
    revenue_qs = (
        Invoice.objects
        .filter(status="paid", generated_date__gte=twelve_months_ago)
        .annotate(month=TruncMonth("generated_date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )
    revenue_labels = [r["month"].strftime("%b %Y") for r in revenue_qs]
    revenue_data = [float(r["total"]) for r in revenue_qs]

    # Lead pipeline counts
    status_order = ["new", "contacted", "demo", "negotiation", "won", "lost"]
    lead_status_map = dict(Lead.STATUS_CHOICES)
    lead_pipeline = Lead.objects.values("status").annotate(count=Count("id"))
    pipeline_counts = {row["status"]: row["count"] for row in lead_pipeline}
    pipeline_labels = [lead_status_map[s] for s in status_order]
    pipeline_data = [pipeline_counts.get(s, 0) for s in status_order]

    # Lead source breakdown
    source_qs = Lead.objects.exclude(source="").values("source").annotate(count=Count("id"))
    source_map = dict(Lead.SOURCE_CHOICES)
    source_labels = [source_map.get(r["source"], r["source"]) for r in source_qs]
    source_data = [r["count"] for r in source_qs]

    # Client health distribution
    client_status_qs = Client.objects.values("status").annotate(count=Count("id"))
    client_status_map = dict(Client.STATUS_CHOICES)
    client_labels = [client_status_map.get(r["status"], r["status"]) for r in client_status_qs]
    client_data = [r["count"] for r in client_status_qs]

    # Key metrics
    total_revenue = Invoice.objects.filter(status="paid").aggregate(t=Sum("amount"))["t"] or 0
    total_outstanding = Invoice.objects.filter(status__in=["pending", "overdue"]).aggregate(t=Sum("amount"))["t"] or 0
    conversion_rate = 0
    total_leads = Lead.objects.count()
    won_leads = Lead.objects.filter(status="won").count()
    if total_leads:
        conversion_rate = round(won_leads / total_leads * 100, 1)

    return render(request, "dashboard/reports.html", {
        "revenue_labels": json.dumps(revenue_labels),
        "revenue_data": json.dumps(revenue_data),
        "pipeline_labels": json.dumps(pipeline_labels),
        "pipeline_data": json.dumps(pipeline_data),
        "source_labels": json.dumps(source_labels),
        "source_data": json.dumps(source_data),
        "client_labels": json.dumps(client_labels),
        "client_data": json.dumps(client_data),
        "total_revenue": total_revenue,
        "total_outstanding": total_outstanding,
        "total_leads": total_leads,
        "won_leads": won_leads,
        "conversion_rate": conversion_rate,
        "total_clients": Client.objects.count(),
        "active_clients": Client.objects.filter(status="active").count(),
    })


@login_required
def search(request):
    q = request.GET.get("q", "").strip()
    leads = clients = invoices = []
    if q:
        leads = Lead.objects.filter(
            Q(organization_name__icontains=q) |
            Q(contact_person__icontains=q) |
            Q(phone__icontains=q) |
            Q(email__icontains=q)
        ).order_by("-created_at")[:15]
        clients = Client.objects.filter(
            Q(organization_name__icontains=q) |
            Q(email__icontains=q) |
            Q(phone__icontains=q) |
            Q(industry__icontains=q)
        ).order_by("organization_name")[:15]
        invoices = Invoice.objects.filter(
            Q(invoice_number__icontains=q) |
            Q(client__organization_name__icontains=q)
        ).select_related("client").order_by("-generated_date")[:15]
    return render(request, "dashboard/search.html", {
        "q": q,
        "leads": leads,
        "clients": clients,
        "invoices": invoices,
    })


@login_required
def team_performance(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)

    users = User.objects.filter(is_active=True).order_by("first_name", "username")
    stats = []
    for user in users:
        leads_assigned = Lead.objects.filter(assigned_to=user).count()
        leads_won = Lead.objects.filter(assigned_to=user, status="won").count()
        conversion = round(leads_won / leads_assigned * 100) if leads_assigned else 0
        activities_this_month = Activity.objects.filter(
            assigned_to=user, created_at__date__gte=month_start
        ).count()
        interactions_this_month = ClientInteraction.objects.filter(
            created_by=user, created_at__date__gte=month_start
        ).count()
        revenue = (
            Invoice.objects
            .filter(client__in=Lead.objects.filter(assigned_to=user, status="won").values("linked_client"))
            .aggregate(total=Sum("total_amount"))["total"] or 0
        )
        stats.append({
            "user": user,
            "leads_assigned": leads_assigned,
            "leads_won": leads_won,
            "conversion": conversion,
            "activities_this_month": activities_this_month,
            "interactions_this_month": interactions_this_month,
            "revenue": revenue,
        })
    # Sort by won leads descending
    stats.sort(key=lambda x: x["leads_won"], reverse=True)
    return render(request, "dashboard/team_performance.html", {
        "stats": stats,
        "month": month_start.strftime("%B %Y"),
    })
