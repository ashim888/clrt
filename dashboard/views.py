import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import models as _db_models
from django.db.models import Sum, Count, Q, Avg
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
    now_local = timezone.localtime(timezone.now())
    in_30_days = today + timezone.timedelta(days=30)
    month_start = today.replace(day=1)
    last_month_end = month_start - timezone.timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    # ── Greeting ────────────────────────────────────────────────
    hour = now_local.hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    # ── Follow-ups ───────────────────────────────────────────────
    todays_followups = Activity.objects.filter(
        next_follow_up_date=today,
        status__in=["pending", "rescheduled"],
    ).select_related("lead", "created_by")

    overdue_followups = Activity.objects.filter(
        next_follow_up_date__lt=today,
        next_follow_up_date__isnull=False,
        status__in=["pending", "rescheduled"],
    ).select_related("lead").order_by("next_follow_up_date")

    client_followups_today = ClientInteraction.objects.filter(
        next_follow_up_date=today,
        follow_up_done=False,
    ).select_related("client", "created_by")

    client_followups_overdue = ClientInteraction.objects.filter(
        next_follow_up_date__lt=today,
        next_follow_up_date__isnull=False,
        follow_up_done=False,
    ).select_related("client").order_by("next_follow_up_date")

    # ── Today's merged agenda ────────────────────────────────────
    agenda_today = []
    for a in todays_followups:
        agenda_today.append({
            "kind": "lead", "pk": a.pk,
            "name": a.lead.organization_name,
            "url": f"/leads/{a.lead.pk}/",
            "sub": a.get_type_display(),
            "notes": a.notes,
        })
    for c in client_followups_today:
        agenda_today.append({
            "kind": "client", "pk": c.pk,
            "name": c.client.organization_name,
            "url": f"/clients/{c.client.pk}/",
            "sub": c.get_type_display(),
            "notes": c.notes,
        })

    # ── Contracts & Invoices ─────────────────────────────────────
    expiring_contracts = Contract.objects.filter(
        status="active",
        end_date__gte=today,
        end_date__lte=in_30_days,
    ).select_related("client").order_by("end_date")

    pending_invoices = Invoice.objects.filter(
        status__in=["pending", "overdue"]
    ).select_related("client").order_by("due_date")

    pending_invoice_total = pending_invoices.aggregate(t=Sum("amount"))["t"] or 0

    # ── Revenue ──────────────────────────────────────────────────
    revenue_month = Invoice.objects.filter(
        status="paid",
        generated_date__year=today.year,
        generated_date__month=today.month,
    ).aggregate(t=Sum("amount"))["t"] or 0

    revenue_last_month = Invoice.objects.filter(
        status="paid",
        generated_date__year=last_month_start.year,
        generated_date__month=last_month_start.month,
    ).aggregate(t=Sum("amount"))["t"] or 0

    def _trend(cur, prev):
        try:
            cur, prev = float(cur or 0), float(prev or 0)
            if prev == 0:
                return None
            return int((cur - prev) / prev * 100)
        except Exception:
            return None

    revenue_trend = _trend(revenue_month, revenue_last_month)

    # ── Won this month ───────────────────────────────────────────
    won_qs = Lead.objects.filter(
        status="won",
        updated_at__year=today.year,
        updated_at__month=today.month,
    ).aggregate(count=Count("id"), value=Sum("deal_value"))
    won_this_month = {"count": won_qs["count"] or 0, "value": won_qs["value"] or 0}

    won_last = Lead.objects.filter(
        status="won",
        updated_at__year=last_month_start.year,
        updated_at__month=last_month_start.month,
    ).aggregate(value=Sum("deal_value"))["value"] or 0
    won_trend = _trend(won_this_month["value"], won_last)

    # ── Pipeline by stage ────────────────────────────────────────
    OPEN_STAGES = [
        ("new", "New"), ("contacted", "Contacted"),
        ("demo", "Demo"), ("negotiation", "Negotiation"),
    ]
    STAGE_COLORS = {
        "new": "#3b82f6", "contacted": "#6366f1",
        "demo": "#8b5cf6", "negotiation": "#f59e0b",
    }
    stage_agg = {
        s["status"]: s
        for s in Lead.objects.filter(
            status__in=[k for k, _ in OPEN_STAGES]
        ).values("status").annotate(count=Count("id"), value=Sum("deal_value"))
    }
    pipeline_total = sum(float(v.get("value") or 0) for v in stage_agg.values())
    max_val = max((float(v.get("value") or 0) for v in stage_agg.values()), default=1) or 1
    pipeline_by_stage = []
    for key, label in OPEN_STAGES:
        d = stage_agg.get(key, {})
        val = float(d.get("value") or 0)
        pipeline_by_stage.append({
            "key": key, "label": label,
            "count": d.get("count", 0),
            "value": val,
            "pct": int(val / max_val * 100),
            "color": STAGE_COLORS[key],
        })

    # ── Urgent count ─────────────────────────────────────────────
    urgent_count = (
        overdue_followups.count()
        + client_followups_overdue.count()
        + Invoice.objects.filter(status="overdue").count()
    )

    # ── Active clients ───────────────────────────────────────────
    active_clients = Client.objects.filter(status="active").count()

    # ── Recent activity feed ─────────────────────────────────────
    recent_activities = Activity.objects.select_related(
        "lead", "created_by"
    ).order_by("-created_at")[:8]

    # ── Monthly goal ─────────────────────────────────────────────
    from .models import UserGoal
    my_goal = None
    try:
        goal_obj = UserGoal.objects.get(user=request.user, month=month_start)
        achieved = Lead.objects.filter(
            status="won",
            updated_at__year=today.year,
            updated_at__month=today.month,
            assigned_to=request.user,
        ).aggregate(t=Sum("deal_value"))["t"] or 0
        pct = min(int(float(achieved) / float(goal_obj.target) * 100), 100) if goal_obj.target else 0
        my_goal = {"target": goal_obj.target, "achieved": achieved, "pct": pct}
    except UserGoal.DoesNotExist:
        pass

    return render(request, "dashboard/dashboard.html", {
        "today": today,
        "greeting": greeting,
        # follow-ups (kept for modal JS)
        "todays_followups": todays_followups,
        "overdue_followups": overdue_followups,
        "client_followups_today": client_followups_today,
        "client_followups_overdue": client_followups_overdue,
        # agenda
        "agenda_today": agenda_today,
        # alerts
        "expiring_contracts": expiring_contracts,
        "pending_invoices": pending_invoices,
        "pending_invoice_total": pending_invoice_total,
        # KPIs
        "revenue_month": revenue_month,
        "revenue_trend": revenue_trend,
        "won_this_month": won_this_month,
        "won_trend": won_trend,
        "pipeline_by_stage": pipeline_by_stage,
        "pipeline_total": pipeline_total,
        "urgent_count": urgent_count,
        "active_clients": active_clients,
        # feed
        "recent_activities": recent_activities,
        # goal
        "my_goal": my_goal,
    })


