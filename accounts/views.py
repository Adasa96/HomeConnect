from django.shortcuts import render, redirect
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


# LOGIN VIEW
def login_view(request):
    if request.user.is_authenticated:
        if request.user.user_type == "service_provider":
            return redirect("accounts:provider_dashboard")
        return redirect("services:dashboard")

    if request.method == "POST":
        form = UserLoginForm(request, data=request.POST)

        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=username, password=password)

            if user:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                if user.user_type == "service_provider":
                    return redirect("accounts:provider_dashboard")
                return redirect("services:dashboard")

            messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Please fix the errors below.")

    else:
        form = UserLoginForm()

    return render(request, "accounts/login.html", {"form": form})

# REGISTER VIEW
def register_view(request):
    if request.user.is_authenticated:
        if request.user.user_type == "service_provider":
            return redirect("accounts:provider_dashboard")
        return redirect("services:dashboard")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Account created. Welcome {user.username}!")

            if user.user_type == "service_provider":
                return redirect("accounts:provider_dashboard")
            return redirect("services:dashboard")
    else:
        form = UserRegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


# LOGOUT VIEW
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect("accounts:login")


# HOMEOWNER PROFILE
@login_required
def profile_view(request):
    if request.user.user_type == "service_provider":
        return redirect("accounts:provider_dashboard")

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:profile")

    else:
        form = UserProfileForm(instance=request.user)

    return render(request, "accounts/profile.html", {"form": form})


# PROVIDER DASHBOARD
@login_required
def provider_dashboard(request):
    if request.user.user_type != "service_provider":
        messages.error(request, "You are not a service provider.")
        return redirect("services:dashboard")

    provider = request.user.provider_profile

    # Providers incoming service requests
    requests_list = provider.servicerequest_set.all() if hasattr(provider, "servicerequest_set") else []

    return render(
        request, "accounts/provider_dashboard.html",
        {
            "provider": provider,
            "requests": requests_list,
        },
    )
@login_required
def provider_dashboard_view(request):
    user = request.user

    if user.user_type != "service_provider":
        return redirect("accounts:login")

    # Ensure provider profile exists
    try:
        profile = user.provider_profile
    except ServiceProvider.DoesNotExist:
        profile = ServiceProvider.objects.create(user=user)

    # Fetch incoming service requests
    requests_list = profile.servicerequest_set.all() if hasattr(profile, "servicerequest_set") else []

    return render(
        request,
        "services/provider_dashboard.html",
        {
            "provider": profile,
            "requests": requests_list,
        },
    )


@login_required
def homeowner_dashboard(request):
    return render(request, 'accounts/homeowner_dashboard.html')


# PROVIDER SKILLS SHOWCASE PAGE
@login_required
def provider_showcase_view(request):
    if request.user.user_type != "service_provider":
        messages.error(request, "You are not a service provider.")
        return redirect("services:dashboard")

    provider = request.user.provider_profile

    if request.method == "POST":
        form = ProviderSkillsForm(request.POST, instance=provider)
        if form.is_valid():
            form.save()
            messages.success(request, "Your skills have been updated.")
            return redirect("accounts:provider_showcase")
    else:
        form = ProviderSkillsForm(instance=provider)

    return render(
        request, "accounts/provider_showcase.html",
        {
            "form": form,
            "provider": provider,
        },
    )

@login_required
def edit_profile(request):
    user = request.user
    
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:profile")
    else:
        form = UserUpdateForm(instance=user)

    return render(request, "accounts/edit_profile.html", {"form": form})

@login_required
def delete_profile(request):
    user = request.user

    if request.method == "POST":
        user.delete()
        messages.success(request, "Your account has been permanently deleted.")
        return redirect("accounts:login") 

    messages.error(request, "Invalid request.")
    return redirect("accounts:profile")

@login_required
def delete_account(request):
    user = request.user

    if request.method == "POST":
        user.delete()
        messages.success(request, "Your account has been deleted.")
        return redirect("accounts:login")

    return render(request, "accounts/delete_account_confirm.html")

# PASSWORD RESET 
class CustomPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")
