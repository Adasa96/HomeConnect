from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden

from .models import ServiceRequest
from accounts.models import ServiceProvider

from .forms import ServiceRequestForm, ProviderEditForm

# HOMEOWNER VIEWS
@login_required
def homeowner_dashboard(request):
    """Dashboard for homeowners showing their service requests and creating new requests"""
    if request.user.user_type != 'homeowner':
        return redirect('services:provider_dashboard')

    requests_qs = (
        ServiceRequest.objects.filter(homeowner=request.user)
        .select_related('provider', 'service')
        .order_by('-created_at')
    )

    if request.method == 'POST':
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            service_request = form.save(commit=False)
            service_request.homeowner = request.user
            service_request.save()
            messages.success(request, f"Service request sent to {service_request.provider.company_name}")
            return redirect('services:homeowner_dashboard')
    else:
        form = ServiceRequestForm()

    return render(
        request,
        'services/dashboard.html',
        {'requests': requests_qs, 'form': form}
    )


@login_required
def create_service_request(request, provider_pk=None):
    """Homeowner creates a service request for a provider"""
    if request.user.user_type != 'homeowner':
        messages.error(request, "Only homeowners can create service requests.")
        return redirect('services:provider_dashboard')

    form = ServiceRequestForm(request.POST or None)
    if provider_pk:
        form.fields['provider'].queryset = ServiceProvider.objects.filter(pk=provider_pk)
    else:
        form.fields['provider'].queryset = ServiceProvider.objects.all()

    if request.method == 'POST' and form.is_valid():
        service_request = form.save(commit=False)
        service_request.homeowner = request.user
        service_request.save()
        messages.success(request, "Service request submitted successfully!")
        return redirect('services:homeowner_dashboard')

    return render(request, 'services/service_request_form.html', {'form': form})


@login_required
def request_detail(request, pk):
    """Homeowner views their own request"""
    sr = get_object_or_404(ServiceRequest, pk=pk, homeowner=request.user)
    return render(request, 'services/request_detail.html', {'request_obj': sr})


@login_required
def update_request(request, pk):
    """Homeowner edits their own request"""
    request_obj = get_object_or_404(ServiceRequest, pk=pk, homeowner=request.user)

    if request.method == 'POST':
        form = ServiceRequestForm(request.POST, instance=request_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Request updated successfully.")
            return redirect('services:request_detail', pk=pk)
    else:
        form = ServiceRequestForm(instance=request_obj)

    return render(request, 'services/request_edit.html', {'form': form, 'request_obj': request_obj})


@login_required
def delete_request(request, pk):
    """Homeowner deletes their own request"""
    service_request = get_object_or_404(ServiceRequest, pk=pk, homeowner=request.user)

    if request.method == 'POST':
        service_request.delete()
        messages.success(request, "Request deleted successfully.")
        return redirect('services:homeowner_dashboard')

    return render(request, 'services/request_delete_confirm.html', {'request_item': service_request})


# SERVICE PROVIDER VIEWS
@login_required
def providers_list(request):
    """List all service providers"""
    providers = ServiceProvider.objects.select_related('user').prefetch_related('services')
    return render(request, 'services/providers_list.html', {'providers': providers})


@login_required
def provider_detail(request, pk):
    """View a single provider"""
    provider = get_object_or_404(ServiceProvider, pk=pk)
    form = ServiceRequestForm()

    if request.method == 'POST' and request.user.user_type == 'homeowner':
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            sr = form.save(commit=False)
            sr.homeowner = request.user
            sr.provider = provider
            sr.save()
            messages.success(request, "Service request sent successfully!")
            return redirect('services:providers')

    return render(request, 'services/provider_detail.html', {'provider': provider, 'form': form})


@login_required
def provider_dashboard(request):
    """Provider dashboard showing requests for this provider"""
    if request.user.user_type != 'service_provider':
        return HttpResponseForbidden("Access denied.")

    # Use the related_name from your model
    provider = request.user.services_provider_profile

    # Get all requests for this provider
    requests_qs = provider.requests.select_related('homeowner', 'service').order_by('-created_at')

    return render(
        request,
        'services/provider_dashboard.html',
        {'provider': provider, 'requests': requests_qs}
    )

@require_POST
@login_required
def request_action(request, pk):
    """Provider can accept/complete/cancel a request"""
    sr = get_object_or_404(ServiceRequest, pk=pk)

    # Only provider owner or staff can change
    if not (hasattr(request.user, 'services_provider_profile') and request.user.services_provider_profile == sr.provider) and not request.user.is_staff:
        return HttpResponseForbidden("Not allowed.")

    action = request.POST.get('action')
    if action == 'accept':
        sr.status = ServiceRequest.STATUS_ACCEPTED
    elif action == 'complete':
        sr.status = ServiceRequest.STATUS_COMPLETED
    elif action == 'cancel':
        sr.status = ServiceRequest.STATUS_CANCELLED
    sr.save()
    messages.success(request, f"Request {sr.id} updated to {sr.status}.")
    return redirect('services:provider_dashboard')


@login_required
def provider_update(request, pk):
    """Edit provider profile"""
    provider = get_object_or_404(ServiceProvider, pk=pk)
    if provider.user != request.user:
        return HttpResponseForbidden("Not allowed.")

    form = ProviderEditForm(request.POST or None, request.FILES or None, instance=provider)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('services:provider_detail', pk=pk)

    return render(request, 'services/provider_update.html', {'form': form, 'provider': provider})


@login_required
def provider_delete(request, pk):
    """Delete provider profile"""
    provider = get_object_or_404(ServiceProvider, pk=pk)
    if provider.user != request.user:
        return HttpResponseForbidden("Not allowed.")

    if request.method == 'POST':
        user = provider.user
        provider.delete()
        user.delete()  # Optional: delete the user account as well
        messages.success(request, "Provider profile deleted successfully.")
        return redirect('accounts:login')

    return render(request, 'services/provider_delete_confirm.html', {'provider': provider})