@login_required
def reports(request):
    from datetime import date as _date
    today = timezone.now().date()

    # Date range filter
    date_from_str = request.GET.get("date_from", "")
    date_to_str = request.GET.get("date_to", "")
    try:
        date_from = _date.fromisoformat(date_from_str) if date_from_str else None
    except ValueError:
        date_from = None
    try:
        date_to = _date.fromisoformat(date_to_str) if date_to_str else None
    except ValueError:
        date_to = None

    twelve_months_ago = today.replace(day=1) - timezone.timedelta(days=365)

    # Revenue by month
    rev_qs = Invoice.objects.filter(status="paid")
    if date_from:
        rev_qs = rev_qs.filter(generated_date__gte=date_from)
    elif not date_from and not date_to:
        rev_qs = rev_qs.filter(generated_date__gte=twelve_months_ago)
    if date_to:
        rev_qs = rev_qs.filter(generated_date__lte=date_to)
    revenue_qs = (
        rev_qs
        .annotate(month=TruncMonth("generated_date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")
    )
    revenue_labels = [r["month"].strftime("%b %Y") for r in revenue_qs]
    revenue_data = [float(r["total"]) for r in revenue_qs]

    # Lead pipeline counts (date-filtered if range supplied)
    lead_qs = Lead.objects
    if date_from:
        lead_qs = lead_qs.filter(created_at__date__gte=date_from)
    if date_to:
        lead_qs = lead_qs.filter(created_at__date__lte=date_to)

    status_order = ["new", "contacted", "demo", "negotiation", "won", "lost"]
    lead_status_map = dict(Lead.STATUS_CHOICES)
    lead_pipeline = lead_qs.values("status").annotate(count=Count("id"))
    pipeline_counts = {row["status"]: row["count"] for row in lead_pipeline}
    pipeline_labels = [lead_status_map[s] for s in status_order]
    pipeline_data = [pipeline_counts.get(s, 0) for s in status_order]

    # Lead source breakdown
    source_qs = lead_qs.exclude(source="").values("source").annotate(count=Count("id"))
    source_map = dict(Lead.SOURCE_CHOICES)
    source_labels = [source_map.get(r["source"], r["source"]) for r in source_qs]
    source_data = [r["count"] for r in source_qs]

    # Client health distribution (not date-filtered — always all-time)
    client_status_qs = Client.objects.values("status").annotate(count=Count("id"))
    client_status_map = dict(Client.STATUS_CHOICES)
    client_labels = [client_status_map.get(r["status"], r["status"]) for r in client_status_qs]
    client_data = [r["count"] for r in client_status_qs]

    # Key metrics
    inv_base = Invoice.objects
    if date_from:
        inv_base = inv_base.filter(generated_date__gte=date_from)
    if date_to:
        inv_base = inv_base.filter(generated_date__lte=date_to)
    total_revenue = inv_base.filter(status="paid").aggregate(t=Sum("amount"))["t"] or 0
    total_outstanding = Invoice.objects.filter(status__in=["pending", "overdue"]).aggregate(t=Sum("amount"))["t"] or 0

    total_leads = lead_qs.count()
    won_leads = lead_qs.filter(status="won").count()
    conversion_rate = round(won_leads / total_leads * 100, 1) if total_leads else 0

    # Pipeline value metrics (always all-time for forecast accuracy)
    STAGE_PROB = {"new": 10, "contacted": 25, "demo": 50, "negotiation": 75, "won": 100, "lost": 0}
    active_stages = ["new", "contacted", "demo", "negotiation"]
    pipeline_value_qs = (
        Lead.objects
        .filter(status__in=active_stages, deal_value__isnull=False)
        .values("status")
        .annotate(total=Sum("deal_value"))
    )
    pipeline_value_map = {row["status"]: float(row["total"]) for row in pipeline_value_qs}
    active_pipeline_value = sum(pipeline_value_map.values())
    weighted_forecast = sum(pipeline_value_map.get(s, 0) * STAGE_PROB[s] / 100 for s in active_stages)
    won_pipeline_value = Lead.objects.filter(status="won", deal_value__isnull=False).aggregate(t=Sum("deal_value"))["t"] or 0

    pv_labels = [lead_status_map[s] for s in status_order]
    pv_data = [pipeline_value_map.get(s, 0) for s in status_order]
    pv_data[status_order.index("won")] = float(won_pipeline_value)

    # Lost reason breakdown
    lost_qs = lead_qs.filter(status="lost")
    lost_reasons = list(
        lost_qs.exclude(lost_reason="")
        .values("lost_reason").annotate(count=Count("id"))
        .order_by("-count")[:10]
    )
    lost_total = lost_qs.count()
    lost_no_reason = lost_qs.filter(lost_reason="").count()

    # Conversion funnel
    funnel_stages = ["new", "contacted", "demo", "negotiation", "won"]
    funnel_colors = ["#93c5fd", "#a5b4fc", "#c4b5fd", "#fbbf24", "#34d399"]
    funnel_counts = [pipeline_counts.get(s, 0) for s in funnel_stages]
    funnel_labels = [lead_status_map[s] for s in funnel_stages]
    funnel_max = max(funnel_counts) if funnel_counts else 1
    funnel_display = []
    for i, (stage, count, color) in enumerate(zip(funnel_stages, funnel_counts, funnel_colors)):
        prev_count = funnel_counts[i - 1] if i > 0 else None
        dropped = round((prev_count - count) / prev_count * 100) if prev_count and count < prev_count else 0
        funnel_display.append({
            "label": lead_status_map[stage],
            "count": count,
            "pct": round(count / funnel_max * 100) if funnel_max else 0,
            "color": color,
            "prev_count": prev_count,
            "dropped": dropped,
        })

    return render(request, "dashboard/reports.html", {
        "revenue_labels": json.dumps(revenue_labels),
        "revenue_data": json.dumps(revenue_data),
        "pipeline_labels": json.dumps(pipeline_labels),
        "pipeline_data": json.dumps(pipeline_data),
        "pv_labels": json.dumps(pv_labels),
        "pv_data": json.dumps(pv_data),
        "source_labels": json.dumps(source_labels),
        "source_data": json.dumps(source_data),
        "client_labels": json.dumps(client_labels),
        "client_data": json.dumps(client_data),
        "funnel_labels": json.dumps(funnel_labels),
        "funnel_data": json.dumps(funnel_counts),
        "funnel_labels_display": funnel_display,
        "total_revenue": total_revenue,
        "total_outstanding": total_outstanding,
        "total_leads": total_leads,
        "won_leads": won_leads,
        "conversion_rate": conversion_rate,
        "total_clients": Client.objects.count(),
        "active_clients": Client.objects.filter(status="active").count(),
        "active_pipeline_value": active_pipeline_value,
        "weighted_forecast": weighted_forecast,
        "won_pipeline_value": won_pipeline_value,
        "lost_reasons": lost_reasons,
        "lost_total": lost_total,
        "lost_no_reason": lost_no_reason,
        "date_from": date_from_str,
        "date_to": date_to_str,
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

    from .models import UserGoal
    goals = {g.user_id: g for g in UserGoal.objects.filter(month=month_start)}

    users = User.objects.filter(is_active=True).order_by("first_name", "username")
    stats = []
    for user in users:
        leads_assigned = Lead.objects.filter(assigned_to=user).count()
        leads_won = Lead.objects.filter(assigned_to=user, status="won").count()
        conversion = round(leads_won / leads_assigned * 100) if leads_assigned else 0
        activities_this_month = Activity.objects.filter(
            created_by=user, created_at__date__gte=month_start
        ).count()
        interactions_this_month = ClientInteraction.objects.filter(
            created_by=user, created_at__date__gte=month_start
        ).count()
        deal_value_won = (
            Lead.objects
            .filter(assigned_to=user, status="won", deal_value__isnull=False)
            .aggregate(t=Sum("deal_value"))["t"] or 0
        )
        revenue = (
            Invoice.objects
            .filter(client__linked_lead__assigned_to=user, status="paid")
            .aggregate(total=Sum("amount"))["total"] or 0
        )
        goal = goals.get(user.pk)
        quota_pct = (
            min(int(float(deal_value_won) / float(goal.target) * 100), 100)
            if goal and goal.target else None
        )
        stats.append({
            "user": user,
            "leads_assigned": leads_assigned,
            "leads_won": leads_won,
            "conversion": conversion,
            "activities_this_month": activities_this_month,
            "interactions_this_month": interactions_this_month,
            "deal_value_won": deal_value_won,
            "revenue": revenue,
            "quota_target": goal.target if goal else None,
            "quota_pct": quota_pct,
        })
    stats.sort(key=lambda x: x["leads_won"], reverse=True)
    return render(request, "dashboard/team_performance.html", {
        "stats": stats,
        "month": month_start.strftime("%B %Y"),
    })


@login_required
def report_leads(request):
    from datetime import date as _date
    today = timezone.now().date()
    date_from_str = request.GET.get("date_from", "")
    date_to_str = request.GET.get("date_to", "")
    try:
        date_from = _date.fromisoformat(date_from_str) if date_from_str else None
    except ValueError:
        date_from = None
    try:
        date_to = _date.fromisoformat(date_to_str) if date_to_str else None
    except ValueError:
        date_to = None

    qs = Lead.objects
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    # Stage breakdown
    STATUS_ORDER = ["new", "contacted", "demo", "negotiation", "won", "lost"]
    status_map = dict(Lead.STATUS_CHOICES)
    STAGE_PROB = {"new": 10, "contacted": 25, "demo": 50, "negotiation": 75, "won": 100, "lost": 0}
    stage_rows = []
    for s in STATUS_ORDER:
        stage_qs = qs.filter(status=s)
        count = stage_qs.count()
        dv = stage_qs.filter(deal_value__isnull=False).aggregate(
            total=Sum("deal_value"), avg=Avg("deal_value")
        )
        stage_rows.append({
            "status": s, "label": status_map[s], "count": count,
            "total_value": dv["total"] or 0,
            "avg_value": dv["avg"] or 0,
            "prob": STAGE_PROB[s],
        })
    total_leads = qs.count()
    won_count = qs.filter(status="won").count()
    lost_count = qs.filter(status="lost").count()
    active_count = qs.exclude(status__in=["won", "lost"]).count()
    conversion_rate = round(won_count / total_leads * 100, 1) if total_leads else 0

    # Source breakdown
    source_map = dict(Lead.SOURCE_CHOICES)
    source_rows = []
    for src, label in Lead.SOURCE_CHOICES:
        src_qs = qs.filter(source=src)
        count = src_qs.count()
        if not count:
            continue
        won = src_qs.filter(status="won").count()
        source_rows.append({
            "source": src, "label": label, "count": count,
            "won": won, "rate": round(won / count * 100) if count else 0,
        })
    source_rows.sort(key=lambda x: x["count"], reverse=True)

    # Assigned-to breakdown
    assigned_rows = []
    for user in User.objects.filter(is_active=True).order_by("first_name"):
        u_qs = qs.filter(assigned_to=user)
        count = u_qs.count()
        if not count:
            continue
        won = u_qs.filter(status="won").count()
        pipeline = u_qs.filter(status__in=["new","contacted","demo","negotiation"],
                               deal_value__isnull=False).aggregate(t=Sum("deal_value"))["t"] or 0
        won_val = u_qs.filter(status="won", deal_value__isnull=False).aggregate(t=Sum("deal_value"))["t"] or 0
        assigned_rows.append({
            "user": user, "count": count, "won": won,
            "rate": round(won / count * 100) if count else 0,
            "pipeline": pipeline, "won_value": won_val,
        })
    assigned_rows.sort(key=lambda x: x["count"], reverse=True)

    # Lost reasons
    lost_reasons = list(
        qs.filter(status="lost").exclude(lost_reason="")
        .values("lost_reason").annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    return render(request, "dashboard/report_leads.html", {
        "stage_rows": stage_rows,
        "source_rows": source_rows,
        "assigned_rows": assigned_rows,
        "lost_reasons": lost_reasons,
        "total_leads": total_leads,
        "won_count": won_count,
        "lost_count": lost_count,
        "active_count": active_count,
        "conversion_rate": conversion_rate,
        "date_from": date_from_str,
        "date_to": date_to_str,
        "today": today,
    })


@login_required
def report_clients(request):
    today = timezone.now().date()

    # Status summary
    status_map = dict(Client.STATUS_CHOICES)
    total_clients = Client.objects.count()
    status_counts = {
        r["status"]: r["count"]
        for r in Client.objects.values("status").annotate(count=Count("id"))
    }

    # Industry breakdown
    industry_rows = list(
        Client.objects.exclude(industry="")
        .values("industry").annotate(count=Count("id"))
        .order_by("-count")[:12]
    )

    # Top clients by revenue
    from billing.models import Invoice as _Inv
    top_clients = list(
        _Inv.objects.values("client", "client__organization_name")
        .annotate(
            total_billed=Sum("amount"),
            total_paid=Sum("amount", filter=Q(status="paid")),
            total_outstanding=Sum("amount", filter=Q(status__in=["pending","overdue"])),
        )
        .order_by("-total_billed")[:10]
    )

    # Contract expiry
    from clients.models import Contract
    expiring_30 = Contract.objects.filter(status="active", end_date__gte=today,
        end_date__lte=today + timezone.timedelta(days=30)).select_related("client").order_by("end_date")
    expiring_60 = Contract.objects.filter(status="active", end_date__gt=today + timezone.timedelta(days=30),
        end_date__lte=today + timezone.timedelta(days=60)).select_related("client").order_by("end_date")
    expiring_90 = Contract.objects.filter(status="active", end_date__gt=today + timezone.timedelta(days=60),
        end_date__lte=today + timezone.timedelta(days=90)).select_related("client").order_by("end_date")

    # New clients per month (last 6 months)
    six_months_ago = (today.replace(day=1) - timezone.timedelta(days=1)).replace(day=1)
    six_months_ago = six_months_ago.replace(month=max(1, six_months_ago.month - 4))
    new_by_month = list(
        Client.objects.filter(created_at__date__gte=six_months_ago)
        .annotate(month=TruncMonth("created_at"))
        .values("month").annotate(count=Count("id"))
        .order_by("month")
    )

    return render(request, "dashboard/report_clients.html", {
        "total_clients": total_clients,
        "status_counts": status_counts,
        "status_map": status_map,
        "industry_rows": industry_rows,
        "top_clients": top_clients,
        "expiring_30": expiring_30,
        "expiring_60": expiring_60,
        "expiring_90": expiring_90,
        "new_by_month": new_by_month,
        "today": today,
    })


@login_required
def report_billing(request):
    today = timezone.now().date()
    month_start = today.replace(day=1)
    twelve_months_ago = (today.replace(day=1) - timezone.timedelta(days=365))

    from billing.models import Invoice as _Inv, Payment as _Pay

    # Summary
    total_collected = _Inv.objects.filter(status="paid").aggregate(t=Sum("amount"))["t"] or 0
    this_month = _Inv.objects.filter(
        status="paid", generated_date__gte=month_start
    ).aggregate(t=Sum("amount"))["t"] or 0
    outstanding = _Inv.objects.filter(status__in=["pending","overdue"]).aggregate(t=Sum("amount"))["t"] or 0
    overdue_amt = _Inv.objects.filter(status="overdue").aggregate(t=Sum("amount"))["t"] or 0
    overdue_count = _Inv.objects.filter(status="overdue").count()

    # Status breakdown
    status_rows = list(
        _Inv.objects.values("status").annotate(count=Count("id"), total=Sum("amount"))
        .order_by("-total")
    )
    inv_status_map = dict(_Inv.STATUS_CHOICES)
    for r in status_rows:
        r["label"] = inv_status_map.get(r["status"], r["status"])

    # Top debtors
    top_debtors = list(
        _Inv.objects.filter(status__in=["pending","overdue"])
        .values("client", "client__organization_name")
        .annotate(owed=Sum("amount"))
        .order_by("-owed")[:10]
    )

    # Payment mode breakdown
    mode_rows = list(
        _Pay.objects.values("payment_mode")
        .annotate(count=Count("id"), total=Sum("amount_paid"))
        .order_by("-total")
    )
    mode_map = dict(_Pay.MODE_CHOICES)
    for r in mode_rows:
        r["label"] = mode_map.get(r["payment_mode"], r["payment_mode"])

    # Monthly revenue trend (last 12 months)
    monthly = list(
        _Inv.objects.filter(status="paid", generated_date__gte=twelve_months_ago)
        .annotate(month=TruncMonth("generated_date"))
        .values("month").annotate(total=Sum("amount"))
        .order_by("month")
    )

    return render(request, "dashboard/report_billing.html", {
        "total_collected": total_collected,
        "this_month": this_month,
        "outstanding": outstanding,
        "overdue_amt": overdue_amt,
        "overdue_count": overdue_count,
        "status_rows": status_rows,
        "top_debtors": top_debtors,
        "mode_rows": mode_rows,
        "monthly": monthly,
        "today": today,
    })


@login_required
def site_settings_view(request):
    if not (request.user.is_superuser or getattr(request.user, 'role', '') == 'admin'):
        messages.error(request, "Only admins can change system settings.")
        return redirect("dashboard:dashboard")
    from .models import SiteSettings
    from .forms import SiteSettingsForm
    obj = SiteSettings.load()
    if request.method == "POST":
        form = SiteSettingsForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Settings saved.")
            return redirect("dashboard:settings")
    else:
        form = SiteSettingsForm(instance=obj)
    return render(request, "dashboard/settings.html", {"form": form, "obj": obj})


# ── Notifications ────────────────────────────────────────────────

@login_required
def notification_read(request, pk):
    from .models import Notification
    notif = Notification.objects.filter(pk=pk, user=request.user).first()
    if notif:
        notif.is_read = True
        notif.save(update_fields=["is_read"])
        if notif.link:
            return redirect(notif.link)
    return redirect("dashboard:dashboard")


@login_required
def notifications_read_all(request):
    from .models import Notification
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect(request.META.get("HTTP_REFERER", "dashboard:dashboard"))


@login_required
def notification_list(request):
    from .models import Notification
    notifs = Notification.objects.filter(user=request.user)
    return render(request, "dashboard/notifications.html", {"notifs": notifs})


# ── Audit Trail ──────────────────────────────────────────────────

@login_required
def audit_trail(request):
    if not (request.user.is_superuser or getattr(request.user, 'role', '') == 'admin'):
        messages.error(request, "Access restricted to admins.")
        return redirect("dashboard:dashboard")
    from .models import AuditLog
    logs = AuditLog.objects.select_related("user").all()
    model = request.GET.get("model", "")
    action = request.GET.get("action", "")
    if model:
        logs = logs.filter(model_name=model)
    if action:
        logs = logs.filter(action=action)
    from django.core.paginator import Paginator
    page_obj = Paginator(logs, 50).get_page(request.GET.get("page"))
    return render(request, "dashboard/audit_trail.html", {
        "page_obj": page_obj,
        "logs": page_obj,
        "model": model,
        "action_filter": action,
        "model_choices": ["Lead", "Client"],
        "action_choices": AuditLog.ACTION_CHOICES,
    })


# ── Calendar ──────────────────────────────────────────────────────

@login_required
def calendar_view(request):
    from .models import CalendarEvent
    return render(request, "dashboard/calendar.html", {
        "color_choices": CalendarEvent.COLOR_CHOICES,
    })


@login_required
def calendar_events(request):
    from django.http import JsonResponse as _JR
    start = request.GET.get("start", "")
    end = request.GET.get("end", "")
    events = []

    from leads.models import Activity
    from clients.models import ClientInteraction
    import datetime

    act_qs = Activity.objects.filter(next_follow_up_date__isnull=False).select_related("lead")
    if start:
        act_qs = act_qs.filter(next_follow_up_date__gte=start[:10])
    if end:
        act_qs = act_qs.filter(next_follow_up_date__lte=end[:10])
    for a in act_qs:
        events.append({
            "id": f"lead-act-{a.pk}",
            "title": f"{a.lead.organization_name} — {a.get_type_display()}",
            "start": str(a.next_follow_up_date),
            "url": f"/leads/{a.lead_id}/",
            "color": "#3b82f6",
            "extendedProps": {"type": "Lead Follow-up", "status": a.status},
        })

    ci_qs = ClientInteraction.objects.filter(next_follow_up_date__isnull=False, follow_up_done=False).select_related("client")
    if start:
        ci_qs = ci_qs.filter(next_follow_up_date__gte=start[:10])
    if end:
        ci_qs = ci_qs.filter(next_follow_up_date__lte=end[:10])
    for ci in ci_qs:
        events.append({
            "id": f"client-ci-{ci.pk}",
            "title": f"{ci.client.organization_name} — {ci.get_type_display()}",
            "start": str(ci.next_follow_up_date),
            "url": f"/clients/{ci.client_id}/",
            "color": "#10b981",
            "extendedProps": {"type": "Client Follow-up"},
        })

    from billing.models import Invoice
    inv_qs = Invoice.objects.filter(status__in=["pending", "overdue"]).select_related("client")
    if start:
        inv_qs = inv_qs.filter(due_date__gte=start[:10])
    if end:
        inv_qs = inv_qs.filter(due_date__lte=end[:10])
    for inv in inv_qs:
        events.append({
            "id": f"inv-{inv.pk}",
            "title": f"Invoice due: {inv.client.organization_name}",
            "start": str(inv.due_date),
            "url": f"/billing/{inv.pk}/",
            "color": "#f59e0b" if inv.status == "pending" else "#ef4444",
            "extendedProps": {"type": "Invoice Due", "status": inv.status},
        })

    from clients.models import Contract
    con_qs = Contract.objects.filter(status="active").select_related("client")
    if start:
        con_qs = con_qs.filter(end_date__gte=start[:10])
    if end:
        con_qs = con_qs.filter(end_date__lte=end[:10])
    for con in con_qs:
        events.append({
            "id": f"con-{con.pk}",
            "title": f"Contract ends: {con.client.organization_name}",
            "start": str(con.end_date),
            "url": f"/clients/contracts/{con.pk}/",
            "color": "#8b5cf6",
            "extendedProps": {"type": "Contract Expiry"},
        })

    from .models import CalendarEvent
    from datetime import datetime as _dt2, time as _time2, date as _date2
    from django.utils import timezone as _tz2
    ce_qs = CalendarEvent.objects.select_related('created_by')
    if start:
        start_aware = _tz2.make_aware(_dt2.combine(_date2.fromisoformat(start[:10]), _time2.min))
        ce_qs = ce_qs.filter(start__gte=start_aware)
    if end:
        end_aware = _tz2.make_aware(_dt2.combine(_date2.fromisoformat(end[:10]), _time2.max))
        ce_qs = ce_qs.filter(start__lte=end_aware)
    from django.utils import timezone as _tz_local
    for e in ce_qs:
        local_start = _tz_local.localtime(e.start)
        start_out = local_start.strftime('%Y-%m-%d') if e.all_day else local_start.isoformat()
        end_out = None
        if e.end:
            local_end = _tz_local.localtime(e.end)
            end_out = local_end.strftime('%Y-%m-%d') if e.all_day else local_end.isoformat()
        events.append({
            'id': f'custom-{e.pk}',
            'title': e.title,
            'start': start_out,
            'end': end_out,
            'allDay': e.all_day,
            'color': e.color,
            'extendedProps': {
                'type': 'custom',
                'pk': e.pk,
                'description': e.description,
                'created_by': str(e.created_by) if e.created_by else '',
            },
        })

    return _JR(events, safe=False)


@login_required
@require_POST
def calendar_event_save(request):
    from .models import CalendarEvent
    from datetime import datetime as _dt, time as _time
    from django.utils import timezone as _tz
    from django.utils.dateparse import parse_date
    from django.shortcuts import get_object_or_404
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    title = data.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'Title is required.'}, status=400)

    all_day = bool(data.get('all_day', True))
    start_str = data.get('start', '')
    end_str = data.get('end', '')
    color = data.get('color', '#6366f1')
    description = data.get('description', '')
    pk = data.get('pk')

    try:
        if all_day:
            d = parse_date(start_str[:10])
            start = _tz.make_aware(_dt.combine(d, _time.min))
            end = _tz.make_aware(_dt.combine(parse_date(end_str[:10]), _time.min)) if end_str else None
        else:
            naive_start = _dt.fromisoformat(start_str)
            start = _tz.make_aware(naive_start) if _tz.is_naive(naive_start) else naive_start
            if end_str:
                naive_end = _dt.fromisoformat(end_str)
                end = _tz.make_aware(naive_end) if _tz.is_naive(naive_end) else naive_end
            else:
                end = None
    except (ValueError, TypeError, AttributeError):
        return JsonResponse({'error': 'Invalid date/time.'}, status=400)

    if pk:
        event = get_object_or_404(CalendarEvent, pk=pk)
    else:
        event = CalendarEvent(created_by=request.user)

    event.title = title
    event.start = start
    event.end = end
    event.all_day = all_day
    event.color = color
    event.description = description
    event.save()
    return JsonResponse({'ok': True, 'pk': event.pk})


@login_required
@require_POST
def calendar_event_delete(request, pk):
    from .models import CalendarEvent
    from django.shortcuts import get_object_or_404
    event = get_object_or_404(CalendarEvent, pk=pk)
    event.delete()
    return JsonResponse({'ok': True})


# ── Quota / Goal Tracking ────────────────────────────────────────

@login_required
def quota_list(request):
    if not request.user.is_admin():
        messages.error(request, "Access denied.")
        return redirect("dashboard:dashboard")
    from .models import UserGoal
    from leads.models import Lead
    today = timezone.now().date()
    month_start = today.replace(day=1)
    users = User.objects.filter(is_active=True).order_by("first_name", "username")
    goals = {g.user_id: g for g in UserGoal.objects.filter(month=month_start)}
    rows = []
    for u in users:
        goal = goals.get(u.pk)
        achieved = Lead.objects.filter(
            status="won",
            updated_at__year=today.year,
            updated_at__month=today.month,
            assigned_to=u,
        ).aggregate(t=Sum("deal_value"))["t"] or 0
        target = goal.target if goal else None
        pct = min(int(float(achieved) / float(target) * 100), 100) if target else 0
        rows.append({"user": u, "target": target, "achieved": achieved, "pct": pct, "goal": goal})
    return render(request, "dashboard/quotas.html", {
        "rows": rows,
        "month": month_start,
        "today": today,
    })


@login_required
@require_POST
def quota_set(request):
    if not request.user.is_admin():
        messages.error(request, "Access denied.")
        return redirect("dashboard:quota_list")
    from .models import UserGoal
    from datetime import date as _date
    user_pk = request.POST.get("user_pk")
    target_str = request.POST.get("target", "").strip()
    month_str = request.POST.get("month")
    try:
        target = float(target_str)
        month = _date.fromisoformat(month_str)
        month = month.replace(day=1)
        target_user = User.objects.get(pk=user_pk)
    except (ValueError, TypeError, User.DoesNotExist):
        messages.error(request, "Invalid input.")
        return redirect("dashboard:quota_list")
    if target <= 0:
        UserGoal.objects.filter(user=target_user, month=month).delete()
        messages.success(request, f"Goal removed for {target_user.get_full_name() or target_user.username}.")
    else:
        UserGoal.objects.update_or_create(
            user=target_user, month=month,
            defaults={"target": target},
        )
        messages.success(request, f"Goal updated for {target_user.get_full_name() or target_user.username}.")
    return redirect("dashboard:quota_list")


# ── Quick Notes ──────────────────────────────────────────────────

@login_required
@require_POST
def quick_note_add(request):
    from .models import QuickNote
    from django.shortcuts import get_object_or_404
    body = request.POST.get("body", "").strip()
    if not body:
        messages.error(request, "Note cannot be empty.")
        return redirect(request.META.get("HTTP_REFERER", "/"))
    lead_pk = request.POST.get("lead_pk")
    client_pk = request.POST.get("client_pk")
    note = QuickNote(user=request.user, body=body)
    if lead_pk:
        from leads.models import Lead
        note.lead = get_object_or_404(Lead, pk=lead_pk)
    elif client_pk:
        from clients.models import Client
        note.client = get_object_or_404(Client, pk=client_pk)
    note.save()
    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
@require_POST
def quick_note_delete(request, pk):
    from .models import QuickNote
    from django.shortcuts import get_object_or_404
    note = get_object_or_404(QuickNote, pk=pk)
    note.delete()
    return redirect(request.META.get("HTTP_REFERER", "/"))


# ── Tags ─────────────────────────────────────────────────────────

@login_required
@require_POST
def tag_create(request):
    from .models import Tag
    try:
        data = json.loads(request.body)
        name = data.get("name", "").strip()[:50]
        color = data.get("color", "#6366f1")
        if not name:
            return JsonResponse({"error": "Name required"}, status=400)
        tag, _ = Tag.objects.get_or_create(name=name, defaults={"color": color})
        return JsonResponse({"id": tag.pk, "name": tag.name, "color": tag.color})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
