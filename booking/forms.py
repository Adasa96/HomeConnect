from django import forms
from .models import Booking
from django.utils import timezone

class BookingForm(forms.ModelForm):
    scheduled_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type':'datetime-local','class':'form-control'}))

    class Meta:
        model = Booking
        fields = ('provider','service','scheduled_time','notes')
        widgets = {
            'notes': forms.Textarea(attrs={'class':'form-control','rows':4}),
            'service': forms.Select(attrs={'class':'form-control'}),
            'provider': forms.Select(attrs={'class':'form-control'}),
        }
