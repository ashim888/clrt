import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, Count, Max, Prefetch
from .models import Lead, Activity
from .forms import LeadForm, ActivityForm

LEAD_SORT_FIELDS = {
    "org": "organization_name",
    "contact": "contact_person",
    "status": "status",
    "value": "deal_value",
    "created": "created_at",
    "followup": "next_followup_max",
}


def _can_edit_leads(user):
    return user.role in ("admin", "sales") or user.is_superuser


@login_required
def lead_list(request):
    q = request.GET.get("q", "")
    status = request.GET.get("status", "")
    source = request.GET.get("source", "")
    sort = request.GET.get("sort", "created")
    order = request.GET.get("order", "desc")

    tag = request.GET.get("tag", "")

    latest_activity_qs = Activity.objects.select_related("created_by").order_by("-created_at")
    leads = (
        Lead.objects
        .select_related("assigned_to")
        .prefetch_related(
            Prefetch("activities", queryset=latest_activity_qs, to_attr="all_activities"),
            "tags",
        )
        .annotate(
            activity_count=Count("activities"),
            next_followup_max=Max("activities__next_follow_up_date"),
        )
    )
    if q:
        leads = leads.filter(
            Q(organization_name__icontains=q) |
            Q(contact_person__icontains=q) |
            Q(phone__icontains=q)
        )
    if status:
        leads = leads.filter(status=status)
    if source:
        leads = leads.filter(source=source)
    if tag:
        leads = leads.filter(tags__pk=tag)

    sort_field = LEAD_SORT_FIELDS.get(sort, "created_at")
    leads = leads.order_by(f"{'-' if order == 'desc' else ''}{sort_field}")

    paginator = Paginator(leads, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    from dashboard.models import Tag
    return render(request, "leads/lead_list.html", {
        "leads": page_obj,
        "page_obj": page_obj,
        "q": q,
        "status": status,
        "source": source,
        "tag": tag,
        "sort": sort,
        "order": order,
        "status_choices": Lead.STATUS_CHOICES,
        "source_choices": Lead.SOURCE_CHOICES,
        "all_tags": Tag.objects.all(),
    })


@login_required
def lead_detail(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    activities = lead.activities.select_related("created_by")
    from dashboard.models import AuditLog, QuickNote
    audit_logs = AuditLog.objects.filter(model_name="Lead", object_id=pk).select_related("user")[:20]
    quick_notes = QuickNote.objects.filter(lead_id=pk).select_related("user")
    return render(request, "leads/lead_detail.html", {
        "lead": lead,
        "activities": activities,
        "status_choices": Lead.STATUS_CHOICES,
        "audit_logs": audit_logs,
        "quick_notes": quick_notes,
    })


@login_required
def lead_create(request):
    if not _can_edit_leads(request.user):
        messages.error(request, "Access denied.")
        return redirect("leads:lead_list")
    form = LeadForm(request.POST or None)
    if form.is_valid():
        lead = form.save()
        messages.success(request, f"Lead \"{lead.organization_name}\" created.")
        from dashboard.audit import log_audit
        log_audit(request.user, 'created', lead)
        if lead.assigned_to and lead.assigned_to != request.user:
            from django.urls import reverse as _rev
            from dashboard.models import Notification
            Notification.push(
                lead.assigned_to,
                title=f"New lead assigned: {lead.organization_name}",
                link=_rev("leads:lead_detail", args=[lead.pk]),
                type="lead",
            )
        return redirect("leads:lead_detail", pk=lead.pk)
    from dashboard.models import Tag
    return render(request, "leads/lead_form.html", {
        "form": form, "title": "Add Lead",
        "all_tags": Tag.objects.all(), "selected_tags": [],
    })


@login_required
def lead_edit(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if not _can_edit_leads(request.user):
        messages.error(request, "Access denied.")
        return redirect("leads:lead_detail", pk=pk)
    form = LeadForm(request.POST or None, instance=lead)
    if form.is_valid():
        from dashboard.audit import log_audit, model_changes
        old = Lead.objects.get(pk=pk)
        form.save()
        lead.refresh_from_db()
        diff = model_changes(old, lead, ["organization_name", "contact_person", "phone", "email", "source", "deal_value", "status", "assigned_to", "notes"])
        if diff:
            log_audit(request.user, 'updated', lead, diff)
        messages.success(request, "Lead updated.")
        return redirect("leads:lead_detail", pk=pk)
    from dashboard.models import Tag
    return render(request, "leads/lead_form.html", {
        "form": form, "title": "Edit Lead", "lead": lead,
        "all_tags": Tag.objects.all(), "selected_tags": lead.tags.all(),
    })


@login_required
def lead_delete(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if not request.user.is_admin():
        messages.error(request, "Access denied.")
        return redirect("leads:lead_detail", pk=pk)
    if request.method == "POST":
        lead.delete()
        messages.success(request, "Lead deleted.")
        return redirect("leads:lead_list")
    return render(request, "leads/lead_confirm_delete.html", {"lead": lead})


@login_required
def activity_add(request, lead_pk):
    lead = get_object_or_404(Lead, pk=lead_pk)
    form = ActivityForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        activity = form.save(commit=False)
        activity.lead = lead
        activity.created_by = request.user
        activity.save()
        messages.success(request, "Activity logged.")
        return redirect("leads:lead_detail", pk=lead_pk)
    return render(request, "leads/activity_form.html", {"form": form, "lead": lead})


@login_required
def activity_edit(request, pk):
    activity = get_object_or_404(Activity, pk=pk)
    if not _can_edit_leads(request.user):
        messages.error(request, "Access denied.")
        return redirect("leads:lead_detail", pk=activity.lead.pk)
    form = ActivityForm(request.POST or None, request.FILES or None, instance=activity)
    if form.is_valid():
        form.save()
        messages.success(request, "Activity updated.")
        return redirect("leads:lead_detail", pk=activity.lead.pk)
    return render(request, "leads/activity_form.html", {"form": form, "lead": activity.lead, "editing": True})


@login_required
@require_POST
def activity_delete(request, pk):
    activity = get_object_or_404(Activity, pk=pk)
    if not _can_edit_leads(request.user):
        messages.error(request, "Access denied.")
        return redirect("leads:lead_detail", pk=activity.lead.pk)
    lead_pk = activity.lead.pk
    activity.delete()
    messages.success(request, "Activity deleted.")
    return redirect("leads:lead_detail", pk=lead_pk)


@login_required
@require_POST
def activity_update_status(request, pk):
    activity = get_object_or_404(Activity, pk=pk)
    valid_statuses = [s for s, _ in Activity.STATUS_CHOICES]
    new_status = request.POST.get("status", "").strip()
    if new_status not in valid_statuses:
        return JsonResponse({"error": "Invalid status"}, status=400)
    activity.status = new_status
    update_fields = ["status"]
    note = request.POST.get("resolution_note", "").strip()
    activity.resolution_note = note
    update_fields.append("resolution_note")
    if request.FILES.get("attachment"):
        activity.attachment = request.FILES["attachment"]
        update_fields.append("attachment")
    if new_status == "rescheduled":
        from datetime import date as _date
        reschedule_date_str = request.POST.get("reschedule_date", "").strip()
        if reschedule_date_str:
            try:
                activity.next_follow_up_date = _date.fromisoformat(reschedule_date_str)
                update_fields.append("next_follow_up_date")
            except ValueError:
                pass
    activity.save(update_fields=update_fields)
    attachment_url = activity.attachment.url if activity.attachment else None
    return JsonResponse({
        "status": activity.status,
        "resolution_note": activity.resolution_note,
        "next_follow_up_date": str(activity.next_follow_up_date) if activity.next_follow_up_date else None,
        "attachment_url": attachment_url,
    })


@login_required
@require_POST
def lead_update_status(request, pk):
    if not _can_edit_leads(request.user):
        return JsonResponse({"error": "Permission denied"}, status=403)
    lead = get_object_or_404(Lead, pk=pk)
    old_status = lead.status
    new_status = request.POST.get("status")
    valid = [s for s, _ in Lead.STATUS_CHOICES]
    if new_status not in valid:
        return JsonResponse({"error": "Invalid status"}, status=400)
    lead.status = new_status
    update_fields = ["status", "updated_at"]
    if new_status == "lost":
        lead.lost_reason = request.POST.get("lost_reason", "").strip()
        update_fields.append("lost_reason")
    lead.save(update_fields=update_fields)
    from dashboard.audit import log_audit
    changes = {"status": [old_status, new_status]}
    if new_status == "lost" and lead.lost_reason:
        changes["lost_reason"] = ["", lead.lost_reason]
    log_audit(request.user, 'status_changed', lead, changes)

    # Push in-app notification to the assigned user
    if new_status in ("won", "lost") and lead.assigned_to and lead.assigned_to != request.user:
        from django.urls import reverse as _rev
        from dashboard.models import Notification
        verb = "Won" if new_status == "won" else "Lost"
        Notification.push(
            lead.assigned_to,
            title=f"Lead {verb}: {lead.organization_name}",
            body=lead.lost_reason if new_status == "lost" else "",
            link=_rev("leads:lead_detail", args=[lead.pk]),
            type="lead",
        )

    response = {"status": new_status, "label": lead.get_status_display()}
    if new_status == "won" and not hasattr(lead, "client"):
        from django.urls import reverse
        response["redirect"] = reverse("leads:convert_to_client", args=[lead.pk])
    return JsonResponse(response)


@login_required
def lead_check_duplicate(request):
    org = request.GET.get("org", "").strip()
    phone = request.GET.get("phone", "").strip()
    exclude_pk = request.GET.get("pk")
    if not org and not phone:
        return JsonResponse({"duplicates": []})
    qs = Lead.objects
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    matches = []
    if org:
        for lead in qs.filter(organization_name__iexact=org)[:3]:
            matches.append({"pk": lead.pk, "org": lead.organization_name, "status": lead.get_status_display()})
    if phone and not matches:
        for lead in qs.filter(phone=phone)[:3]:
            matches.append({"pk": lead.pk, "org": lead.organization_name, "status": lead.get_status_display()})
    return JsonResponse({"duplicates": matches})


@login_required
@require_POST
def lead_bulk_action(request):
    if not _can_edit_leads(request.user):
        return JsonResponse({"error": "Permission denied"}, status=403)
    ids = request.POST.getlist("ids")
    action = request.POST.get("action")
    if not ids or not action:
        return JsonResponse({"error": "Missing ids or action"}, status=400)
    qs = Lead.objects.filter(pk__in=ids)
    if action == "delete":
        if not request.user.is_admin():
            return JsonResponse({"error": "Only admins can delete leads"}, status=403)
        qs.delete()
    elif action == "status":
        value = request.POST.get("value")
        valid = [s for s, _ in Lead.STATUS_CHOICES]
        if value not in valid:
            return JsonResponse({"error": "Invalid status"}, status=400)
        qs.update(status=value)
    else:
        return JsonResponse({"error": "Unknown action"}, status=400)
    return JsonResponse({"ok": True})


@login_required
def lead_kanban(request):
    STAGE_PROBABILITY = {
        "new": 10, "contacted": 25, "demo": 50,
        "negotiation": 75, "won": 100, "lost": 0,
    }
    status_order = ["new", "contacted", "demo", "negotiation", "won", "lost"]
    status_labels = dict(Lead.STATUS_CHOICES)
    latest_activity_qs = Activity.objects.order_by("-created_at")
    all_leads = (
        Lead.objects
        .select_related("assigned_to")
        .prefetch_related(Prefetch("activities", queryset=latest_activity_qs, to_attr="all_activities"))
    )
    buckets = {s: [] for s in status_order}
    for lead in all_leads:
        if lead.status in buckets:
            buckets[lead.status].append(lead)

    columns = []
    pipeline_total = 0.0
    weighted_total = 0.0
    for s in status_order:
        col_leads = buckets[s]
        col_value = sum((float(l.deal_value) for l in col_leads if l.deal_value), 0.0)
        prob = STAGE_PROBABILITY[s]
        columns.append({
            "key": s,
            "label": status_labels[s],
            "leads": col_leads,
            "value": col_value,
            "probability": prob,
        })
        if s not in ("won", "lost"):
            pipeline_total += col_value
        weighted_total += col_value * prob / 100

    return render(request, "leads/lead_kanban.html", {
        "columns": columns,
        "pipeline_total": pipeline_total,
        "weighted_total": weighted_total,
    })


@login_required
def lead_import(request):
    if not _can_edit_leads(request.user):
        messages.error(request, "Access denied.")
        return redirect("leads:lead_list")

    VALID_SOURCES = {s for s, _ in Lead.SOURCE_CHOICES}
    VALID_STATUSES = {s for s, _ in Lead.STATUS_CHOICES}
    REQUIRED_COLS = {"organization_name", "contact_person", "phone"}

    # Step 2 — confirm import (data stored in session)
    if request.method == "POST" and request.POST.get("action") == "import":
        import json as _json
        rows = request.session.pop("lead_import_rows", [])
        if not rows:
            messages.error(request, "Session expired — please re-upload the file.")
            return redirect("leads:lead_import")
        skipped = 0
        created = 0
        for row in rows:
            if row.get("_dup"):
                skipped += 1
                continue
            dv = None
            if row.get("deal_value"):
                try:
                    dv = float(str(row["deal_value"]).replace(",", ""))
                except ValueError:
                    pass
            Lead.objects.create(
                organization_name=row["organization_name"],
                contact_person=row.get("contact_person", ""),
                phone=row.get("phone", ""),
                email=row.get("email", ""),
                source=row.get("source", "") if row.get("source", "") in VALID_SOURCES else "",
                deal_value=dv,
                status=row.get("status", "new") if row.get("status", "new") in VALID_STATUSES else "new",
                notes=row.get("notes", ""),
            )
            created += 1
        messages.success(request, f"Imported {created} lead(s). {skipped} duplicate(s) skipped.")
        return redirect("leads:lead_list")

    # Step 1 — parse uploaded file
    if request.method == "POST" and request.FILES.get("csv_file"):
        import io
        f = request.FILES["csv_file"]
        try:
            text = f.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            f.seek(0)
            text = f.read().decode("latin-1")
        reader = csv.DictReader(io.StringIO(text))
        cols = [c.strip().lower().replace(" ", "_") for c in (reader.fieldnames or [])]
        missing = REQUIRED_COLS - set(cols)
        if missing:
            messages.error(request, f"CSV is missing required columns: {', '.join(sorted(missing))}")
            return redirect("leads:lead_import")

        existing_names = set(
            Lead.objects.values_list("organization_name__iexact", flat=True)
        )
        existing_phones = set(Lead.objects.values_list("phone", flat=True))

        rows = []
        for raw in reader:
            norm = {c.strip().lower().replace(" ", "_"): (v or "").strip() for c, v in raw.items()}
            org = norm.get("organization_name", "")
            phone = norm.get("phone", "")
            if not org:
                continue
            is_dup = org.lower() in existing_names or (phone and phone in existing_phones)
            norm["_dup"] = is_dup
            rows.append(norm)

        if not rows:
            messages.error(request, "No valid rows found in the file.")
            return redirect("leads:lead_import")

        request.session["lead_import_rows"] = rows
        return render(request, "leads/lead_import.html", {
            "rows": rows,
            "cols": cols,
            "preview": True,
            "new_count": sum(1 for r in rows if not r["_dup"]),
            "dup_count": sum(1 for r in rows if r["_dup"]),
        })

    if request.GET.get("sample"):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="leads_sample.csv"'
        writer = csv.writer(response)
        writer.writerow(["organization_name", "contact_person", "phone", "email", "source", "deal_value", "status", "notes"])
        writer.writerow(["Acme Corp", "Jane Doe", "9800000001", "jane@acme.com", "referral", "50000", "new", "Met at conference"])
        writer.writerow(["Beta Ltd", "John Smith", "9800000002", "john@beta.com", "website", "", "contacted", ""])
        return response

    COLUMNS = [
        ("organization_name", True),
        ("contact_person", True),
        ("phone", True),
        ("email", False),
        ("source", False),
        ("deal_value", False),
        ("status", False),
        ("notes", False),
    ]
    return render(request, "leads/lead_import.html", {"preview": False, "columns": COLUMNS})


@login_required
def lead_export_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="leads.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "Organization", "Contact Person", "Phone", "Email",
        "Source", "Deal Value (Rs.)", "Status", "Assigned To", "Created",
    ])
    for lead in Lead.objects.select_related("assigned_to").order_by("-created_at"):
        writer.writerow([
            lead.organization_name,
            lead.contact_person,
            lead.phone,
            lead.email,
            lead.get_source_display() if lead.source else "",
            lead.deal_value or "",
            lead.get_status_display(),
            lead.assigned_to.get_full_name() if lead.assigned_to else "",
            lead.created_at.strftime("%Y-%m-%d"),
        ])
    return response


@login_required
def convert_to_client(request, pk):
    from clients.models import Client
    lead = get_object_or_404(Lead, pk=pk)
    if lead.status != "won":
        messages.error(request, "Only Won leads can be converted to clients.")
        return redirect("leads:lead_detail", pk=pk)
    if hasattr(lead, "client"):
        messages.info(request, "Already converted.")
        return redirect("clients:client_detail", pk=lead.client.pk)
    if request.method == "POST":
        client = Client.objects.create(
            organization_name=lead.organization_name,
            linked_lead=lead,
            phone=lead.phone,
            email=lead.email,
        )
        messages.success(request, f"Lead converted to client: {client.organization_name}")
        return redirect("clients:client_detail", pk=client.pk)
    return render(request, "leads/convert_confirm.html", {"lead": lead})


# ── Public Lead Capture ──────────────────────────────────────────

def lead_capture(request):
    from .forms import LeadCaptureForm
    from dashboard.models import SiteSettings, Notification
    from django.contrib.auth import get_user_model
    site = SiteSettings.load()
    form = LeadCaptureForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if form.cleaned_data.get("website_url"):
            # Honeypot triggered — silently discard
            return redirect("leads:lead_capture_thanks")
        lead = Lead.objects.create(
            organization_name=form.cleaned_data["organization_name"],
            contact_person=form.cleaned_data["contact_person"],
            phone=form.cleaned_data["phone"],
            email=form.cleaned_data["email"],
            notes=form.cleaned_data.get("notes", ""),
            source="website",
            status="new",
        )
        from django.urls import reverse
        link = reverse("leads:lead_detail", args=[lead.pk])
        User = get_user_model()
        for admin in User.objects.filter(role="admin", is_active=True):
            Notification.push(
                admin,
                title=f"New web enquiry: {lead.organization_name}",
                body=f"{lead.contact_person} · {lead.phone}",
                link=link,
                type="lead",
            )
        return redirect("leads:lead_capture_thanks")
    return render(request, "leads/lead_capture.html", {"form": form, "site": site})


def lead_capture_thanks(request):
    from dashboard.models import SiteSettings
    return render(request, "leads/lead_capture_thanks.html", {"site": SiteSettings.load()})
