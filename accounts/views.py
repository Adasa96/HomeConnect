from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponseForbidden, JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth import get_user_model
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView

from services.models import ServiceRequest, Service
from accounts.models import ServiceProvider
from services.forms import ServiceRequestForm
from .forms import (
    ProviderSkillsForm,
    UserRegistrationForm,
    UserLoginForm,
    UserProfileForm,
    ServiceProviderUpdateForm,
    UserUpdateForm,
)
from connectmpesa.models import PaymentRequest, MpesaTransaction

# Optional: import for Daraja integration
from django_daraja.mpesa.core import MpesaClient

User = get_user_model()

# -------------------------
# HOME PAGE
# -------------------------
def home_view(request):
    return render(request, 'accounts/home_page.html')


# -------------------------
# AUTHENTICATION
# -------------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:redirect_after_login')

    form = UserLoginForm(request.POST or None)
    if request.method == "POST": 
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")

             # Debugging prints
            print("Username:", username, "Password:", password)
            print("User exists:", User.objects.filter(username=username).exists())
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('accounts:redirect_after_login')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            # Display form errors
            messages.error(request, "Please correct the errors below.")
    
    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    request.session.flush()
    messages.info(request, "Logged out successfully.")
    return redirect("accounts:login")


def register_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:redirect_after_login')

    form = UserRegistrationForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Account created. Welcome {user.username}!")
        return redirect('accounts:redirect_after_login')
    return render(request, "accounts/register.html", {"form": form})


@login_required
def redirect_after_login(request):
    if request.user.user_type == "service_provider":
        return redirect("accounts:provider_dashboard")
    return redirect("accounts:homeowner_dashboard")


# -------------------------
# DASHBOARDS
# -------------------------
@login_required
def provider_dashboard(request):
    if request.user.user_type != "service_provider":
        return HttpResponseForbidden("Access denied.")

    provider = request.user.provider_profile
    requests_list = ServiceRequest.objects.filter(provider=provider).select_related('homeowner', 'service')
    return render(request, "services/provider_dashboard.html", {"provider": provider, "requests": requests_list})


@login_required
def homeowner_dashboard(request):
    if request.user.user_type != "homeowner":
        return HttpResponseForbidden("Access denied.")

    requests_list = ServiceRequest.objects.filter(homeowner=request.user).select_related('provider', 'service')
    return render(request, "services/homeowner_dashboard.html", {"requests": requests_list})


# -------------------------
# PROFILE MANAGEMENT
# -------------------------
@login_required
def profile_view(request):
    form = UserProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form})


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserUpdateForm, ServiceProviderUpdateForm

@login_required
def edit_profile(request):
    user = request.user

    if user.user_type == "service_provider":
        # Service provider: edit both user info and provider-specific fields
        provider = user.provider_profile
        if request.method == "POST":
            user_form = UserUpdateForm(request.POST, request.FILES, instance=user)
            provider_form = ServiceProviderUpdateForm(request.POST, request.FILES, instance=provider)
            if user_form.is_valid() and provider_form.is_valid():
                user_form.save()
                provider_form.save()
                messages.success(request, "Profile updated successfully!")
                return redirect("accounts:profile")
        else:
            user_form = UserUpdateForm(instance=user)
            provider_form = ServiceProviderUpdateForm(instance=provider)

        context = {
            "user_form": user_form,
            "provider_form": provider_form,
            "is_provider": True,
        }
    else:
        # Homeowner: only edit user info
        if request.method == "POST":
            user_form = UserUpdateForm(request.POST, request.FILES, instance=user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, "Profile updated successfully!")
                return redirect("accounts:profile")
        else:
            user_form = UserUpdateForm(instance=user)

        context = {
            "user_form": user_form,
            "is_provider": False,
        }

    return render(request, "accounts/edit_profile.html", context)



@login_required
def delete_profile(request):
    if request.method == "POST":
        request.user.delete()
        messages.success(request, "Account deleted successfully.")
        return redirect("accounts:login")
    return render(request, "accounts/delete_account_confirm.html")


@login_required
def delete_account(request):
    """
    Deletes the logged-in user's account (homeowner or provider) and all associated profiles.
    """
    user = request.user

    if request.method == "POST":
        user.delete()
        messages.success(request, "Your account has been permanently deleted.")
        return redirect("accounts:login")

    return render(request, "accounts/delete_account_confirm.html")


