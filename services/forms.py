from django import forms
from .models import ServiceRequest, ServiceProvider

class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ('service', 'details', 'provider')  # include provider if you want to assign directly
        widgets = {
            'service': forms.Select(attrs={'class': 'form-control'}),
            'provider': forms.Select(attrs={'class': 'form-control'}),
            'details': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Describe your service request in detail...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super(ServiceRequestForm, self).__init__(*args, **kwargs)
        # Optional: filter providers to only active ones
        self.fields['provider'].queryset = ServiceProvider.objects.all()  # customize as needed
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
                "placeholder": "Describe your skills"
            }),
            "experience_years": forms.NumberInput(attrs={
                "class": "form-control",
            }),
            "services": forms.SelectMultiple(attrs={
                "class": "form-select"
            }),
        }
