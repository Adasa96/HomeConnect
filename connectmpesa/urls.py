from django.urls import path
from . import views

app_name = 'connectmpesa'

urlpatterns = [
    path('start/', views.start_payment, name='start_payment'),
    path('callback/', views.mpesa_callback, name='mpesa_callback'),
]
