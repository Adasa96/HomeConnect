from django.urls import path
from . import views

app_name = 'connectmpesa'

urlpatterns = [
    path('start/', views.start_payment, name='start_payment'),
    path('callback/', views.mpesa_callback, name='mpesa_callback'),
    path('connectmpesa/status/<int:pk>/', views.payment_status, name='payment_status'),
]
