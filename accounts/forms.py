from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from .models import ServiceProvider, User
from services.models import Service

User = get_user_model()

# ----------------------------------------
# PHONE VALIDATOR
# ----------------------------------------
phone_validator = RegexValidator(
    regex=r'^\+?\d{9,15}$',
    message='Enter a valid phone number (9–15 digits, optional +).'
)


# ------------------------------------------------
# LOGIN FORM
# ------------------------------------------------

class UserLoginForm(forms.Form): 
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))

# ------------------------------------------------
# USER REGISTRATION FORM
# ------------------------------------------------
class UserRegistrationForm(forms.ModelForm):
    # --- Fields (Remain the same) ---
    phone = forms.CharField(
        required=False,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2547XXXXXXXX'})
    )
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    USER_TYPES = [
        ('homeowner', 'Homeowner'),
        ('service_provider', 'Service Provider'),
    ]
    user_type = forms.ChoiceField(
        choices=USER_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Services You Offer"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'location', 'city', 'user_type', 'bio', 'profile_image', 'services')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            raise ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        """
        Modified: Only saves the User object and sets the password. 
        The ServiceProvider creation logic is moved to the view for transactional safety.
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        
        # NOTE: If 'user_type' is not a field on your custom User model, 
        # you need to ensure it's saved somewhere (e.g., on a separate Profile model).
        # Assuming you've added user_type to your custom User model or are handling it via a Profile model later.
        
        if commit:
            user.save()
            # Removed: provider_profile creation logic
            
        return user
# ------------------------------------------------
# USER PROFILE UPDATE FORM
# ------------------------------------------------
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'location', 'city', 'bio', 'profile_image')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ------------------------------------------------
# PROVIDER SKILLS FORM
# ------------------------------------------------
class ProviderSkillsForm(forms.ModelForm):
    class Meta:
        model = ServiceProvider
        fields = ['skills']
        widgets = {
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 5})
        }


# ------------------------------------------------
# SERVICE PROVIDER PROFILE FORMS
# ------------------------------------------------
class ProviderUserFieldsForm(forms.ModelForm):
    """Fields from the User model for providers."""
    class Meta:
        model = User
        fields = ["bio", "phone", "location", "city", "profile_image"]
        widgets = {
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "profile_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


class ProviderProfileForm(forms.ModelForm):
    """Fields from the ServiceProvider model."""
    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Services You Offer"
    )

    class Meta:
        model = ServiceProvider
        fields = [
            "company_name",
            "skills",
            "experience_years",
            "portfolio_image",
            "services",
        ]
        widgets = {
            "company_name": forms.TextInput(attrs={"class": "form-control"}),
            "skills": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "experience_years": forms.NumberInput(attrs={"class": "form-control"}),
            "portfolio_image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


class ServiceProviderUpdateForm(forms.ModelForm):
    """Update form for ServiceProvider model only."""
    class Meta:
        model = ServiceProvider
        fields = [
            "company_name",
            "skills",
            "experience_years",
            "portfolio_image",
            "services",
        ]
        widgets = {
            "services": forms.CheckboxSelectMultiple(),
        }


# ------------------------------------------------
# GENERAL USER UPDATE FORM
# ------------------------------------------------
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
