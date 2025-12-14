from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponseForbidden, JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, IntegrityError # <-- transaction and IntegrityError are crucial

from django.contrib.auth import get_user_model
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView

from services.models import ServiceRequest, Service
from accounts.models import ServiceProvider, Profile # <-- Ensure Profile is imported
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
# NOTE: Ensure django_daraja is configured in your settings.
# from django_daraja.mpesa.core import MpesaClient 

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
    """
    HANDLED: Safely creates the User and the associated Profile or ServiceProvider 
    using database transactions to prevent IntegrityError.
    """
    if request.user.is_authenticated:
        return redirect('accounts:redirect_after_login')

    # Note: request.FILES is needed for 'profile_image'
    form = UserRegistrationForm(request.POST or None, request.FILES or None) 
    
    if request.method == "POST" and form.is_valid():
        try:
            # --- START ATOMIC TRANSACTION ---
            # If any database write in this block fails, all previous writes in this block are rolled back.
            with transaction.atomic(): 
                
                # 1. Create the base User object (form.save() is responsible for this now)
                user = form.save(commit=True) 
                
                # Retrieve the necessary data from the form's cleaned data
                user_type = form.cleaned_data.get("user_type")
                services = form.cleaned_data.get("services")
                
                # 2. Handle Profile/ServiceProvider creation based on user_type
                if user_type == "service_provider":
                    # Create the ServiceProvider instance linked to the new user
                    provider_profile = ServiceProvider.objects.create(user=user)
                    
                    # Link Many-to-Many services
                    if services:
                        provider_profile.services.set(services)
                        
                    # NOTE: If you decide all users (providers included) must have a Profile, 
                    # you would uncomment the line below:
                    # Profile.objects.create(user=user)
                    
                else: # Default for 'homeowner'
                    # Create the general Profile object for the homeowner
                    Profile.objects.create(user=user) 
                    
            # --- END ATOMIC TRANSACTION (Success) ---
            
            # 3. Log the user in and redirect
            login(request, user)
            messages.success(request, f"Account created. Welcome {user.username}!")
            return redirect('accounts:redirect_after_login')

        except IntegrityError:
            # Catches the UNIQUE constraint failed error. 
            # The transaction should have rolled back, so we just show an error message.
            messages.error(request, "A user account with this ID already exists. Please try logging in or using a different username/email.")
            return redirect('accounts:register')
        
        except Exception as e:
            # Catch other unexpected errors
            print(f"Registration Error: {e}")
            messages.error(request, "An unexpected error occurred during registration.")
            return redirect('accounts:register')

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

    # Using request.user.provider_profile requires that the ServiceProvider model 
    # has a related_name or the default related_name is used.
    # Assuming 'provider_profile' is the correct reverse lookup name.
    try:
        provider = request.user.provider_profile
    except ServiceProvider.DoesNotExist:
        messages.warning(request, "Please complete your provider profile.")
        return redirect('accounts:provider_create') # Direct user to create their profile

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
    # This view seems to be using UserProfileForm, which is fine, 
    # but the logic often requires separate handling for provider forms.
    # The 'edit_profile' view handles this more completely.

    # We can retrieve the related profile or provider data here for display
    is_provider = request.user.user_type == "service_provider"
    
    # Safely get provider or profile (assuming get_or_create worked in register_view)
    if is_provider:
        try:
            profile_data = request.user.provider_profile
        except ServiceProvider.DoesNotExist:
            profile_data = None # Or redirect to complete profile
    else:
        try:
            profile_data = request.user.profile 
        except Profile.DoesNotExist:
            profile_data = None
            
    # Assuming a template logic handles displaying the data.
    return render(request, "accounts/profile.html", {
        "user_obj": request.user,
        "profile_data": profile_data,
        "is_provider": is_provider
    })


@login_required
def edit_profile(request):
    user = request.user

    if user.user_type == "service_provider":
        # Service provider: edit both user info and provider-specific fields
        try:
            provider = user.provider_profile
        except ServiceProvider.DoesNotExist:
            messages.warning(request, "Please complete your provider profile before editing.")
            return redirect('accounts:provider_create') 

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
        # Homeowner: only edit user info (and optionally the generic Profile)
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
        # Using the standard Django user delete cascade
        request.user.delete() 
        messages.success(request, "Account deleted successfully.")
        return redirect("accounts:login")
    return render(request, "accounts/delete_account_confirm.html")


# Keeping the duplicate delete_account for compatibility, though delete_profile handles it
@login_required
def delete_account(request):
    """
    Deletes the logged-in user's account (homeowner or provider) and all associated profiles.
    """
    return delete_profile(request) # Redirecting to the cleaner delete_profile logic


