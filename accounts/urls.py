from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from accounts.views import home_view

app_name = 'accounts'

urlpatterns = [
    path('', views.home_view, name='home'),
    # AUTHENTICATION
    path('register/', views.register_view, name='register'),
    path("after-login/", views.redirect_after_login, name="redirect_after_login"),
    path('logout/', views.logout_view, name='logout'),

    # PASSWORD RESET WORKFLOW
    path('password-reset/', 
         views.CustomPasswordResetView.as_view(), 
         name='password_reset'),

    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/',
         views.CustomPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),

    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    # DASHBOARDS
    path('login/',views.login_view, name='login'),
    path('provider/dashboard/', views.provider_dashboard, name='provider_dashboard'),
    path('homeowner/dashboard/', views.homeowner_dashboard, name='homeowner_dashboard'),

    
    # PROFILE MANAGEMENT
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/delete/', views.delete_profile, name='delete_profile'),
    path('delete/', views.delete_account, name='delete_account'),


    # SERVICE PROVIDER SKILLS
    path('provider/showcase/', views.provider_showcase_view, name='provider_showcase'),

    # CRUD: HOMEOWNERS
    path('homeowners/', views.homeowner_list, name='homeowner_list'),
    path('homeowners/<int:pk>/', views.homeowner_detail, name='homeowner_detail'),
    path('homeowners/<int:pk>/update/', views.homeowner_update, name='homeowner_update'),
    path('homeowners/<int:pk>/delete/', views.homeowner_delete, name='homeowner_delete'),

    # CRUD: SERVICE PROVIDERS
    path('providers/', views.provider_list, name='provider_list'),
    path('providers/create/', views.provider_create, name='provider_create'),
    path('providers/<int:pk>/', views.provider_detail, name='provider_detail'),
    path('providers/<int:pk>/update/', views.provider_update, name='provider_update'),
    path('providers/<int:pk>/delete/', views.provider_delete, name='provider_delete'),

    #SERVICES
    path('service-request/', views.create_service_request,name='create_service_request'),
    path('service_request_provider/<int:provider_pk>/', views.create_service_request,
    name='create_service_request_for_provider'),

]
