from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    # Dashboard
    path('', views.homeowner_dashboard, name='dashboard'),
    path('provider/dashboard/', views.provider_dashboard, name='provider_dashboard'),

    # PROVIDERS
    path('providers/', views.providers_list, name='providers'),
    path('providers/<int:pk>/', views.provider_detail, name='provider_detail'),
    path('providers/<int:pk>/update/', views.provider_update, name='provider_update'),
    path('providers/<int:pk>/delete/', views.provider_delete, name='provider_delete'),

    # REQUESTS (homeowner)
    path('requests/<int:pk>/', views.request_detail, name='request_detail'),
    path('requests/<int:pk>/update/', views.update_request, name='update_request'),
    path('requests/<int:pk>/delete/', views.delete_request, name='delete_request'),

    # REQUEST ACTIONS (provider side)
    path('requests/<int:pk>/action/', views.request_action, name='request_action'),
]
