import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, Count, Max, Prefetch
from .models import Lead, Activity
from .forms import LeadForm, ActivityForm


def _can_edit_leads(user):
    return user.role in ("admin", "sales") or user.is_superuser


@login_required
def lead_list(request):
    q = request.GET.get("q", "")
    status = request.GET.get("status", "")
    latest_activity_qs = Activity.objects.select_related("created_by").order_by("-created_at")
    leads = (
        Lead.objects
        .select_related("assigned_to")
        .prefetch_related(Prefetch("activities", queryset=latest_activity_qs, to_attr="all_activities"))
        .annotate(
            activity_count=Count("activities"),
            next_followup_max=Max("activities__next_follow_up_date"),
        )
    )
    source = request.GET.get("source", "")
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
    leads = leads.order_by("-created_at")
    return render(request, "leads/lead_list.html", {
        "leads": leads,
        "q": q,
        "status": status,
        "source": source,
        "status_choices": Lead.STATUS_CHOICES,
        "source_choices": Lead.SOURCE_CHOICES,
    })


@login_required
def lead_detail(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    activities = lead.activities.select_related("created_by")
    return render(request, "leads/lead_detail.html", {
        "lead": lead,
        "activities": activities,
        "status_choices": Lead.STATUS_CHOICES,
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
        return redirect("leads:lead_detail", pk=lead.pk)
    return render(request, "leads/lead_form.html", {"form": form, "title": "Add Lead"})


@login_required
def lead_edit(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if not _can_edit_leads(request.user):
        messages.error(request, "Access denied.")
        return redirect("leads:lead_detail", pk=pk)
    form = LeadForm(request.POST or None, instance=lead)
    if form.is_valid():
        form.save()
        messages.success(request, "Lead updated.")
        return redirect("leads:lead_detail", pk=pk)
    return render(request, "leads/lead_form.html", {"form": form, "title": "Edit Lead", "lead": lead})


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
    new_status = request.POST.get("status")
    valid = [s for s, _ in Lead.STATUS_CHOICES]
    if new_status not in valid:
        return JsonResponse({"error": "Invalid status"}, status=400)
    lead.status = new_status
    lead.save(update_fields=["status", "updated_at"])
    response = {"status": new_status, "label": lead.get_status_display()}
    # If just marked Won and not yet a client, signal frontend to redirect
    if new_status == "won" and not hasattr(lead, "client"):
        from django.urls import reverse
        response["redirect"] = reverse("leads:convert_to_client", args=[lead.pk])
    return JsonResponse(response)


@login_required
def lead_kanban(request):
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
    # Build an ordered list of column dicts for the template
    columns = [
        {"key": s, "label": status_labels[s], "leads": buckets[s]}
        for s in status_order
    ]
    return render(request, "leads/lead_kanban.html", {
        "columns": columns,
        "status_order": status_order,
    })


@login_required
def lead_export_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="leads.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "Organization", "Contact Person", "Phone", "Email",
        "Source", "Status", "Assigned To", "Created",
    ])
    for lead in Lead.objects.select_related("assigned_to").order_by("-created_at"):
        writer.writerow([
            lead.organization_name,
            lead.contact_person,
            lead.phone,
            lead.email,
            lead.get_source_display() if lead.source else "",
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
