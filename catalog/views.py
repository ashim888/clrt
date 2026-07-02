from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Service, ServiceCategory
from .forms import ServiceForm, ServiceCategoryForm


def _can_edit(user):
    return user.is_superuser or getattr(user, 'role', '') in ('admin', 'sales')


@login_required
def service_list(request):
    q = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    services = Service.objects.select_related('category')
    if q:
        services = services.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if category_id:
        services = services.filter(category_id=category_id)
    categories = ServiceCategory.objects.all()
    return render(request, 'catalog/service_list.html', {
        'services': services,
        'categories': categories,
        'q': q,
        'category_id': category_id,
        'can_edit': _can_edit(request.user),
    })


@login_required
def service_create(request):
    if not _can_edit(request.user):
        messages.error(request, 'Access denied.')
        return redirect('catalog:service_list')
    form = ServiceForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Service added to catalog.')
        return redirect('catalog:service_list')
    return render(request, 'catalog/service_form.html', {'form': form, 'title': 'Add Service'})


@login_required
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if not _can_edit(request.user):
        messages.error(request, 'Access denied.')
        return redirect('catalog:service_list')
    form = ServiceForm(request.POST or None, instance=service)
    if form.is_valid():
        form.save()
        messages.success(request, 'Service updated.')
        return redirect('catalog:service_list')
    return render(request, 'catalog/service_form.html', {'form': form, 'title': 'Edit Service', 'service': service})


@login_required
@require_POST
def service_delete(request, pk):
    if not _can_edit(request.user):
        messages.error(request, 'Access denied.')
        return redirect('catalog:service_list')
    service = get_object_or_404(Service, pk=pk)
    service.delete()
    messages.success(request, f'"{service.name}" removed from catalog.')
    return redirect('catalog:service_list')


@login_required
def service_catalog_json(request):
    """JSON endpoint consumed by proposal/invoice forms to autocomplete line items."""
    q = request.GET.get('q', '').strip()
    qs = Service.objects.filter(is_active=True).select_related('category')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
    data = [
        {
            'id': s.pk,
            'name': s.name,
            'description': s.description,
            'unit': s.get_unit_display(),
            'default_price': float(s.default_price),
            'category': s.category.name if s.category else '',
        }
        for s in qs[:50]
    ]
    return JsonResponse({'services': data})
