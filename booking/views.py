from django.shortcuts import render

# Create your views here.
def create_booking(request):
    return render(request, 'booking/create.html')

def my_bookings(request):
    return render(request, 'booking/my_bookings.html')

def provider_bookings(request):
    return render(request, 'booking/provider_bookings.html')
