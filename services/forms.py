from django import forms
from .models import ServiceRequest, ServiceProvider, Service

class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ('service', 'provider', 'description')
        widgets = {
            'service': forms.Select(attrs={'class': 'form-select'}),
            'provider': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Describe your service request in detail...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically populate providers
        self.fields['provider'].queryset = ServiceProvider.objects.all()
        self.fields['service'].empty_label = "Select a service"
        self.fields['provider'].empty_label = "Select a provider"


class ProviderEditForm(forms.ModelForm):
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
            "company_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Company Name"
            }),
            "skills": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Describe your skills or services"
            }),
            "experience_years": forms.NumberInput(attrs={
                "class": "form-control",
            }),
            "portfolio_image": forms.ClearableFileInput(attrs={
                "class": "form-control"
            }),
            "services": forms.SelectMultiple(attrs={
                "class": "form-select"
            }),
        }
