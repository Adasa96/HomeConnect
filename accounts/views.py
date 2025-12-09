from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy

from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView

from .models import ServiceProvider
from .forms import (
    ProviderSkillsForm,
    UserRegistrationForm,
    UserLoginForm,
    UserProfileForm,
    ServiceProviderUpdateForm,
    UserUpdateForm,
)

def home_view(request):
    return render(request, 'accounts/home.html')
    
# LOGIN VIEW
def login_view(request):
    if request.user.is_authenticated:
        return redirect(
            "accounts:provider_dashboard"
            if request.user.user_type == "service_provider"
            else "services:dashboard"
        )

    form = UserLoginForm(request, data=request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=username, password=password)

            if user:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")

                return redirect(
                    "accounts:provider_dashboard"
                    if user.user_type == "service_provider"
                    else "services:dashboard"
                )
            messages.error(request, "Invalid login credentials.")

    return render(request, "accounts/login.html", {"form": form})


# REGISTRATION VIEW
def register_view(request):
    if request.user.is_authenticated:
        return redirect(
            "accounts:provider_dashboard"
            if request.user.user_type == "service_provider"
            else "services:dashboard"
        )

    form = UserRegistrationForm(request.POST or None, request.FILES or None)

    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            login(request, user)

            messages.success(request, f"Account created. Welcome {user.username}!")

            return redirect(
                "accounts:provider_dashboard"
                if user.user_type == "service_provider"
                else "services:dashboard"
            )

    return render(request, "accounts/register.html", {"form": form})


# LOGOUT VIEW
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect("accounts:login")


# HOMEOWNER PROFILE CRUD

# READ HOMEOWNER PROFILE
@login_required
def profile_view(request):
    if request.user.user_type == "service_provider":
        return redirect("accounts:provider_dashboard")

    form = UserProfileForm(
        request.POST or None, 
        request.FILES or None, 
        instance=request.user
    )

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("accounts:profile")

    return render(request, "accounts/profile.html", {"form": form})

@login_required
def homeowner_list(request):
    """
    List all homeowners
    """
    # Filter users who are homeowners
    homeowners = User.objects.filter(user_type='homeowner')

    return render(request, 'accounts/homeowner_list.html', {
        'homeowners': homeowners
    })

@login_required
def homeowner_detail(request, pk):
    """
    Show details of a specific homeowner
    """
    homeowner = User.objects.filter(pk=pk, user_type='homeowner').first()
    if not homeowner:
        from django.http import Http404
        raise Http404("Homeowner does not exist.")

    return render(request, 'accounts/homeowner_detail.html', {
        'homeowner': homeowner
    })

@login_required
def homeowner_update(request, pk):
    """
    Update a homeowner's profile
    """
    # Only allow updating homeowners
    homeowner = get_object_or_404(User, pk=pk, user_type='homeowner')

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=homeowner)
        if form.is_valid():
            form.save()
            messages.success(request, f"{homeowner.username}'s profile has been updated.")
            return redirect('accounts:homeowner_detail', pk=homeowner.pk)
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = UserUpdateForm(instance=homeowner)

    return render(request, 'accounts/homeowner_update.html', {
        'form': form,
        'homeowner': homeowner
    })

@login_required
def homeowner_delete(request, pk):
    """
    Delete a homeowner's profile
    """
    # Only allow deleting homeowners
    homeowner = get_object_or_404(User, pk=pk, user_type='homeowner')

    if request.method == 'POST':
        homeowner.delete()
        messages.success(request, f"{homeowner.username}'s profile has been deleted.")
        return redirect('accounts:homeowner_list')

    return render(request, 'accounts/homeowner_delete_confirm.html', {
        'homeowner': homeowner
    })



# UPDATE HOMEOWNER PROFILE
@login_required
def edit_profile(request):
    user = request.user
    form = UserUpdateForm(request.POST or None, instance=user)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:profile")

    return render(request, "accounts/edit_profile.html", {"form": form})


# DELETE HOMEOWNER ACCOUNT
@login_required
def delete_profile(request):
    if request.method == "POST":
        request.user.delete()
        messages.success(request, "Your account has been permanently deleted.")
        return redirect("accounts:login")

    return render(request, "accounts/delete_account_confirm.html")

@login_required
def homeowner_dashboard(request):
    """
    Dashboard for homeowners
    """
    if request.user.user_type != 'homeowner':
        # Redirect service providers to their dashboard
        from django.shortcuts import redirect
        return redirect('accounts:provider_dashboard')

    return render(request, 'accounts/homeowner_dashboard.html')


# SERVICE PROVIDER CRUD

# PROVIDER DASHBOARD
@login_required
def provider_dashboard(request):
    """Dashboard for service providers showing incoming service requests."""
    
    if request.user.user_type != "service_provider":
        return HttpResponseForbidden("Access denied.")
    
    # Get or create provider profile linked to this user
    provider, _ = ServiceProvider.objects.get_or_create(user=request.user)
    
    # Fetch all requests for this provider
    requests_list = ServiceRequest.objects.filter(provider=provider)\
                        .select_related('homeowner', 'service')\
                        .order_by('-created_at')

    context = {
        "provider": provider,
        "requests": requests_list,
    }
    return render(request, "services/provider_dashboard.html", context)



