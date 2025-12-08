from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden

from .models import ServiceProvider, ServiceRequest
from .forms import ServiceRequestForm, ProviderEditForm


@login_required
def dashboard(request):
    """Homeowner dashboard showing their requests"""
    requests_qs = ServiceRequest.objects.filter(homeowner=request.user).select_related('provider', 'service').order_by('-created_at')
    return render(request, 'services/dashboard.html', {'requests': requests_qs})


def providers_list(request):
    """List all service providers along with the services they offer. Prefetch 'services' from the related user models to reduce queries."""
    providers = ServiceProvider.objects.select_related('user').prefetch_related('user__services')
    return render(request, 'services/providers_list.html', {'providers': providers})


def provider_detail(request, pk):
    """View a single provider and allow homeowners to send requests"""
    provider = get_object_or_404(ServiceProvider, pk=pk)

    if request.method == 'POST':
        if not request.user.is_authenticated or request.user == provider.user:
            return redirect('accounts:login')
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.homeowner = request.user
            req.provider = provider
            req.save()
            messages.success(request, 'Service request sent to the provider.')
            return redirect('services:providers')
    else:
        form = ServiceRequestForm()

    return render(request, 'services/provider_detail.html', {'provider': provider, 'form': form})


@login_required
def provider_dashboard(request):
    """Provider dashboard showing requests for this provider"""
    if not hasattr(request.user, 'provider_profile'):
        return HttpResponseForbidden('Not a provider')

    provider = request.user.provider_profile
    requests_qs = provider.requests.select_related('homeowner', 'service').order_by('-created_at')
    return render(request, 'services/provider_dashboard.html', {'provider': provider, 'requests': requests_qs})


@require_POST
@login_required
def request_action(request, pk):
    """Provider accepts/completes/cancels a service request"""
    sr = get_object_or_404(ServiceRequest, pk=pk)

    # Only provider owning the request or staff can change
    if not (hasattr(request.user, 'provider_profile') and request.user.provider_profile == sr.provider) and not request.user.is_staff:
        return HttpResponseForbidden('Not allowed')

    action = request.POST.get('action')
    if action == 'accept':
        sr.status = ServiceRequest.STATUS_ACCEPTED
    elif action == 'complete':
        sr.status = ServiceRequest.STATUS_COMPLETED
    elif action == 'cancel':
        sr.status = ServiceRequest.STATUS_CANCELLED
    sr.save()
    messages.success(request, f'Request {sr.id} updated to {sr.status}.')
    return redirect('services:provider_dashboard')


# Optional CRUD for homeowner requests

@login_required
def request_detail(request, pk):
    """Homeowner can view details of their own request if not accepted"""
    sr = get_object_or_404(ServiceRequest, pk=pk)
    if sr.homeowner != request.user or sr.status != ServiceRequest.STATUS_PENDING:
        return HttpResponseForbidden('Cannot delete this request')

    if request.method == 'POST':
        sr.delete()
        messages.success(request, 'Request deleted.')
        return redirect('services:dashboard')

    return render(request, 'services/request_confirm_delete.html', {'request_obj': sr})

@login_required
def update_request(request, pk):
    request_obj = get_object_or_404(ServiceRequest, pk=pk)

    # Only the homeowner who created the request can edit it
    if request_obj.homeowner != request.user:
        messages.error(request, "You are not allowed to edit this request.")
        return redirect("services:request_detail", pk=pk)

    if request.method == "POST":
        form = ServiceRequestForm(request.POST, instance=request_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Your request has been updated successfully.")
            return redirect("services:request_detail", pk=pk)
    else:
        form = ServiceRequestForm(instance=request_obj)

    return render(request, "services/request_edit.html", {"form": form, "request_obj": request_obj})

@login_required
def delete_request(request, pk):
    service_request = get_object_or_404(ServiceRequest, pk=pk, homeowner=request.user)

    if request.method == "POST":
        service_request.delete()
        messages.success(request, "Request deleted successfully.")
        return redirect('services:dashboard')

    return render(request, 'services/request_delete_confirm.html', {'request_item': service_request})

@login_required
def update_provider(request, pk):
    provider = get_object_or_404(ServiceProvider, pk=pk)

    # Only the owner can edit
    if provider.user != request.user:
        return HttpResponseForbidden("You are not allowed to edit this profile.")

    if request.method == "POST":
        form = ProviderEditForm(request.POST, request.FILES, instance=provider)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('services:provider_detail', pk=pk)
    else:
        form = ProviderEditForm(instance=provider)

    return render(request, "services/provider_edit.html", {"form": form, "provider": provider})

@login_required
def delete_provider(request, pk):
    provider = get_object_or_404(ServiceProvider, pk=pk)

    # Only owner can delete
    if provider.user != request.user:
        return HttpResponseForbidden("Not allowed.")

    if request.method == "POST":
        provider.delete()
        messages.success(request, "Provider profile deleted.")
        return redirect('services:providers')

    return render(request, "services/provider_delete_confirm.html", {"provider": provider})
@login_required
def provider_update(request, pk):
    provider = get_object_or_404(ServiceProvider, pk=pk)

    # Only the provider themselves should edit their profile
    if provider.user != request.user:
        messages.error(request, "You are not allowed to edit this profile.")
        return redirect("services:provider_detail", pk=pk)

    if request.method == "POST":
        form = ProviderEditForm(request.POST, request.FILES, instance=provider)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("services:provider_detail", pk=pk)
    else:
        form = ProviderEditForm(instance=provider)

    return render(request, "services/provider_update.html", {"form": form, "provider": provider})

@login_required
def provider_delete(request, pk):
    provider = get_object_or_404(ServiceProvider, pk=pk)

    # Only the owner of the profile can delete it
    if provider.user != request.user:
        messages.error(request, "You are not allowed to delete this profile.")
        return redirect("services:provider_detail", pk=pk)

    if request.method == "POST":
        user = provider.user
        provider.delete()
        user.delete()   # Optional: delete the user account too

        messages.success(request, "Your provider profile has been deleted.")
        return redirect("accounts:login")

    return render(request, "services/provider_delete.html", {"provider": provider})

