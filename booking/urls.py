from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('create/', views.create_booking, name='create_booking'),
    path('mine/', views.my_bookings, name='my_bookings'),
    path('provider/', views.provider_bookings, name='provider_bookings'),
]
