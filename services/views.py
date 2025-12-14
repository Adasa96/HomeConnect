from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden, JsonResponse

from .models import ServiceRequest
from accounts.models import ServiceProvider
from .forms import ServiceRequestForm, ProviderEditForm

from django.conf import settings
from django_daraja.mpesa.core import MpesaClient


# ----------------------
# HOMEOWNER VIEWS
# ----------------------

@login_required
def homeowner_dashboard(request):
    """Homeowner dashboard: list requests and create new ones"""
    if request.user.user_type != 'homeowner':
        return redirect('accounts:redirect_after_login')

    requests_qs = ServiceRequest.objects.filter(
        homeowner=request.user
    ).select_related('provider', 'service').order_by('-created_at')

    if request.method == 'POST':
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            service_request = form.save(commit=False)
            service_request.homeowner = request.user
            service_request.save()

            # Optional: initiate STK Push payment
            phone = request.POST.get('phone')
            if phone and hasattr(service_request.service, 'price'):
                try:
                    cl = MpesaClient(
                        consumer_key=settings.MPESA_CONSUMER_KEY,
                        consumer_secret=settings.MPESA_CONSUMER_SECRET,
                        environment=settings.MPESA_ENVIRONMENT
                    )
                    response = cl.stk_push(
                        phone_number=phone,
                        amount=service_request.service.price,
                        account_reference=f"SR-{service_request.pk}",
                        transaction_desc=f"Payment for {service_request.service.name}",
                        callback_url=request.build_absolute_uri('/mpesa/callback/')
                    )
                    service_request.checkout_request_id = response.json().get('CheckoutRequestID')
                    service_request.save()
                    messages.success(request, f"Request sent and payment initiated to {service_request.provider.company_name}")
                except Exception as e:
                    messages.warning(request, f"Request sent but payment failed: {e}")
            else:
                messages.success(request, f"Request sent to {service_request.provider.company_name}")

            return redirect('services:homeowner_dashboard')
    else:
        form = ServiceRequestForm()

    return render(request, 'services/dashboard.html', {'requests': requests_qs, 'form': form})


@login_required
def create_service_request(request, provider_pk=None):
    """Standalone page to create a service request"""
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
    """Homeowner views details of their request"""
    sr = get_object_or_404(ServiceRequest, pk=pk, homeowner=request.user)
    return render(request, 'services/request_detail.html', {'request_obj': sr})


@login_required
def update_request(request, pk):
    """Homeowner updates a request (only description editable)"""
    service_request = get_object_or_404(ServiceRequest, pk=pk, homeowner=request.user)

    if request.method == 'POST':
        form = ServiceRequestForm(request.POST, instance=service_request)
        if form.is_valid():
            updated = form.save(commit=False)
            # Lock fields that shouldn't be changed
            updated.homeowner = request.user
            updated.provider = service_request.provider
            updated.service = service_request.service
            updated.save()
            messages.success(request, "Request updated successfully.")
            return redirect('services:homeowner_dashboard')
    else:
        form = ServiceRequestForm(instance=service_request)

    return render(request, 'services/request_edit.html', {'form': form, 'request_obj': service_request})


@login_required
@require_POST
def delete_request(request, pk):
    """Homeowner deletes a request (AJAX)"""
    service_request = get_object_or_404(ServiceRequest, pk=pk, homeowner=request.user)
    service_request.delete()
    return JsonResponse({"success": True})


# ----------------------
# SERVICE PROVIDER VIEWS
# ----------------------

@login_required
def providers_list(request):
    """List all service providers"""
    providers = ServiceProvider.objects.select_related('user').prefetch_related('services')
    return render(request, 'services/providers_list.html', {'providers': providers})


@login_required
def provider_detail(request, pk):
    """View provider details and allow homeowners to create requests"""
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
    """Provider sees all requests assigned to them"""
    if request.user.user_type != "service_provider":
        return HttpResponseForbidden("Access denied")

    provider = request.user.provider_profile
    requests_qs = ServiceRequest.objects.filter(provider=provider)

    return render(request, "services/provider_dashboard.html", {"provider": provider, "requests": requests_qs})


@login_required
@require_POST
def request_action(request, pk):
    """Provider can accept, complete, or cancel a request"""
    sr = get_object_or_404(ServiceRequest, pk=pk)

    # Only provider owner or staff can change
    if not (hasattr(request.user, 'provider_profile') and request.user.provider_profile == sr.provider) and not request.user.is_staff:
        return HttpResponseForbidden("Not allowed.")

    action = request.POST.get('action')
    if action == 'accept':
        sr.status = ServiceRequest.STATUS_ACCEPTED
    elif action == 'complete':
        sr.status = ServiceRequest.STATUS_COMPLETED
    elif action == 'cancel':
        sr.status = ServiceRequest.STATUS_CANCELLED
    else:
        messages.error(request, "Invalid action.")
        return redirect('services:provider_dashboard')

    sr.save()
    messages.success(request, f"Request {sr.id} updated to {sr.status}.")
    return redirect('services:provider_dashboard')


@login_required
def provider_update(request, pk):
    """Provider edits their profile"""
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
    """Delete provider profile (and optionally the user account)"""
    provider = get_object_or_404(ServiceProvider, pk=pk)
    if provider.user != request.user:
        return HttpResponseForbidden("Not allowed.")

    if request.method == 'POST':
        user = provider.user
        provider.delete()
        user.delete()
        messages.success(request, "Provider profile deleted successfully.")
        return redirect('accounts:login')

    return render(request, 'services/provider_delete_confirm.html', {'provider': provider})
