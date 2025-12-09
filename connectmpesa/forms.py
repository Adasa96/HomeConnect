from django import forms
from .models import PaymentRequest

class MpesaPaymentForm(forms.ModelForm):
    class Meta:
        model = PaymentRequest
        fields = ['amount', 'phone_number']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '07XXXXXXXX'}),
        }
