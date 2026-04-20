from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from leads.models import Lead, Activity
from clients.models import Contract
from billing.models import Invoice


@login_required
def dashboard(request):
    today = timezone.now().date()
    in_30_days = today + timezone.timedelta(days=30)

    # Today's and overdue follow-ups
    todays_followups = Activity.objects.filter(
        next_follow_up_date=today
    ).select_related("lead", "created_by")

    overdue_followups = Activity.objects.filter(
        next_follow_up_date__lt=today,
        lead__status__in=["new", "contacted", "demo", "negotiation"]
    ).select_related("lead").order_by("next_follow_up_date")

    # Contracts expiring in 30 days
    expiring_contracts = Contract.objects.filter(
        status="active",
        end_date__gte=today,
        end_date__lte=in_30_days
    ).select_related("client").order_by("end_date")

    # Pending/overdue invoices
    pending_invoices = Invoice.objects.filter(
        status__in=["pending", "overdue"]
    ).select_related("client").order_by("due_date")

    # Revenue summary
    paid_this_month = Invoice.objects.filter(
        status="paid",
        generated_date__year=today.year,
        generated_date__month=today.month,
    )
    from django.db.models import Sum
    revenue_month = paid_this_month.aggregate(t=Sum("amount"))["t"] or 0

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
        "expiring_contracts": expiring_contracts,
        "pending_invoices": pending_invoices,
        "revenue_month": revenue_month,
        "lead_stats": lead_stats,
    })