# -------------------------
# SERVICE PROVIDER MANAGEMENT
# -------------------------
@login_required
def provider_showcase_view(request):
    if request.user.user_type != "service_provider":
        messages.error(request, "Unauthorized access.")
        return redirect("accounts:homeowner_dashboard")

    provider = request.user.provider_profile
    form = ProviderSkillsForm(request.POST or None, instance=provider)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Skills updated successfully!")
        return redirect("accounts:provider_showcase")
    return render(request, "accounts/provider_showcase.html", {"form": form, "provider": provider})


@login_required
def provider_update_view(request):
    if request.user.user_type != "service_provider":
        return redirect("accounts:homeowner_dashboard")

    provider = request.user.provider_profile
    form = ServiceProviderUpdateForm(request.POST or None, request.FILES or None, instance=provider)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Provider profile updated!")
        return redirect("accounts:provider_dashboard")
    return render(request, "services/provider_update.html", {"form": form})

# -------------------------
# SERVICE PROVIDER MANAGEMENT (CRUD)
# -------------------------
@login_required
def provider_list(request):
    """
    List all service providers
    """
    providers = ServiceProvider.objects.all()
    return render(request, 'services/providers_list.html', {'providers': providers})


@login_required
def provider_create(request):
    """
    Create a new service provider profile
    """
    if hasattr(request.user, 'provider_profile'):
        messages.info(request, "You already have a provider profile.")
        return redirect('accounts:provider_detail', pk=request.user.provider_profile.pk)

    form = ServiceProviderUpdateForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        provider = form.save(commit=False)
        provider.user = request.user
        provider.save()
        form.save_m2m()  # save ManyToMany relationships
        messages.success(request, "Provider profile created successfully.")
        return redirect('accounts:provider_detail', pk=provider.pk)
    return render(request, 'services/provider_create.html', {'form': form})


@login_required
def provider_detail(request, pk):
    """
    Show details of a specific service provider
    """
    provider = get_object_or_404(ServiceProvider, pk=pk)

    # Homeowners can submit service requests from this page
    form = ServiceRequestForm(request.POST or None)
    if request.method == 'POST' and request.user.user_type == "homeowner":
        if form.is_valid():
            service_request = form.save(commit=False)
            service_request.homeowner = request.user
            service_request.provider = provider
            service_request.save()
            messages.success(request, "Service request sent successfully!")
            return redirect("accounts:homeowner_dashboard")
    elif request.method == 'POST':
        messages.error(request, "Only homeowners can request services.")

    return render(request, 'services/provider_detail.html', {'provider': provider, 'form': form})


@login_required
def provider_update(request, pk):
    provider = get_object_or_404(ServiceProvider, pk=pk)
    if request.method == 'POST':
        form = ServiceProviderUpdateForm(request.POST, request.FILES, instance=provider)
        if form.is_valid():
            form.save()
            messages.success(request, "Provider profile updated successfully.")
            return redirect('services:provider_detail', pk=provider.pk)
    else:
        form = ServiceProviderUpdateForm(instance=provider)
    return render(request, 'services/provider_update.html', {'form': form, 'provider': provider})


@login_required
def provider_delete(request, pk):
    provider = get_object_or_404(ServiceProvider, pk=pk)

    # Only owner can delete
    if request.user != provider.user:
        messages.error(request, "You are not allowed to delete this profile.")
        return redirect('services:provider_detail', pk=provider.pk)

    if request.method == 'POST':
        provider.delete()
        messages.success(request, "Provider profile deleted successfully.")
        return redirect('services:provider_list')

    return render(request, 'services/provider_delete_confirm.html', {'provider': provider})


# -------------------------
# HOMEOWNER MANAGEMENT (CRUD)
# -------------------------
@login_required
def homeowner_list(request):
    """
    List all homeowners
    """
    homeowners = User.objects.filter(user_type='homeowner')
    return render(request, 'accounts/homeowner_list.html', {'homeowners': homeowners})


@login_required
def homeowner_detail(request, pk):
    """
    Show details of a specific homeowner
    """
    homeowner = get_object_or_404(User, pk=pk, user_type='homeowner')
    return render(request, 'accounts/homeowner_detail.html', {'homeowner': homeowner})