# -------------------------
# SERVICE PROVIDER MANAGEMENT
# -------------------------
@login_required
def provider_showcase_view(request):
    if request.user.user_type != "service_provider":
        messages.error(request, "Unauthorized access.")
        return redirect("accounts:homeowner_dashboard")

    try:
        provider = request.user.provider_profile
    except ServiceProvider.DoesNotExist:
        messages.warning(request, "Please complete your provider profile.")
        return redirect('accounts:provider_create') 

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

    try:
        provider = request.user.provider_profile
    except ServiceProvider.DoesNotExist:
        messages.warning(request, "Please complete your provider profile.")
        return redirect('accounts:provider_create') 
        
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
    # Check if a provider profile already exists (using related_name)
    if hasattr(request.user, 'provider_profile'):
        messages.info(request, "You already have a provider profile.")
        return redirect('accounts:provider_detail', pk=request.user.provider_profile.pk)

    # Check if user is trying to create a provider profile but is registered as a homeowner
    if request.user.user_type != "service_provider":
         messages.error(request, "Your account type is Homeowner. You cannot manually create a Provider Profile.")
         return redirect('accounts:homeowner_dashboard')


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
    # Security check: Only the provider owner can update
    if request.user != provider.user:
        return HttpResponseForbidden("You do not have permission to update this profile.")

    if request.method == 'POST':
        form = ServiceProviderUpdateForm(request.POST, request.FILES, instance=provider)
        if form.is_valid():
            form.save()
            messages.success(request, "Provider profile updated successfully.")
            return redirect('accounts:provider_detail', pk=provider.pk) # Changed namespace to accounts
    else:
        form = ServiceProviderUpdateForm(instance=provider)
    return render(request, 'services/provider_update.html', {'form': form, 'provider': provider})


@login_required
def provider_delete(request, pk):
    provider = get_object_or_404(ServiceProvider, pk=pk)

    # Only owner can delete
    if request.user != provider.user:
        messages.error(request, "You are not allowed to delete this profile.")
        return redirect('accounts:provider_detail', pk=provider.pk) # Changed namespace to accounts

    if request.method == 'POST':
        provider.delete()
        messages.success(request, "Provider profile deleted successfully.")
        return redirect('accounts:provider_list') # Changed namespace to accounts

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
    # Security check: A user can only update their own profile
    if request.user != homeowner:
        return HttpResponseForbidden("You do not have permission to update this profile.")

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
    # Security check: A user can only delete their own profile
    if request.user != homeowner:
        return HttpResponseForbidden("You do not have permission to delete this profile.")

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
        # Filter provider queryset if a specific provider is targeted
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
    # NOTE: You MUST UNCOMMENT the `from django_daraja.mpesa.core import MpesaClient` 
    # import at the top of the file for this view to work.

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
        # cl = MpesaClient() # <-- UNCOMMENT THIS LINE
        
        # stk_response = cl.stk_push( # <-- UNCOMMENT THIS BLOCK
        #     phone_number=phone_number,
        #     amount=int(amount),
        #     account_reference=f"HomeConnect-{request.user.username}",
        #     transaction_desc="Service Payment",
        #     callback_url=request.build_absolute_uri("/connectmpesa/callback/")
        # )

        # --- Simulated Response for testing without MpesaClient ---
        stk_response = {"CheckoutRequestID": "simulated_id", "ResponseCode": "0"} 
        # --- End Simulated Response ---


        if stk_response and stk_response.get("ResponseCode") == "0":
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
    
    # Safely extract data from Daraja callback payload
    callback_metadata = data.get("Body", {}).get("stkCallback", {})
    checkout_id = callback_metadata.get("CheckoutRequestID")
    result_code = callback_metadata.get("ResultCode")
    result_desc = callback_metadata.get("ResultDesc")
    
    # Extract transaction details if the transaction was successful (ResultCode == 0)
    transaction_details = callback_metadata.get("CallbackMetadata", {}).get("Item", [])
    amount = None
    phone = None
    
    for item in transaction_details:
        if item.get("Name") == "Amount":
            amount = item.get("Value")
        elif item.get("Name") == "PhoneNumber":
            phone = item.get("Value")

    # Find the PaymentRequest
    try:
        payment = PaymentRequest.objects.get(checkout_request_id=checkout_id)
        
        payment.status = PaymentRequest.STATUS_COMPLETED if result_code == 0 else PaymentRequest.STATUS_FAILED
        payment.save()
        
        # Log the transaction
        MpesaTransaction.objects.create(
            payment_request=payment,
            mpesa_transaction_id=checkout_id, # This should ideally be the MpesaReceiptNumber, but using checkout_id for now
            amount=amount,
            phone_number=phone,
            result_code=result_code,
            result_desc=result_desc,
            raw_payload=data
        )
    except PaymentRequest.DoesNotExist:
        # Log this error since we cannot inform the user directly
        print(f"MPESA Callback Error: PaymentRequest not found for Checkout ID: {checkout_id}")
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