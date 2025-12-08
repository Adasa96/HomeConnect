from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from .models import ServiceProvider

User = get_user_model()

# Basic phone validator: allow optional + and 9-15 digits
phone_validator = RegexValidator(
    regex=r'^\+?\d{9,15}$',
    message='Enter a valid phone number (digits only, optional leading +, 9 to 15 digits)'
)

# LOGIN FORM
class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username'
    }))

    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))


# REGISTRATION FORM
class UserRegistrationForm(forms.ModelForm):
    phone = forms.CharField(
        required=False,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone (e.g. 2547XXXXXXXX)'
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )

    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )

    USER_TYPES = [
        ('homeowner', 'Homeowner'),
        ('service_provider', 'Service Provider'),
    ]

    user_type = forms.ChoiceField(
        choices=USER_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'location', 'city', 'user_type', 'bio', 'profile_image')

        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Short description about you (optional)'
            }),
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone (e.g. 2547XXXXXXXX)'
            }),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street or address (optional)'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City (optional)'}),
        }

    # Validate matching passwords
    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if p1 and p2 and p1 != p2:
            raise ValidationError("Passwords do not match.")

        return cleaned_data

    # Save user and set password properly
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()
        return user



# PROFILE UPDATE FORM
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'location', 'city', 'bio', 'profile_image')

        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
        }
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']   # Add more fields if your User model has them
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email'
            }),
        }
# SERVICE PROVIDER SHOWCASE FORM
class ServiceProviderUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('bio', 'services', 'phone', 'location', 'city', 'profile_image')

        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'services': forms.CheckboxSelectMultiple(),  # providers choose services they offer
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
class ProviderSkillsForm(forms.ModelForm):
    class Meta:
        model = ServiceProvider
        fields = ['skills']
        widgets = {
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 5})
        }