# UPDATE SERVICE PROVIDER PROFILE
@login_required
def provider_update_view(request):
    if request.user.user_type != "service_provider":
        return redirect("services:dashboard")

    provider = request.user.provider_profile

    form = ServiceProviderUpdateForm(
        request.POST or None,
        request.FILES or None,
        instance=provider
    )

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Provider profile updated.")
            return redirect("accounts:provider_dashboard")

    return render(request, "accounts/provider_update.html", {"form": form})


# DELETE SERVICE PROVIDER ACCOUNT
@login_required
def provider_delete_view(request):
    if request.method == "POST":
        request.user.delete()
        messages.success(request, "Your provider account has been deleted.")
        return redirect("accounts:login")

    return render(request, "accounts/delete_account_confirm.html")


# SERVICE PROVIDER SKILLS CRUD
@login_required
def provider_showcase_view(request):
    if request.user.user_type != "service_provider":
        messages.error(request, "Unauthorized access.")
        return redirect("services:dashboard")

    provider = request.user.provider_profile

    form = ProviderSkillsForm(
        request.POST or None,
        instance=provider
    )

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Skills updated successfully.")
            return redirect("accounts:provider_showcase")

    return render(
        request,
        "accounts/provider_showcase.html",
        {"form": form, "provider": provider},
    )

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ServiceProvider

@login_required
def provider_list(request):
    """
    List all service providers
    """
    providers = ServiceProvider.objects.all()

    return render(request, 'services/providers_list.html',{
        'providers': providers
    })

@login_required
def provider_create(request):
    """
    Create a new service provider profile
    """
    # Check if user is already a provider
    if hasattr(request.user, 'provider_profile'):
        messages.info(request, "You already have a provider profile.")
        return redirect('accounts:provider_detail', pk=request.user.provider_profile.pk)

    if request.method == 'POST':
        form = ServiceProviderUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            provider = form.save(commit=False)
            provider.user = request.user
            provider.save()
            form.save_m2m()
            messages.success(request, "Provider profile created successfully.")
            return redirect('accounts:provider_detail', pk=provider.pk)
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = ServiceProviderUpdateForm()

    return render(request, 'services/provider_create.html', {
        'form': form
    })

@login_required
def provider_detail(request, pk):
    provider = get_object_or_404(ServiceProvider, pk=pk)

    if request.method == 'POST':
        if not request.user.is_authenticated or request.user == provider.user:
            return redirect('accounts:login')

        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.homeowner = request.user
            req.provider = provider  # <-- assign ServiceProvider, not User
            req.save()
            messages.success(request, 'Service request sent successfully!')
            return redirect('services:providers')
    else:
        form = ServiceRequestForm()

    return render(request, 'services/provider_detail.html', {'provider': provider, 'form': form})

@login_required
def provider_update(request, pk):
    provider = get_object_or_404(ServiceProvider, pk=pk)
    if request.method == "POST":
        form = ServiceProviderUpdateForm(request.POST, request.FILES, instance=provider)
        if form.is_valid():
            form.save()
            messages.success(request, "Provider profile updated successfully.")
            return redirect("accounts:provider_detail", pk=provider.pk)
    else:
        form = ServiceProviderUpdateForm(instance=provider)
    return render(request, "services/provider_update.html", {"form": form, "provider": provider})

@login_required
def provider_delete(request, pk):
    provider = get_object_or_404(ServiceProvider, pk=pk)

    # Only the owner can delete
    if request.user != provider.user:
        messages.error(request, "You are not allowed to delete this profile.")
        return redirect("accounts:provider_detail", pk=provider.pk)

    if request.method == "POST":
        provider.delete()
        messages.success(request, "Provider profile deleted successfully.")
        return redirect("services:providers_list")
    return render(
        request,
        "services/provider_delete_confirm.html",
        {"provider": provider}
    )


@login_required
def delete_account(request):
    user = request.user

    if request.method == "POST":
        user.delete()
        messages.success(request, "Your account has been deleted.")
        return redirect("accounts:login")

    return render(request, "accounts/delete_account_confirm.html")


@login_required
def create_service_request(request, provider_pk=None):
    """
    Homeowner can create a service request to a provider.
    Optional provider_pk allows pre-selecting a provider.
    """
    if request.user.user_type != "homeowner":
        messages.error(request, "Only homeowners can request services.")
        return redirect("accounts:provider_dashboard")

    form = ServiceRequestForm(request.POST or None)

    if provider_pk:
        form.fields['provider'].queryset = ServiceProvider.objects.filter(pk=provider_pk)
    else:
        # Show all providers
        form.fields['provider'].queryset = ServiceProvider.objects.all()

    if request.method == "POST":
        if form.is_valid():
            service_request = form.save(commit=False)
            service_request.homeowner = request.user
            service_request.save()
            messages.success(request, "Service request submitted successfully!")
            return redirect("accounts:homeowner_dashboard")

    return render(request, "services/service_request_form.html", {"form": form})



# PASSWORD RESET

class CustomPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")