@login_required
def homeowner_update(request, pk):
    """
    Update a homeowner's profile
    """
    homeowner = get_object_or_404(User, pk=pk, user_type='homeowner')
    form = UserUpdateForm(request.POST or None, request.FILES or None, instance=homeowner)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f"{homeowner.username}'s profile has been updated.")
        return redirect('accounts:homeowner_detail', pk=homeowner.pk)
    return render(request, 'accounts/homeowner_update.html', {'form': form, 'homeowner': homeowner})


@login_required
def homeowner_delete(request, pk):
    """
    Delete a homeowner's profile
    """
    homeowner = get_object_or_404(User, pk=pk, user_type='homeowner')
    if request.method == 'POST':
        homeowner.delete()
        messages.success(request, f"{homeowner.username}'s profile has been deleted.")
        return redirect('accounts:homeowner_list')
    return render(request, 'accounts/homeowner_delete_confirm.html', {'homeowner': homeowner})



# -------------------------
# SERVICE REQUESTS
# -------------------------
@login_required
def create_service_request(request, provider_pk=None):
    if request.user.user_type != "homeowner":
        messages.error(request, "Only homeowners can request services.")
        return redirect("accounts:provider_dashboard")

    form = ServiceRequestForm(request.POST or None)
    if provider_pk:
        form.fields['provider'].queryset = ServiceProvider.objects.filter(pk=provider_pk)
    else:
        form.fields['provider'].queryset = ServiceProvider.objects.all()

    if request.method == "POST" and form.is_valid():
        service_request = form.save(commit=False)
        service_request.homeowner = request.user
        service_request.save()
        messages.success(request, "Service request submitted successfully!")
        return redirect("accounts:homeowner_dashboard")
    return render(request, "services/service_request_form.html", {"form": form})


# -------------------------
# MPESA PAYMENTS
# -------------------------
@login_required
def mpesa_payment_request(request, amount=None):
    """
    Initiates MPESA payment via Daraja.
    """
    if request.method == "POST":
        phone_number = request.POST.get("phone_number")
        amount = request.POST.get("amount")
        if not phone_number or not amount:
            messages.error(request, "Phone number and amount are required.")
            return redirect("accounts:homeowner_dashboard")

        # Create a PaymentRequest object
        payment = PaymentRequest.objects.create(
            user=request.user,
            phone_number=phone_number,
            amount=amount
        )

        # Call Daraja STK Push
        cl = MpesaClient()
        stk_response = cl.stk_push(
            phone_number=phone_number,
            amount=int(amount),
            account_reference=f"HomeConnect-{request.user.username}",
            transaction_desc="Service Payment",
            callback_url=request.build_absolute_uri("/connectmpesa/callback/")
        )

        if stk_response:
            payment.checkout_request_id = stk_response.get("CheckoutRequestID")
            payment.status = PaymentRequest.STATUS_SENT
            payment.save()
            messages.success(request, "MPESA payment request sent! Check your phone.")
        else:
            payment.status = PaymentRequest.STATUS_FAILED
            payment.save()
            messages.error(request, "Failed to initiate MPESA payment.")

        return redirect("accounts:homeowner_dashboard")

    return render(request, "connectmpesa/mpesa_payment.html")


@csrf_exempt
def mpesa_payment_callback(request):
    """
    Handles MPESA callback from Daraja.
    Updates PaymentRequest and logs transaction.
    """
    import json
    data = json.loads(request.body)
    checkout_id = data.get("CheckoutRequestID")
    result_code = data.get("ResultCode")
    result_desc = data.get("ResultDesc")
    amount = data.get("Amount")
    phone = data.get("PhoneNumber")

    # Find the PaymentRequest
    try:
        payment = PaymentRequest.objects.get(checkout_request_id=checkout_id)
        payment.status = PaymentRequest.STATUS_COMPLETED if result_code == 0 else PaymentRequest.STATUS_FAILED
        payment.save()
        MpesaTransaction.objects.create(
            payment_request=payment,
            mpesa_transaction_id=checkout_id,
            amount=amount,
            result_code=result_code,
            result_desc=result_desc,
            raw_payload=data
        )
    except PaymentRequest.DoesNotExist:
        return JsonResponse({"error": "PaymentRequest not found"}, status=404)

    return JsonResponse({"status": "success"})


# -------------------------
# PASSWORD RESET
# -------------------------
class CustomPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")
